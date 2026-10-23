"""Import entries from the MSCD thesis search on KiltHub.

Examples:
    python scripts/import_collection.py --all
    python scripts/import_collection.py --with-document-metrics

The normal import is intentionally fast: it collects public catalogue metadata and
KiltHub preview images. The optional metric pass downloads the PDFs to calculate
their page and word counts, then caches them locally (outside Git).
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import DB_PATH, current_time, init_db  # noqa: E402


SEARCH_URL = "https://api.figshare.com/v2/articles/search"
SEARCH_FOR = "Master of Science in Computational Design (MSCD)"
USER_AGENT = "MSCD-Thesis-Orbit/1.0 (course project)"
CACHE_DIR = ROOT / "data" / "pdf-cache"


# Read public API metadata using an identifiable educational user agent.
def fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=45) as response:  # noqa: S310 - fixed public API endpoint
        import json

        return json.load(response)


def collection_entries(limit: int | None = None) -> list[dict]:
    """Follow the KiltHub MSCD thesis search, mirroring its item-type filter."""
    entries: list[dict] = []
    seen: set[int] = set()
    offset = 0
    page_size = 1000
    while True:
        import json

        request = Request(
            SEARCH_URL,
            data=json.dumps({
                "search_for": SEARCH_FOR,
                "limit": page_size,
                "offset": offset,
                "order": "published_date",
                "order_direction": "desc",
            }).encode("utf-8"),
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=45) as response:  # noqa: S310 - fixed public Figshare API endpoint
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("Unexpected response from the KiltHub thesis search API.")
        added = 0
        for entry in batch:
            # The website URL combines this query with itemTypes=8 (thesis).
            if entry.get("defined_type") != 8 or "kilthub.cmu.edu" not in entry.get("url_public_html", ""):
                continue
            source_id = int(entry["id"])
            if source_id not in seen:
                seen.add(source_id)
                entries.append(entry)
                added += 1
        if limit is not None and len(entries) >= limit:
            return entries[:limit]
        if len(batch) < page_size:
            return entries
        if not added:
            raise ValueError("The search API repeated a page; import stopped to avoid an incomplete catalogue.")
        offset += page_size


# Convert repository HTML to plain text for display and embedding.
def strip_html(value: str) -> str:
    text = html.unescape(re.sub(r"<[^>]*>", " ", value or ""))
    return re.sub(r"\s+", " ", text).strip()


# Assign an editable starter category with keyword rules, not semantic inference.
def choose_category(title: str, keywords: list[str], abstract: str) -> str:
    content = " ".join([title, *keywords, abstract]).lower()
    groups = [
        ("Robotics + Fabrication", ("robot", "fabricat", "manufactur", "material", "making", "woodwork", "print")),
        ("XR + Immersion", ("virtual reality", "augmented reality", " vr", " ar", "immersive", "spatial audio", "motion capture")),
        ("AI + Generative Design", ("artificial intelligence", "generative", "machine learning", "deep learning", "llm", "language model", "retrieval")),
        ("Data + Built Environment", ("dataset", "data ", "building", "urban", "iot", "environment", "point cloud")),
        ("Interaction + Experience", ("interaction", "experience", "interface", "learning", "accessible", "wearable", "design tool")),
    ]
    for category, signals in groups:
        if any(signal in content for signal in signals):
            return category
    return "Computational Design"


# Select the first publicly listed PDF download from repository file metadata.
def find_pdf(files: list[dict]) -> str:
    for file in files:
        name = str(file.get("name", "")).lower()
        if name.endswith(".pdf"):
            return str(file.get("download_url", ""))
    return ""


def saved_metrics(source_id: int) -> tuple[int | None, int | None]:
    """Return completed measurements so interrupted imports can resume safely."""
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT page_count, word_count FROM theses WHERE source_id = ?", (source_id,)
        ).fetchone()
    if row and row[0] is not None and row[1] is not None:
        return int(row[0]), int(row[1])
    return None, None


# Reuse a cached PDF when present; otherwise download the public source.
def download_pdf(source_id: int, pdf_url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destination = CACHE_DIR / f"{source_id}.pdf"
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    request = Request(pdf_url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=120) as response, destination.open("wb") as file:  # noqa: S310 - URL is from Figshare metadata
        shutil.copyfileobj(response, file)
    return destination


# Count PDF pages and extractable words; represent inaccessible metrics as missing.
def document_metrics(source_id: int, pdf_url: str, keep_pdf_cache: bool) -> tuple[int | None, int | None]:
    if not pdf_url:
        return None, None
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise SystemExit("Install dependencies first: python -m pip install -r requirements.txt") from error

    path: Path | None = None
    try:
        path = download_pdf(source_id, pdf_url)
        reader = PdfReader(path)
        pages = len(reader.pages)
        words = 0
        for page in reader.pages:
            words += len(re.findall(r"\b[\w'-]+\b", page.extract_text() or ""))
        return pages, words
    except Exception as error:  # PDF text extraction can fail on scanned or protected documents.
        print(f"  ! Could not calculate metrics for {source_id}: {error}")
        return None, None
    finally:
        if path and path.exists() and not keep_pdf_cache:
            path.unlink()


# Refresh source fields while preserving user summaries, categories, and custom images.
def upsert_thesis(detail: dict, preview_url: str, include_metrics: bool, keep_pdf_cache: bool) -> None:
    source_id = int(detail["id"])
    title = strip_html(detail.get("title", ""))
    authors = ", ".join(author.get("full_name", "") for author in detail.get("authors", []))
    published = str(detail.get("published_date", ""))
    year = int(published[:4]) if len(published) >= 4 and published[:4].isdigit() else None
    abstract = strip_html(detail.get("description", ""))
    keywords = [str(keyword).strip() for keyword in detail.get("keywords", []) if str(keyword).strip()]
    category = choose_category(title, keywords, abstract)
    pdf_url = find_pdf(detail.get("files") or [])
    page_count, word_count = (None, None)
    if include_metrics:
        page_count, word_count = saved_metrics(source_id)
        if page_count is None or word_count is None:
            page_count, word_count = document_metrics(source_id, pdf_url, keep_pdf_cache)
    source_url = str(detail.get("url_public_html", ""))
    image_url = str(detail.get("thumb", "") or preview_url)
    now = current_time()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO theses (
                source_id, in_source_search, title, author, published_date, year, category, keywords,
                source_abstract, ai_summary, page_count, word_count, source_url,
                pdf_url, image_url, image_source, created_at, updated_at
            ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, 'KiltHub preview image', ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                in_source_search = 1,
                title = excluded.title,
                author = excluded.author,
                published_date = excluded.published_date,
                year = excluded.year,
                source_abstract = excluded.source_abstract,
                source_url = excluded.source_url,
                pdf_url = excluded.pdf_url,
                image_url = CASE WHEN theses.image_source = 'KiltHub preview image' THEN excluded.image_url ELSE theses.image_url END,
                page_count = COALESCE(excluded.page_count, theses.page_count),
                word_count = COALESCE(excluded.word_count, theses.word_count),
                updated_at = excluded.updated_at
            """,
            (
                source_id,
                title,
                authors,
                published,
                year,
                category,
                ", ".join(keywords),
                abstract,
                page_count,
                word_count,
                source_url,
                pdf_url,
                image_url,
                now,
                now,
            ),
        )
        from scripts.enrich_advisors import advisor_fields
        connection.execute(
            "UPDATE theses SET advisors=?, advisor_source=? WHERE source_id=?",
            (advisor_fields(detail), f"https://api.figshare.com/v2/articles/{source_id}#Advisor(s)", source_id),
        )


