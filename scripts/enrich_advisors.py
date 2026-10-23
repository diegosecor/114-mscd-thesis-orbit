"""Fetch public KiltHub Advisor(s) fields; never infer supervisors from authors."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sqlite3
import sys
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import DB_PATH, init_db
from scripts.import_collection import fetch_json, strip_html


# Preserve name separators while cleaning the published Advisor(s) field.
def advisor_fields(detail: dict) -> str:
    for field in detail.get("custom_fields", []):
        if field.get("name", "").lower() in {"advisor(s)", "advisors", "advisor"}:
            value = field.get("value") or ""
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            value = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", str(value))
            return ", ".join(filter(None, (strip_html(name) for name in re.split(r"[,;\n\r]+", value))))
    return ""


# Retrieve advisor provenance from one public Figshare record.
def load_advisor(source_id: int) -> tuple[int, str]:
    detail = fetch_json(f"https://api.figshare.com/v2/articles/{source_id}")
    return source_id, advisor_fields(detail)


# Fetch with bounded concurrency and write only source-based advisor metadata.
def main():
    init_db()
    with sqlite3.connect(DB_PATH) as connection:
        source_ids = [row[0] for row in connection.execute(
            "SELECT source_id FROM theses WHERE in_source_search=1 AND source_id IS NOT NULL"
        )]
    failures = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(load_advisor, source_id): source_id for source_id in source_ids}
        for future in as_completed(futures):
            try:
                source_id, advisors = future.result()
                with sqlite3.connect(DB_PATH) as connection:
                    connection.execute(
                        "UPDATE theses SET advisors=?, advisor_source=? WHERE source_id=?",
                        (advisors, f"https://api.figshare.com/v2/articles/{source_id}#Advisor(s)", source_id),
                    )
                print(f"{source_id}: {advisors or '[not published]'}", flush=True)
            except Exception as error:
                failures.append(futures[future])
                print(f"Failed {futures[future]}: {error}", flush=True)
    if failures:
        raise SystemExit(f"Retry for failed records: {failures}")


if __name__ == "__main__":
    main()
