"""Extract project figures and missing document metrics from public thesis PDFs.

Run after import_collection.py. Images are rendered from actual PDF figures, not
generated artwork. The manifest records the source PDF, page, and crop. Downloads
and candidate sheets stay in ignored data/pdf-cache and tmp/thumbnail-review.

    python scripts/enrich_documents.py
    python scripts/enrich_documents.py --ids 29257196
    python scripts/enrich_documents.py --choose 29257196:2
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
# A workspace-local installation also works in the bundled Codex runtime.
if (ROOT / "tmp" / "pdf-tools").is_dir():
    sys.path.insert(0, str(ROOT / "tmp" / "pdf-tools"))

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps

DB_PATH = ROOT / "data" / "theses.db"
CACHE = ROOT / "data" / "pdf-cache"
OUTPUT = ROOT / "static" / "thumbnails"
REVIEW = ROOT / "tmp" / "thumbnail-review"
MANIFEST = ROOT / "data" / "thumbnail_manifest.json"
USER_AGENT = "MSCD-Thesis-Orbit/1.1 (educational thesis catalogue)"
STOP_WORDS = set(
    "the and for with from through towards toward using into between based design "
    "research thesis exploration exploring computational development framework study "
    "interaction interactive environment system approach investigation application "
    "architecture architectural building models model digital".split()
)


# Cache a verified PDF, using a partial file and bounded retries.
def download(record: dict) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{record['source_id']}.pdf"
    if path.exists() and path.stat().st_size > 200:
        return path
    partial = path.with_suffix(".part")
    for attempt in range(3):
        try:
            request = Request(record["pdf_url"], headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=120) as response, partial.open("wb") as stream:
                shutil.copyfileobj(response, stream)
            with partial.open("rb") as stream:
                if b"%PDF" not in stream.read(1024):
                    raise ValueError("The public file is not a PDF.")
            partial.replace(path)
            return path
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError("Download did not complete")


# Measure crop overlap to avoid duplicate candidate image regions.
def overlap_ratio(first, second):
    intersect = first & second
    return intersect.get_area() / max(1, min(first.get_area(), second.get_area()))


def candidate_regions(page):
    """Combine adjacent image fragments to retain complete project figures."""
    page_area = page.rect.get_area()
    regions = []
    for image in page.get_image_info():
        rect = fitz.Rect(image["bbox"]) & page.rect
        if rect.is_empty or rect.width < 70 or rect.height < 55:
            continue
        if image["width"] < 110 or image["height"] < 80:
            continue
        ratio = rect.width / rect.height
        if ratio < 0.22 or ratio > 5.0 or rect.get_area() / page_area < 0.025:
            continue
        # A full-page scan must not be mistaken for a project photograph.
        if rect.get_area() / page_area > 0.86:
            continue
        if not any(overlap_ratio(rect, existing) > .85 for existing in regions):
            regions.append(rect)
    if len(regions) > 1:
        groups = []
        for rect in regions:
            for group in groups:
                expanded = group + (-20, -20, 20, 20)
                if expanded.intersects(rect):
                    group |= rect
                    break
            else:
                groups.append(fitz.Rect(rect))
        regions.extend(
            group for group in groups
            if group.get_area() / page_area < .77
            and not any(overlap_ratio(group, rect) > .97 and
                        abs(group.get_area() - rect.get_area()) < 100 for rect in regions)
        )
    return regions


# Rank real PDF figures heuristically; this is not an embedding similarity score.
def score_region(rect, page, text, tokens, index, total):
    page_area = page.rect.get_area()
    area = rect.get_area() / page_area
    # Captions near the image provide semantic hints without classifying artwork.
    nearby = page.get_textbox(
        fitz.Rect(max(0, rect.x0 - 10), max(0, rect.y0 - 40),
                  min(page.rect.width, rect.x1 + 10),
                  min(page.rect.height, rect.y1 + 95))
    ).lower()
    score = 1.5 + min(area, .45) * 6
    ratio = rect.width / rect.height
    score += max(0, 1 - abs(math.log(max(.1, ratio) / 1.4))) * .9
    score += min(2.0, sum(token in nearby for token in tokens) * .45)
    for term in ("prototype", "our ", "proposed", "interface", "workflow",
                 "demonstrat", "fabricat", "final ", "implementation"):
        if term in nearby:
            score += .4
    # A central chapter is more likely to show the student's own work.
    progress = index / max(1, total)
    score += 1.3 if .3 < progress < .9 else .1
    if "prototype" in nearby or "final result" in nearby:
        score += 1.5
    if index < 5:
        score -= 1.1
    if any(term in text[:350] for term in ("related work", "literature review", "background")):
        score -= 1.5
    if any(term in nearby for term in ("source:", "copyright", "adapted from", "retrieved from")):
        score -= 1.8
    return score, " ".join(nearby.split())[:600]


# Render an attributed PDF crop to a compressed project thumbnail.
def render_region(page, rect, destination):
    rect = (rect + (-3, -3, 3, 3)) & page.rect
    scale = min(2.5, 1000 / max(rect.width, rect.height))
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
    picture = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    picture.save(destination, "JPEG", quality=87, optimize=True)


# Collect document metrics and candidate figures, preserving explicit failure reasons.
def analyze(record):
    source_id = record["source_id"]
    result = {
        "source_id": source_id, "title": record["title"],
        "source_url": record["source_url"], "pdf_url": record["pdf_url"],
        "status": "unavailable",
    }
    if not record["pdf_url"]:
        result["reason"] = "The public KiltHub record does not expose a downloadable PDF."
        return result
    try:
        path = download(record)
        with fitz.open(path) as document:
            count = len(document)
            tokens = {word for word in re.findall(r"[a-z]{4,}", record["title"].lower())
                      if word not in STOP_WORDS}
            candidates = []
            words = 0
            measure = record["word_count"] is None
            for index, page in enumerate(document):
                text = page.get_text()
                if measure:
                    words += len(re.findall(r"\b[\w'-]+\b", text))
                lower = text.lower()
                # Covers, contents, bibliography, and text-only pages are unsuitable.
                if index < 2 or "table of contents" in lower[:250]:
                    continue
                if re.match(r"\s*(?:\d+\s*)?(?:references|bibliography|works cited)\b", lower):
                    continue
                for rect in candidate_regions(page):
                    score, nearby = score_region(rect, page, lower, tokens, index, count)
                    candidates.append({
                        "page": index + 1, "crop": list(rect),
                        "score": round(score, 3), "nearby_text": nearby,
                    })
            result["page_count"] = count
            result["word_count"] = words if measure else record["word_count"]
            ranked = sorted(candidates, key=lambda item: item["score"], reverse=True)
            selected = []
            used_pages = set()
            for item in ranked:
                if item["page"] not in used_pages:
                    selected.append(item)
                    used_pages.add(item["page"])
                if len(selected) >= 8:
                    break
            if not selected:
                result["reason"] = "No suitable raster project figure found; manual selection is needed."
                return result
            folder = REVIEW / str(source_id)
            folder.mkdir(parents=True, exist_ok=True)
            for rank, item in enumerate(selected):
                destination = folder / f"candidate-{rank}.jpg"
                render_region(document[item["page"] - 1], fitz.Rect(item["crop"]), destination)
                item["candidate"] = rank
                item["file"] = str(destination.relative_to(ROOT)).replace("\\", "/")
            result["candidates"] = selected
            result["selected_candidate"] = 0
            result["status"] = "extracted"
            result["reviewed"] = False
            return result
    except Exception as error:
        result["status"] = "error"
        result["reason"] = f"{type(error).__name__}: {error}"
        return result


# Use a readable local font with a portable fallback.
def font(size=12):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


# Build a contact sheet so a human can review figure choices.
def candidate_sheet(item):
    choices = item.get("candidates", [])
    if not choices:
        return
    sheet = Image.new("RGB", (1200, 650), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 8), f"{item['source_id']}  {item['title'][:140]}", font=font(15), fill="#251632")
    for position, candidate in enumerate(choices):
        x = (position % 4) * 300
        y = 40 + (position // 4) * 300
        picture = Image.open(ROOT / candidate["file"])
        picture.thumbnail((284, 247))
        sheet.paste(picture, (x + (300 - picture.width) // 2, y))
        draw.text((x + 8, y + 253),
                  f"#{position} | PDF p.{candidate['page']} | {candidate['score']:.1f}",
                  font=font(13), fill="#523276")
        text = candidate["nearby_text"][:42]
        draw.text((x + 8, y + 275), text, font=font(10), fill="#666666")
    sheet.save(REVIEW / f"{item['source_id']}-candidates.jpg", quality=86)


# Save the chosen figure and its page attribution, preserving existing metrics.
def write_selection(item):
    source_id = item["source_id"]
    selected = item.get("selected_candidate")
    if selected is None or not item.get("candidates"):
        image_url = ""
        image_source = item.get("reason", "Representative figure unavailable.")
    else:
        candidate = item["candidates"][selected]
        destination = OUTPUT / f"{source_id}.jpg"
        shutil.copyfile(ROOT / candidate["file"], destination)
        image_url = f"/thumbnails/{source_id}.jpg"
        image_source = f"Project figure from thesis PDF, page {candidate['page']} (KiltHub)"
        item["image_url"] = image_url
        item["page"] = candidate["page"]
        item["crop"] = candidate["crop"]
    with sqlite3.connect(DB_PATH, timeout=30) as connection:
        # Only touch document measurements and repository-provided previews.
        connection.execute(
            """UPDATE theses SET
               page_count = COALESCE(page_count, ?),
               word_count = COALESCE(word_count, ?),
               image_url = ?, image_source = ?
               WHERE source_id = ?""",
            (item.get("page_count"), item.get("word_count"), image_url, image_source, source_id),
        )


# Create collection-wide contact sheets for thumbnail quality checks.
def overview_sheets(items):
    valid = [item for item in items if item.get("image_url")]
    for start in range(0, len(valid), 12):
        sheet = Image.new("RGB", (1200, 1000), "#f9f8fd")
        draw = ImageDraw.Draw(sheet)
        for offset, item in enumerate(valid[start:start + 12]):
            x, y = (offset % 4) * 300, (offset // 4) * 330
            picture = Image.open(OUTPUT / f"{item['source_id']}.jpg")
            picture.thumbnail((280, 235))
            sheet.paste(picture, (x + (300 - picture.width) // 2, y + 10))
            draw.text((x + 10, y + 250), f"{item['source_id']} / p.{item['page']}", font=font(15), fill="#7d25ff")
            title = item["title"]
            lines = []
            while title and len(lines) < 3:
                cut = min(38, len(title))
                if cut < len(title):
                    cut = title.rfind(" ", 0, cut) or cut
                lines.append(title[:cut])
                title = title[cut:].strip()
            draw.multiline_text((x + 10, y + 274), "\n".join(lines), font=font(12), fill="#251632", spacing=3)
        sheet.save(REVIEW / f"overview-{start // 12 + 1}.jpg", quality=88)


# Run extraction or apply explicit human figure choices and save provenance.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="*", type=int)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--choose", nargs="*", help="Select a reviewed candidate: SOURCE_ID:INDEX")
    parser.add_argument("--figure", nargs="*", help="Review a specific PDF figure: SOURCE_ID:PAGE:REGION_INDEX")
    parser.add_argument("--sheets-only", action="store_true")
    args = parser.parse_args()
    for folder in (CACHE, OUTPUT, REVIEW):
        folder.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    items = manifest.get("records", {})
    if args.figure:
        for selection in args.figure:
            source_id, page_number, region_index = selection.split(":")
            item = items[source_id]
            with fitz.open(CACHE / f"{source_id}.pdf") as document:
                page = document[int(page_number) - 1]
                regions = candidate_regions(page)
                rect = regions[int(region_index)]
                rank = len(item.get("candidates", []))
                destination = REVIEW / source_id / f"candidate-{rank}.jpg"
                destination.parent.mkdir(exist_ok=True)
                render_region(page, rect, destination)
                item.setdefault("candidates", []).append({
                    "page": int(page_number), "crop": list(rect), "score": 0,
                    "nearby_text": "Manually selected after visual inspection.",
                    "candidate": rank,
                    "file": str(destination.relative_to(ROOT)).replace("\\", "/"),
                })
                item["selected_candidate"] = rank
                item["status"] = "extracted"
                item["reviewed"] = True
                write_selection(item)
    elif args.choose:
        for selection in args.choose:
            source_id, rank = selection.split(":")
            item = items[source_id]
            item["selected_candidate"] = int(rank)
            item["reviewed"] = True
            write_selection(item)
    elif not args.sheets_only:
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            records = [dict(row) for row in connection.execute(
                "SELECT * FROM theses WHERE source_id IS NOT NULL ORDER BY published_date DESC"
            )]
        jobs = [row for row in records if
                (not args.ids or row["source_id"] in args.ids)
                and (args.refresh or str(row["source_id"]) not in items
                     or items[str(row["source_id"])].get("status") == "error")]
        # Leave images explicitly edited by the user alone.
        jobs = [row for row in jobs if not row["image_url"] or
                row["image_source"] == "KiltHub preview image" or
                row["image_url"].startswith("/thumbnails/")]
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(analyze, row): row["source_id"] for row in jobs}
            for number, future in enumerate(as_completed(futures), 1):
                item = future.result()
                items[str(item["source_id"])] = item
                write_selection(item)
                candidate_sheet(item)
                manifest = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "method": "Actual raster figures rendered from public thesis PDFs; PDF page numbers are 1-based.",
                    "records": items,
                }
                MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"[{number}/{len(jobs)}] {item['source_id']}: {item['status']} {item.get('reason', '')}", flush=True)
    manifest["records"] = items
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    overview_sheets(list(items.values()))
    print(f"Local project figures: {sum(bool(item.get('image_url')) for item in items.values())}/{len(items)}")


if __name__ == "__main__":
    main()