# Parse import options, report failures, and synchronize the visible source IDs.
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="Import every public MSCD thesis search result.")
    scope.add_argument("--limit", type=int, help="Import only this many newest theses. Default: all.")
    parser.add_argument(
        "--with-document-metrics",
        action="store_true",
        help="Download each PDF and calculate page and word counts. This can take time.",
    )
    parser.add_argument(
        "--keep-pdf-cache",
        action="store_true",
        help="Keep downloaded PDFs in data/pdf-cache after calculating metrics (off by default).",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1.")

    init_db()
    entries = collection_entries(args.limit)
    print(f"Found {len(entries)} public KiltHub MSCD thesis search records.", flush=True)
    failed = []

    for index, entry in enumerate(entries, start=1):
        detail_url = str(entry.get("url_public_api", entry.get("url", "")))
        if not detail_url:
            print(f"[{index}/{len(entries)}] Skipping entry with no public API URL.")
            continue
        try:
            detail = fetch_json(detail_url)
            if not isinstance(detail, dict):
                raise ValueError("Unexpected detail response.")
            print(f"[{index}/{len(entries)}] {strip_html(detail.get('title', 'Untitled'))}", flush=True)
            upsert_thesis(detail, str(entry.get("thumb", "")), args.with_document_metrics, args.keep_pdf_cache)
        except Exception as error:
            failed.append(entry["id"])
            print(f"  ! Failed record {entry['id']}: {error}", flush=True)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"Imported {len(entries) - len(failed)} of {len(entries)} KiltHub records at {stamp}.")
    if failed:
        raise SystemExit(f"Retry the import for failed records: {failed}")
    source_ids = [int(entry["id"]) for entry in entries]
    placeholders = ", ".join("?" for _ in source_ids)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            f"UPDATE theses SET in_source_search = CASE WHEN source_id IN ({placeholders}) "
            "THEN 1 ELSE 0 END WHERE source_id IS NOT NULL",
            source_ids,
        )
    print(f"Synchronized visible records to the KiltHub search: {len(source_ids)}.")


if __name__ == "__main__":
    main()
