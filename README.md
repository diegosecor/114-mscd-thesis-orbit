# MSCD Thesis Orbit

MSCD Thesis Orbit is a local web app for exploring the 30 most recent theses in Carnegie Mellon University's Master of Science in Computational Design KiltHub collection. It turns a catalogue of research documents into an interactive 3D orbit: each thesis is a node, the node colour represents a research category, its size can represent page or word count, and fine dotted lines indicate related work.

I chose this project because I wanted a more visual way to discover the range of research coming out of MSCD. The interface is deliberately inspired by late-1980s and early-1990s CAD drawings: white paper, technical grid lines, and bright violet accents.

## Features

- SQLite database with the 30 newest theses from the public MSCD KiltHub collection.
- Interactive 3D-style canvas: drag to orbit, scroll to zoom, hover to inspect, and select a node for details.
- Filters by category, year, page count, word count, and search terms.
- Create, read, update, and delete thesis records through the interface.
- Each thesis stores its source abstract, editable AI summary, KiltHub link, and preview image URL.
- An import script that can calculate document page and word counts from the public PDFs. It removes temporary PDF downloads by default.

## Database schema

The database is created at `data/theses.db` on first run. It has one table named `theses`.

| Column | Type | Purpose |
| --- | --- | --- |
| `id` | INTEGER | Local primary key for each thesis record. |
| `source_id` | INTEGER | Unique KiltHub/Figshare record id. |
| `title` | TEXT | Thesis title. |
| `author` | TEXT | Thesis author or authors. |
| `published_date` | TEXT | KiltHub posting date. |
| `year` | INTEGER | Posting year used by the year filter. |
| `category` | TEXT | Editable thematic group used in the orbit. |
| `keywords` | TEXT | Comma-separated tags used to reveal connections. |
| `source_abstract` | TEXT | Original abstract from KiltHub. |
| `ai_summary` | TEXT | Short AI-assisted summary, editable before use. |
| `page_count` | INTEGER | Number of PDF pages. |
| `word_count` | INTEGER | Approximate extractable words in the PDF. |
| `source_url` | TEXT | Link to the KiltHub record. |
| `pdf_url` | TEXT | Direct public PDF source. |
| `image_url` | TEXT | Preview image or manually chosen project image. |
| `image_source` | TEXT | Where the image was selected from. |

## Run locally

This project uses Python's built-in `sqlite3` and HTTP server. Python 3.11+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\import_collection.py --limit 30
python app.py
```

Open [http://localhost:8000](http://localhost:8000) in a browser.

The first command imports catalogue metadata, abstracts, source links, and KiltHub preview images. To calculate page and word counts, run the optional enrichment pass:

```powershell
python scripts\import_collection.py --limit 30 --with-document-metrics
```

It downloads each public PDF temporarily and saves only the resulting page and word counts in SQLite. It may take several minutes, depending on the file sizes and internet connection. Add `--keep-pdf-cache` only if you intentionally want to retain the downloaded PDFs.

## CRUD operations

- **Create:** Select **+ Add Thesis**, fill in the form, and save the new record.
- **Read:** Browse the orbit, hover over nodes, select a node for a detail panel, or search/filter the collection.
- **Update:** Select a thesis, choose **Edit**, revise fields such as category, keywords, image, or summary, and save.
- **Delete:** Select a thesis, choose **Delete**, and confirm the removal.

The required user-controlled query is available through category, year, page-count, word-count, and text-search filters.

## Data sources and limits

The initial records come from the public [Master of Computational Design KiltHub collection](https://kilthub.cmu.edu/collections/_/5279693). The importer requests public metadata from the Figshare API that serves KiltHub. Source links remain visible in the detail panel so that a visitor can verify every record.

Page and word counts are only as accurate as the PDF's embedded text. Scanned PDFs, visual diagrams, and unusual encodings can lead to a missing or approximate word count. A KiltHub preview is used initially as the small node image; it can be replaced in the edit form with a visually stronger project image chosen from the thesis PDF.

## AI use and citations

AI tools were used to help plan the SQLite schema, develop and debug the app, and draft short summaries from the source abstracts. Every AI summary should be reviewed against its original KiltHub abstract before submission. The original KiltHub page is retained for each record, and the development process is documented in [`prompt_log.md`](prompt_log.md).
