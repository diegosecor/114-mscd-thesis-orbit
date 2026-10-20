"""Import the newest entries from the public MSCD KiltHub collection.

Examples:
    python scripts/import_collection.py
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


COLLECTION_ID = "5279693"
COLLECTION_URL = f"https://api.figshare.com/v2/collections/{COLLECTION_ID}/articles"
USER_AGENT = "MSCD-Thesis-Orbit/1.0 (course project)"
CACHE_DIR = ROOT / "data" / "pdf-cache"


def fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=45) as response:  # noqa: S310 - fixed public API endpoint
        import json

        return json.load(response)


def strip_html(value: str) -> str:
    text = html.unescape(re.sub(r"<[^>]*>", " ", value or ""))
    return re.sub(r"\s+", " ", text).strip()


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


def download_pdf(source_id: int, pdf_url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destination = CACHE_DIR / f"{source_id}.pdf"
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    request = Request(pdf_url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=120) as response, destination.open("wb") as file:  # noqa: S310 - URL is from Figshare metadata
        shutil.copyfileobj(response, file)
    return destination


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


def upsert_thesis(detail: dict, preview_url: str, include_metrics: bool, keep_pdf_cache: bool) -> None:
    source_id = int(detail["id"])
    title = strip_html(detail.get("title", ""))
    authors = ", ".join(author.get("full_name", "") for author in detail.get("authors", []))
    published = str(detail.get("published_date", ""))
    year = int(published[:4]) if len(published) >= 4 and published[:4].isdigit() else None
    abstract = strip_html(detail.get("description", ""))
    keywords = [str(keyword).strip() for keyword in detail.get("keywords", []) if str(keyword).strip()]
    category = choose_category(title, keywords, abstract)
    pdf_url = find_pdf(detail.get("files", []))
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
                source_id, title, author, published_date, year, category, keywords,
                source_abstract, ai_summary, page_count, word_count, source_url,
                pdf_url, image_url, image_source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, 'KiltHub preview image', ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=30, help="Number of newest theses to import (default: 30).")
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
    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be between 1 and 100.")

    init_db()
    entries = fetch_json(
        f"{COLLECTION_URL}?page=1&page_size={args.limit}&order=published_date&order_direction=desc"
    )
    if not isinstance(entries, list):
        raise SystemExit("Unexpected response from the KiltHub collection API.")

    for index, entry in enumerate(entries, start=1):
        detail_url = str(entry.get("url_public_api", entry.get("url", "")))
        if not detail_url:
            print(f"[{index}/{len(entries)}] Skipping entry with no public API URL.")
            continue
        detail = fetch_json(detail_url)
        if not isinstance(detail, dict):
            print(f"[{index}/{len(entries)}] Skipping unexpected detail response.")
            continue
        print(f"[{index}/{len(entries)}] {strip_html(detail.get('title', 'Untitled'))}")
        upsert_thesis(detail, str(entry.get("thumb", "")), args.with_document_metrics, args.keep_pdf_cache)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"Imported {len(entries)} KiltHub records at {stamp}.")


if __name__ == "__main__":
    main()
