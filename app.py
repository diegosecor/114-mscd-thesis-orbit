"""Local web server for MSCD Thesis Orbit.

Run with: python app.py
Then visit: http://localhost:8000
"""

from __future__ import annotations

import json
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
}


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


def init_db() -> None:
    with database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS theses (
                id INTEGER PRIMARY KEY,
                source_id INTEGER UNIQUE,
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


def current_time() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def as_record(row: sqlite3.Row) -> dict:
    return dict(row)


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_error_json(self, message: str, status: HTTPStatus) -> None:
        self.send_json({"error": message}, status)

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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/theses":
            self.list_theses(parse_qs(parsed.query))
            return
        if parsed.path == "/api/stats":
            self.get_stats()
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

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
        if search:
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

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM theses {where} ORDER BY published_date DESC, title COLLATE NOCASE"
        with database() as connection:
            records = [as_record(row) for row in connection.execute(sql, values)]
        self.send_json({"theses": records})

    def get_stats(self) -> None:
        with database() as connection:
            total = connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0]
            categories = [
                dict(row)
                for row in connection.execute(
                    "SELECT category, COUNT(*) AS count FROM theses GROUP BY category ORDER BY count DESC, category"
                )
            ]
        self.send_json({"total": total, "categories": categories})

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
        self.send_json(as_record(row), HTTPStatus.CREATED)

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
        self.send_json(as_record(row))

    def do_DELETE(self) -> None:
        record_id = self.path_id()
        if record_id is None:
            return
        with database() as connection:
            cursor = connection.execute("DELETE FROM theses WHERE id = ?", (record_id,))
        if cursor.rowcount == 0:
            self.send_error_json("Thesis not found.", HTTPStatus.NOT_FOUND)
            return
        self.send_json({"deleted": record_id})

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
