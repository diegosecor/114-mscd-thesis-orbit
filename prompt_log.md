# Prompt log: MSCD Thesis Orbit

This is a living record of the development process for HW6. It keeps important prompts verbatim, identifies the tools used, and records corrections made during development. I will add any later testing, debugging, and design changes that I personally make before submission rather than inventing time I did not spend.

## Tools and roles

- **OpenAI Codex:** Used as a coding collaborator to interpret the requirements, discuss project scope, plan the database schema, create the local web app, and explain errors.
- **KiltHub / Figshare public API:** Used to retrieve the public metadata for the selected MSCD thesis collection.
- **Python `sqlite3`:** Used to create and query the local database.
- **Python `pypdf`:** Used by the optional enrichment script to calculate PDF page counts and approximate document word counts.

## Development record

### 2026-10-19 — Understand the assignment and narrow the topic

I first asked Codex for a summary of the HW6 database assignment. I decided the required CRUD app should be related to something I personally find useful rather than a generic movie or to-do list. I explored a few ideas and settled on the MSCD thesis archive because I wanted a way to see the range of work from the program.

Important prompt, verbatim:

> Dentro esta el instructivo de la actividad que tengo que hacer, dame un resumen de lo que hay que hacer primero y dame ideas de que puedo hacer que sea corto

Important prompt, verbatim:

> tengo dos ideas, una es la pagina de tesis de cmu de mii programa de mscd seria interesante hacer una matrix de contendinos y que se puedan categoriazar cada tema

### 2026-10-20 — Define the data and visual direction

I chose the 30 most recent records from the public MSCD KiltHub collection. Each record needs a title, author, date, categories, keywords, original abstract, AI-assisted summary, page count, word count, source link, and a representative image. The database is a catalogue that I can edit; it is not a copy of every thesis on KiltHub.

Important prompt, verbatim:

> me gustaria tambien saber el nuemro de paginas de cada documento, y ademas que graficamene sea una orbita pero que se vea visualemne que s epeuda agrupar y ver y tener una descripcion

Important prompt, verbatim:

> 1 fondo blanco lineas claras, tonos morado radioactivo pero lineas muy myuy delggadas y blanco, quiero que se vea como los raficos de cad de los 80s 90s,

> 2 un punto y dependiendo tenga un centrico de algun color dependiendo de las tematicas, quiero que siempre se vean asi sean una linea super super delgada y punteada, pero dependiendo de lo que uno selecciones se vea una linea ruesas, tambien una iimagen en cuadrito peque;a

> 4 quiero que dependiendo de lo que uno quiera organizar la info se edite un poquito el tama;o de lso punos de las tesis la escala

> 5 si una sercripcion, las palabras clasve y el link y una imagen

### 2026-10-20 — Build the first local version

I created a fresh local Git repository named `mscd-thesis-orbit`. The app uses a SQLite `theses` table, a small Python HTTP server, and a browser-based canvas visualization. I used parameterized SQL queries for all create, read, update, and delete operations. I added filters for category, year, pages, word count, and text search.

I also wrote `scripts/import_collection.py`. It gets the newest 30 collection entries, retrieves their public metadata, stores their KiltHub links and abstracts in SQLite, and can optionally calculate page and word counts from the public PDFs. I ran the import and generated 30 short, reviewable AI-assisted summaries from the source abstracts. The PDF metric pass successfully measured 28 theses. Two KiltHub records did not expose a public PDF file, so their page and word counts are intentionally left blank instead of guessed. The script imports KiltHub preview images first; I will replace any weak previews with a better representative image from the thesis PDF when I review the records.

Important prompt, verbatim:

> comienza, tambien tengo que tener el reistro de lo que hablo, dale una miradita al instructivo

## One mistake from AI and how I corrected it

At first, Codex interpreted my interest in robots as a request to make a separate robot-arm research atlas. That was not my intention. I clarified that the source should be the MSCD thesis category on KiltHub, with robots only being one theme I might discover in the collection. After that correction, I changed the project into an MSCD thesis explorer and used the collection endpoint instead of unrelated robotics sources. This correction mattered because it made the data source, project purpose, and visual grouping much more specific.

## Before I submit

- [ ] Review the AI-assisted summary for every thesis against its original abstract and edit inaccurate wording.
- [ ] Review the small image for every thesis and replace any generic preview with a more representative figure, render, interface, or prototype image from the thesis PDF.
- [ ] Test Create, Read, Update, Delete, all filters, the orbit drag interaction, and source links. Add the exact test results here.
- [ ] Record the short demonstration video showing add, browse/filter, update, and delete operations.
- [ ] Add the GitHub repository link to my portfolio and complete the course submission form.
