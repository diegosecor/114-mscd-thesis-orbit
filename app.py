"""Local web server for MSCD Thesis Orbit.

Run with: python app.py
Then visit: http://localhost:8000
"""

from __future__ import annotations

import json
from advisors import advisor_names
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "theses.db"
HOST = "127.0.0.1"
PORT = 8000

EDITABLE_FIELDS = {
    "title",
    "author",
    "published_date",
    "year",
    "category",
    "keywords",
    "source_abstract",
    "ai_summary",
    "page_count",
    "word_count",
    "source_url",
    "pdf_url",
    "image_url",
    "image_source",
    "advisors",
    "advisor_source",
}


# Open the local metadata database and expose rows as named fields.
def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database():
    """Provide a committed SQLite connection and always release its file handle."""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# Create or migrate catalogue fields without discarding existing thesis records.
def init_db() -> None:
    with database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS theses (
                id INTEGER PRIMARY KEY,
                source_id INTEGER UNIQUE,
                in_source_search INTEGER NOT NULL DEFAULT 1,
                title TEXT NOT NULL,
                author TEXT NOT NULL DEFAULT '',
                published_date TEXT NOT NULL DEFAULT '',
                year INTEGER,
                category TEXT NOT NULL DEFAULT 'Uncategorized',
                keywords TEXT NOT NULL DEFAULT '',
                source_abstract TEXT NOT NULL DEFAULT '',
                ai_summary TEXT NOT NULL DEFAULT '',
                page_count INTEGER,
                word_count INTEGER,
                source_url TEXT NOT NULL DEFAULT '',
                pdf_url TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                image_source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(theses)")}
        if "in_source_search" not in columns:
            connection.execute(
                "ALTER TABLE theses ADD COLUMN in_source_search INTEGER NOT NULL DEFAULT 1"
            )
        for field in ("advisors", "advisor_source"):
            if field not in columns:
                connection.execute(f"ALTER TABLE theses ADD COLUMN {field} TEXT NOT NULL DEFAULT ''")


# Use UTC timestamps so records are portable between machines.
def current_time() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# Expose published metadata plus canonical advisor names for grouping.
def as_record(row: sqlite3.Row) -> dict:
    record = dict(row)
    record["advisor_names"] = advisor_names(record.get("advisors", ""))
    return record


# Lazily load the persistent vector store and reconcile visible catalogue records.
def semantic_store(*, synchronize: bool = True):
    from semantic import get_index

    index = get_index(DATA_DIR)
    if synchronize:
        with database() as connection:
            records = [as_record(row) for row in connection.execute(
                "SELECT * FROM theses WHERE in_source_search = 1 OR source_id IS NULL"
            )]
        index.synchronize(records)
    return index


# Whitelist editable fields and validate numbers before building parameterized SQL.
def clean_payload(payload: dict, *, creating: bool) -> dict:
    clean: dict = {}
    for field in EDITABLE_FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if field in {"year", "page_count", "word_count"}:
            if value in (None, ""):
                clean[field] = None
            else:
                try:
                    clean[field] = int(value)
                except (TypeError, ValueError) as error:
                    raise ValueError(f"{field} must be a whole number.") from error
        else:
            clean[field] = str(value).strip()

    if creating:
        clean.setdefault("title", "")
        clean.setdefault("category", "Uncategorized")
        if not clean["title"]:
            raise ValueError("A thesis title is required.")
    return clean


class OrbitRequestHandler(SimpleHTTPRequestHandler):
    # Serve only the project's static directory, not arbitrary workspace files.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    # Write local request diagnostics to the server console.
    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    # Return UTF-8 JSON with explicit size and no stale API caching.
    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # Use the same JSON error shape for validation and service failures.
    def send_error_json(self, message: str, status: HTTPStatus) -> None:
        self.send_json({"error": message}, status)

    # Read a JSON object from the HTTP request and reject malformed bodies.
    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise ValueError("Request body is required.")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Request body must contain valid JSON.") from error
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    # Dispatch catalogue, statistics, semantic endpoints, or static browser assets.
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/theses":
            self.list_theses(parse_qs(parsed.query))
            return
        if parsed.path == "/api/stats":
            self.get_stats()
            return
        if parsed.path.startswith("/api/semantic/"):
            self.semantic_request(parsed.path, parse_qs(parsed.query))
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    # Validate semantic query parameters and return explicit errors, not fake matches.
    def semantic_request(self, path: str, query: dict) -> None:
        try:
            index = semantic_store()
            if path == "/api/semantic/map":
                self.send_json(index.map())
            elif path == "/api/semantic/neighbors":
                thesis_id = int(query.get("id", [""])[0])
                k = max(1, min(20, int(query.get("k", [8])[0])))
                minimum = float(query.get("minimum", [0.35])[0])
                if not 0 <= minimum <= 1:
                    raise ValueError("Minimum similarity must be between 0 and 1.")
                ids = [int(value) for value in query["ids"][0].split(",") if value] if "ids" in query else None
                neighbors = index.neighbors(thesis_id, ids=ids, k=k, minimum=minimum)
                self.send_json({"id": thesis_id, "neighbors": neighbors, "metric": "cosine similarity"})
            else:
                self.send_error_json("Not found.", HTTPStatus.NOT_FOUND)
        except (ValueError, KeyError) as error:
            self.send_error_json(str(error), HTTPStatus.BAD_REQUEST)
        except Exception as error:
            print(f"Semantic index error: {error!r}", flush=True)
            self.send_error_json("The semantic index is unavailable. Check the server and model download.", HTTPStatus.SERVICE_UNAVAILABLE)

    # Apply exact metadata filters before optional semantic ranking of eligible records.
    def list_theses(self, query: dict) -> None:
        clauses: list[str] = []
        values: list[object] = []

        def one(name: str) -> str:
            return query.get(name, [""])[0].strip()

        category = one("category")
        year = one("year")
        search = one("q")
        if category:
            clauses.append("category = ?")
            values.append(category)
        if year:
            try:
                parsed_year = int(year)
            except ValueError:
                self.send_error_json("Year must be a whole number.", HTTPStatus.BAD_REQUEST)
                return
            clauses.append("year = ?")
            values.append(parsed_year)
        try:
            for field, operator in (("year_min", ">="), ("year_max", "<=")):
                value = one(field)
                if value:
                    clauses.append(f"year {operator} ?")
                    values.append(int(value))
        except ValueError:
            self.send_error_json("Year range must contain whole numbers.", HTTPStatus.BAD_REQUEST)
            return
        if search and one("mode") != "semantic":
            clauses.append("(title LIKE ? OR author LIKE ? OR keywords LIKE ? OR ai_summary LIKE ?)")
            values.extend([f"%{search}%"] * 4)

        try:
            for field, operator in (("page_min", ">="), ("page_max", "<="), ("word_min", ">="), ("word_max", "<=")):
                value = one(field)
                if value:
                    column = "page_count" if field.startswith("page") else "word_count"
                    clauses.append(f"{column} {operator} ?")
                    values.append(int(value))
        except ValueError:
            self.send_error_json("Numeric filters must contain whole numbers.", HTTPStatus.BAD_REQUEST)
            return

        clauses.insert(0, "(in_source_search = 1 OR source_id IS NULL)")
        where = f"WHERE {' AND '.join(clauses)}"
        sql = f"SELECT * FROM theses {where} ORDER BY published_date DESC, title COLLATE NOCASE"
        with database() as connection:
            records = [as_record(row) for row in connection.execute(sql, values)]
        if one("advisor"):
            records = [record for record in records if one("advisor") in record["advisor_names"]]
        if search and one("mode") == "semantic":
            try:
                matches = semantic_store().search(search[:2000], ids=[item["id"] for item in records])
                by_id = {record["id"]: record for record in records}
                records = [{**by_id[match["id"]], "semantic_similarity": match["similarity"],
                            "semantic_excerpt": match["excerpt"], "semantic_passage": match["passage"],
                            "semantic_source": match["source"]} for match in matches]
            except Exception as error:
                print(f"Semantic search error: {error!r}", flush=True)
                self.send_error_json("Semantic search is unavailable. Check the server and model download.", HTTPStatus.SERVICE_UNAVAILABLE)
                return
        self.send_json({"theses": records})

    # Compute filter bounds and advisor counts from the visible catalogue.
    def get_stats(self) -> None:
        with database() as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM theses WHERE in_source_search = 1 OR source_id IS NULL"
            ).fetchone()[0]
            categories = [
                dict(row)
                for row in connection.execute(
                    "SELECT category, COUNT(*) AS count FROM theses "
                    "WHERE in_source_search = 1 OR source_id IS NULL "
                    "GROUP BY category ORDER BY count DESC, category"
                )
            ]
            year_range = connection.execute(
                "SELECT MIN(year), MAX(year) FROM theses "
                "WHERE year IS NOT NULL AND (in_source_search = 1 OR source_id IS NULL)"
            ).fetchone()
            metric_ranges = connection.execute(
                "SELECT MIN(page_count), MAX(page_count), MIN(word_count), MAX(word_count) FROM theses "
                "WHERE in_source_search = 1 OR source_id IS NULL"
            ).fetchone()
            advisors: dict[str, int] = {}
            for row in connection.execute("SELECT * FROM theses WHERE in_source_search = 1 OR source_id IS NULL"):
                for advisor in as_record(row)["advisor_names"]:
                    advisors[advisor] = advisors.get(advisor, 0) + 1
        self.send_json({
            "total": total,
            "categories": categories,
            "year_min": year_range[0],
            "year_max": year_range[1],
            "page_min": metric_ranges[0],
            "page_max": metric_ranges[1],
            "word_min": metric_ranges[2],
            "word_max": metric_ranges[3],
            "advisors": [{"name": name, "count": count} for name, count in sorted(advisors.items(), key=lambda pair: (-pair[1], pair[0]))],
        })

    # Insert metadata and embed the record before reporting a successful addition.
    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/theses":
            self.send_error_json("Not found.", HTTPStatus.NOT_FOUND)
            return
        try:
            payload = clean_payload(self.read_json(), creating=True)
        except ValueError as error:
            self.send_error_json(str(error), HTTPStatus.BAD_REQUEST)
            return

        now = current_time()
        columns = list(payload) + ["created_at", "updated_at"]
        values = [payload[key] for key in payload] + [now, now]
        placeholders = ", ".join("?" for _ in columns)
        with database() as connection:
            cursor = connection.execute(
                f"INSERT INTO theses ({', '.join(columns)}) VALUES ({placeholders})", values
            )
            row = connection.execute("SELECT * FROM theses WHERE id = ?", (cursor.lastrowid,)).fetchone()
            try:
                semantic_store(synchronize=False).upsert(as_record(row))
            except Exception as error:
                connection.rollback()
                self.send_error_json(f"The record could not be embedded and was not saved: {error}", HTTPStatus.SERVICE_UNAVAILABLE)
                return
        self.send_json(as_record(row), HTTPStatus.CREATED)

    # Validate edits and refresh vectors; roll back metadata on embedding failure.
    def do_PUT(self) -> None:
        record_id = self.path_id()
        if record_id is None:
            return
        try:
            payload = clean_payload(self.read_json(), creating=False)
        except ValueError as error:
            self.send_error_json(str(error), HTTPStatus.BAD_REQUEST)
            return
        if not payload:
            self.send_error_json("Provide at least one editable field.", HTTPStatus.BAD_REQUEST)
            return
        if "title" in payload and not payload["title"]:
            self.send_error_json("A thesis title is required.", HTTPStatus.BAD_REQUEST)
            return

        fields = list(payload)
        values = [payload[field] for field in fields]
        fields.append("updated_at")
        values.append(current_time())
        values.append(record_id)
        with database() as connection:
            cursor = connection.execute(
                f"UPDATE theses SET {', '.join(f'{field} = ?' for field in fields)} WHERE id = ?", values
            )
            if cursor.rowcount == 0:
                self.send_error_json("Thesis not found.", HTTPStatus.NOT_FOUND)
                return
            row = connection.execute("SELECT * FROM theses WHERE id = ?", (record_id,)).fetchone()
            try:
                semantic_store(synchronize=False).upsert(as_record(row))
            except Exception as error:
                connection.rollback()
                self.send_error_json(f"The changes could not be embedded and were not saved: {error}", HTTPStatus.SERVICE_UNAVAILABLE)
                return
        self.send_json(as_record(row))

    # Remove the requested record and its vectors after the browser's confirmation.
    def do_DELETE(self) -> None:
        record_id = self.path_id()
        if record_id is None:
            return
        with database() as connection:
            cursor = connection.execute("DELETE FROM theses WHERE id = ?", (record_id,))
            if cursor.rowcount == 0:
                self.send_error_json("Thesis not found.", HTTPStatus.NOT_FOUND)
                return
            try:
                semantic_store(synchronize=False).remove(record_id)
            except Exception as error:
                connection.rollback()
                self.send_error_json(f"The vector index could not be updated: {error}", HTTPStatus.SERVICE_UNAVAILABLE)
                return
        self.send_json({"deleted": record_id})

    # Accept only a numeric ID on the documented thesis resource path.
    def path_id(self) -> int | None:
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "theses"]:
            self.send_error_json("Not found.", HTTPStatus.NOT_FOUND)
            return None
        try:
            return int(parts[2])
        except ValueError:
            self.send_error_json("Thesis id must be a whole number.", HTTPStatus.BAD_REQUEST)
            return None


if __name__ == "__main__":
    init_db()
    print(f"MSCD Thesis Orbit is running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), OrbitRequestHandler).serve_forever()
