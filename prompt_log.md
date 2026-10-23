# Prompt log: MSCD Thesis Orbit

## 2026-10-22 — Reset filters also restores original colors

User prompt (verbatim): "quiero que el boton de reset filter tambien devuelva al color original"

Added resetLineColors to clear every per-type color override, remove custom legend CSS variables, restore original legend labels, refresh the inline color square, and redraw. Reset filters now invokes it and refreshes the editor after filtered records reload, so category color previews use the restored collection. Original per-category/year palettes are restored, not replaced by one flat color. Width preferences remain unchanged. All 23 JavaScript tests passed, including restoration of colors/labels without resetting widths.

## 2026-10-22 — Compact per-connection RGB color square

User prompt (verbatim): "quiero poder cambiarle el color a las lineas en el mismo menu que cambia el grosor, solo quiero un cuadradito que me abra un peque;o panel rgb"

Added one 22px native color-input square beside the inline connection heading. It opens the browser's compact color picker and changes only that relationship type's line color. Original per-category/year palettes remain untouched until explicitly overridden; point colors, width rules, semantic scores, and geometry are unchanged. Custom colors invalidate the connection cache and update legend samples/labels; input redraws remain animation-frame coalesced. Color preferences are page-session only, and the existing width-reset still affects widths only. All 22 JavaScript tests passed, including color independence and color-cache invalidation. Browser verification changed year links to a test pink, confirmed its Custom color legend label, and opened the native color picker (saturation/lightness, hue, and three channel fields exposed in accessibility state). Reloaded afterward to restore the source palette and left the inline square ready to use.

## 2026-10-22 — Expanded proportional zoom

User prompt (verbatim): "el zoom esta bloqueado y quiero hacer mas zoom"

Found the old manual zoom cap at 2.2x. Expanded the range to 0.25–8x and changed wheel scaling to proportional steps, normalizing pixel/line/page wheel units and bounding each individual step. Kept camera rotation, selection-stable framing, thumbnail sizes, and rendering caches unchanged. Added zoom regression tests for crossing the old limit, boundaries, reversibility, and wheel units. All 20 JavaScript tests passed; browser scrolling visibly enlarged the cloud and a preview was saved.

## 2026-10-22 — Inline width editor and 15% wider sidebar

User prompt (verbatim): "cuando toco en conecctions un titulo el menu aparece abajo del todo, quiero que aparesca debajo de cada palabra , me refiero al slider, 

2 quiero que esta barra de laizquierda sea un 15% mas ancha"

Codex now moves the existing width editor directly after the clicked connection row, retaining the same slider, values, and event listeners. Switching names moves that editor; clicking the active name still collapses it. Increased desktop sidebar width from 236px to 271.4px and compact width from 184px to 211.6px, exactly 15%, and adjusted reserved canvas/axis offsets to avoid overlap while preserving selection-stable framing. All 17 JavaScript tests passed. Browser checks verified editor placement immediately after both the first connection and year row; measured desktop width was 271.396px after browser subpixel rounding. Saved an inline-editor preview.

## 2026-10-22 — Restore the unboxed CAD legend and simplify sidebar

User prompt (verbatim): "nooooooo quedo muy feo alinealo como antes al costado, no lo encieres en un cuadro, y maneja el tipo de letra anterior,

2 organiza el texto de el cuadro de la izqueirda que sea mas claro para usar , hay algunas redundancias"

Restored the bottom-right legend to right alignment at the edge, with no background, border, or padding, and the previous Courier-style typography. Kept the new dash–dot year pattern but condensed explanations. Organized the sidebar into VIEW, FILTERS, and CONNECTIONS; shortened search/layout labels without changing their values; moved neighbor controls into collapsed Related Thesis Settings; placed the category color key in a separate collapsed section to avoid duplicating the category filter by default. Removed the repeated thesis total from index status and shortened help text. All 17 JavaScript tests passed. Browser verification confirmed the reorganized controls and original unboxed visual direction; saved an updated preview. Rendering optimizations, line widths, and geometry were preserved.

## 2026-10-22 — Readable connection controls and distinct year pattern

User prompt (verbatim): "el texto de abajo a la izquierda no se enteinde bien, creo que seria bueno cambiar una de las dos lineas puneadas por linea punto linea, y explicar mejor esos textos de abajo a la derecha"

Codex changed posting-year links to dash–dot, retaining category/advisor dots and all continuous links and widths. Added a pure connectionPattern helper and regression coverage. Enlarged the left connection-name buttons and category key to 12px, increased contrast, and explicitly separated checkbox visibility from clicking a name to edit width. Replaced the tiny uppercase right legend with a readable English explanation panel and matching line samples, including when semantic lines appear, the category/keyword solid exception, shared-advisor links, and the meaning of multiple connections. Semantic thickness is described within its own type, not as research quality. Preserved rendering caches and node geometry. All 17 JavaScript tests passed; browser review confirmed the new labels, dash–dot sample, and working width editor. Saved a screenshot with both explanations visible.

## 2026-10-22 — Preserve appearance while reducing interaction work

User prompt (verbatim): "esta muy pesado busca la forma de que se siga viendo igual pero no se pona leno"

Source review found immediate full redraws on every pointer event, including stationary-target hover, repeated full-resolution image scaling/caption preparation, per-point metric rescans, repeated number formatter creation, and hit testing during dragging. Codex added animation-frame coalescing for drag/zoom/width input, target-change-only hover redraw, cached metric bounds/formatter, cached device-resolution thumbnail artwork (bounded at 256 appearances), and a full-resolution connection/projection layer reused until camera/data/selection/toggle/width changes. Layer buffers are resized only when dimensions actually change. All thesis records, lines, labels, image quality, opacity rules, and semantic strength differences are retained; no reduced-detail mode was added.

All 16 JavaScript tests passed. New renderer tests verify that 100 hover redraws reuse connections/projections, 100 repeated thumbnail draws prepare artwork once, and 100 redraw requests schedule one frame; they also verify invalidation for camera, widths, selection, semantic neighbors, metrics, and pixel ratio. These are work-count checks, not a measured real-device FPS improvement. Browser checks confirmed orbiting, selected-thesis fading, eight semantic neighbors, and no captured console errors. The existing local server remains running.

## 2026-10-22 — Per-connection width editor

User prompt (verbatim): "continuemos"

Resumed the user's deferred request (verbatim): "recuerda  para hacerlo cuando vuelva, quiero que la parte de abajo a la izquierda si toco alguna palabra pueda ver un slider que edita el grosor de las lineas que estoy tocando, y que aparezca un boton paa volver a las lienas predeerminadas"

Added English connection-name buttons that open a shared width editor for one type at a time. Checkboxes independently control visibility. A 25–250% multiplier scales only that type while preserving semantic strength differences and the previous 20% dotted reduction. Reset line widths restores all type multipliers to 100%; changes are page-session preferences and do not move the cloud. Extracted/tested pure width rules in line-widths.mjs and documented controls in README/CODE_GUIDE. All 13 JavaScript tests passed. The local server was stopped, so it was restarted. Browser verification changed category width to 25%, checked the year remained at 100%, then reset and verified category returned to 100%. Left the editor open at defaults and saved a preview.

## 2026-10-22 — Dotted connection width adjustment

User prompt (verbatim): "quiero las lineas punteadas un poco mas delgadas un 20% mas delgadas"

Codex multiplied final dotted connection widths by 0.8, including selected metadata lanes. Continuous connections, opacity, dash spacing, node sizes, and layout remain unchanged. Updated the browser script cache version.

## 2026-10-22 — Research groups and English code explanations

User prompt (verbatim): "dale me gusta, puedes ademas revisar todo el codigo y agregar notas en ingles de que hacer cada parte del codigo"

Codex implemented Research Constellations and Topic × Length, following the preceding recommendation accepted by the user. Deterministic spherical k-means groups original normalized 384-dimensional thesis profiles (up to seven exploratory groups); extracted title vocabulary supplies provisional labels. Current filters retain full-corpus groups while summaries report visible counts and medians excluding missing metrics. Length mode maps the chosen page/word metric to world-space height and point size. Source categories/colors remain unchanged, and ordinary selection still does not reframe the cloud.

Reviewed the server, vector pipeline, frontend layouts/rendering/interactions, import/enrichment/summary scripts, and tests. Added English function/block explanations across these modules plus CODE_GUIDE.md covering responsibilities, data flow, cache invalidation, metric limitations, script overwrite behavior, and cross-store consistency limits. The README's AI-generated technical section documents the new modes. No repository publication or additional dependency was needed.

Verification: 14 Python tests and 10 JavaScript tests passed, including new deterministic cluster/degenerate-input tests and filtered-summary/median checks. The initial restricted API test run failed because local sockets were blocked; rerunning with local socket access passed, without changing tests to hide failures. The real local API returned 86 theses, 348 passages, and seven groups covering every thesis. Browser checks verified both modes, median summaries, and switching page/word sizing. Visual review prompted spacing fixes for layout help and shorter two-line canvas group labels. The application remains local.

## 2026-10-22 — English interface and research-landscape purpose

User prompt (verbatim): "1 todo tiene que estar en ingles en mi projecto, 2 mi readme tambien
3 la idea de lo mas impotante es poder entender y ver graficamente el alcance y tama;od e las tesis y ver entender mas el enfoque general de todsa las tesis
4 dame mas ideas de cosas que puedo hacer o agregar en el embedding"

Codex shortened the README in English and aligned its purpose with comparing thesis lengths and understanding the collection's research landscape. Updated the remaining bilingual search placeholder to English and the page description. Preserved original-language user prompts in this log for assignment fidelity. Tested English semantic queries through the running API: automated-arm/timber returned Responsive Robotic Assembly; bend/change-shape returned Robotic Metamaterials. Other paraphrases gave less appropriate results, so no blanket translation-equivalence claim was made. README explicitly leaves the stricter no-important-word-overlap demonstration for student validation and marks AI-authored material. New visualization ideas were proposed, not implemented.

## 2026-10-22 — More legible thin connections

User prompt (verbatim): "LAS LINEAS DELGADAS ESTAN MUY DELGADAS"

Codex increased fine dotted connection widths from 0.85 to 1.4 pixels (selected: 1.35 to 1.9), their unselected overview opacity from 0.12 to 0.22, and dash length from 1 to 2 pixels. Semantic links now have a 1.4-pixel minimum while keeping their similarity-based maximum. Preserved stronger primary connections and selection dimming. Updated the script cache version.

## 2026-10-22 — Selection must not reframe the cloud

User prompt (verbatim): "CUANDO CARGA LA PRIMERA VISTA Y TOCO ALGUN PROJECTO SE ME DESACOMODA LA VISTA, NO QUIERO QUE SE MUEVA LA NUBE QUE SE MANTENGA EN EL LUAR QUE ESTA, TAMBIEN QUIERO SABER SI EN LA ACTIVIDAD PUEDO HACER BUSQUEDAS POR PALABRA, Y DAME MAS IDEAS DE QUE PODEMOS VISUALIZAR CON LOS EMBENDING"

Codex found a separate selection-dependent viewport margin: opening the details changed the center and fit even after orbit auto-fit was fixed. The desktop detail space is now reserved before any selection so selecting, switching, or closing a thesis keeps framing identical. Extended the regression test to check these three states; all seven JavaScript tests passed. The explicit selected-neighborhood layout still reorganizes intentionally. Read the revised vector database assignment to distinguish optional exact-word search from required semantic retrieval. No additional proposed visualization was implemented without a choice from the user.

## 2026-10-21 — Stable orbit framing

User prompt (verbatim): "siento que cambiaste la forma de orvitar se mueve el zoom"

Codex identified that viewport auto-fit depended on the current rotation, changing the apparent zoom while dragging. Framing extents are now calculated only when the arrangement changes, not during orbiting. Manual wheel zoom remains unchanged. Updated the browser cache version. A regression test checks 24 rotation angles preserve framing and zoom; it passed, as did the six existing relation tests. Tools: local source inspection, apply_patch, Node tests.

This is a living record of the development process for HW6. It keeps important prompts verbatim, identifies the tools used, and records corrections made during development. I will add any later testing, debugging, and design changes that I personally make before submission rather than inventing time I did not spend.

## Tools and roles

- **OpenAI Codex:** Used as a coding collaborator to interpret the requirements, discuss project scope, plan the database schema, create the local web app, and explain errors.
- **KiltHub / Figshare public API:** Used to retrieve the public metadata for the selected MSCD thesis collection.
- **Python `sqlite3`:** Used to create and query the local database.
- **Python `pypdf` and PyMuPDF:** Used to extract page counts, approximate word counts, and representative figures from public thesis PDFs.

## Development record

### 2026-10-19 — Understand the assignment and narrow the topic

I first asked Codex for a summary of the HW6 database assignment. I decided the required CRUD app should be related to something I personally find useful rather than a generic movie or to-do list. I explored a few ideas and settled on the MSCD thesis archive because I wanted a way to see the range of work from the program.

Important prompt, verbatim:

> Dentro esta el instructivo de la actividad que tengo que hacer, dame un resumen de lo que hay que hacer primero y dame ideas de que puedo hacer que sea corto

Important prompt, verbatim:

> tengo dos ideas, una es la pagina de tesis de cmu de mii programa de mscd seria interesante hacer una matrix de contendinos y que se puedan categoriazar cada tema

### 2026-10-20 — Define the data and visual direction

I initially chose the 30 most recent records from the public MSCD KiltHub collection. After viewing the first version, I decided I wanted all collection entries. Each record needs a title, author, date, categories, keywords, original abstract, AI-assisted summary, page count, word count, source link, and a representative image. The database is an editable catalogue, not a copy of the thesis documents.

Important prompt, verbatim:

> me gustaria tambien saber el nuemro de paginas de cada documento, y ademas que graficamene sea una orbita pero que se vea visualemne que s epeuda agrupar y ver y tener una descripcion

Important prompt, verbatim:

> 1 fondo blanco lineas claras, tonos morado radioactivo pero lineas muy myuy delggadas y blanco, quiero que se vea como los raficos de cad de los 80s 90s,

> 2 un punto y dependiendo tenga un centrico de algun color dependiendo de las tematicas, quiero que siempre se vean asi sean una linea super super delgada y punteada, pero dependiendo de lo que uno selecciones se vea una linea ruesas, tambien una iimagen en cuadrito peque;a

> 4 quiero que dependiendo de lo que uno quiera organizar la info se edite un poquito el tama;o de lso punos de las tesis la escala

> 5 si una sercripcion, las palabras clasve y el link y una imagen

### 2026-10-20 — Build the first local version

I created a fresh local Git repository named `mscd-thesis-orbit`. The app uses a SQLite `theses` table, a small Python HTTP server, and a browser-based canvas visualization. I used parameterized SQL queries for all create, read, update, and delete operations. I added filters for category, year, pages, word count, and text search.

I also wrote `scripts/import_collection.py`. It follows all pages of the public collection, retrieves public metadata, and stores source links and abstracts in SQLite. Initially it imported 30 entries and 28 had accessible PDFs for document metrics. The KiltHub API currently returns 84 records; all 84 are now in the database. A second summary script drafts summaries for the additional 54 records from their abstracts while leaving the original 30 summaries alone.

Important prompt, verbatim:

> comienza, tambien tengo que tener el reistro de lo que hablo, dale una miradita al instructivo

### 2026-10-20 — Expand the archive and refine the orbit

After trying the first preview, I asked for the background grid to be removed and for the square images to show the thesis project rather than the generic KiltHub record thumbnail. I asked to include all theses and to draw more than one relationship line when two theses share different things: category, posting year, and relevant keywords. I also asked for the line colors to reflect those relationships.

Codex checked the public collection and found 84 records across its API pages. The import now follows all pages and updates records by their unique source ID. It keeps the original 30 summaries and adds 54 more short drafts based on the KiltHub abstracts; all 84 records have a summary. Categories remain editable thematic groupings.

The grid was removed. The graph draws a separate curve for each shared category, posting year, or specific keyword. Category colors remain stable when filtering. Broad repository tags such as “Architecture” are excluded from keyword links so that a general discipline label does not connect unrelated projects. Selecting a thesis makes its connections brighter, and checkboxes let me show or hide each relationship type.

The image enrichment pass reads public thesis PDFs and extracts candidate project figures, with the PDF page recorded for attribution. It found figures for 82 records; two KiltHub entries do not expose downloadable PDFs. Candidate sheets were reviewed and several selections were manually corrected because the first automated ranking favored charts or title slides. Review of every figure and any remaining corrections still need to be completed.

Important prompt, verbatim:

> sigamos con lo que falta, agrega todas las tesis, pero quiero que entre las tesis salga mas de una linea muy clara punteada en alunos casos continua cuando si tiene que ver, de distintos colores dependiendo de la catgoria de la tesis , a;o si comparten, y agrea todas las tesis, y los cambios que hablamos anoche

### 2026-10-20 — Improve line visibility and explore the archive

I said the line types were difficult to tell apart. Continuous keyword lines are now thicker than the fine dotted category and year links, with a stronger weight on the selected thesis. I also asked to move among the projects in more ways and let the whole cloud extend through 3D space. The arrange menu now has a full volume cloud, category clusters, year bands, and page-count and word-count layouts. Dragging vertically can rotate the view over a full turn.

I also asked whether Carla Flores's thesis is in this collection. I checked the title and author fields in all 84 imported records; no record matched that name. This only establishes that the entry is not in the current public MSCD collection import.

Important prompt, verbatim:

> no se enteinden las lineas quiero que las que son continuas sean mas gruesas, ademas quiero que pueda organizar los projectos de mas formas y que la nube de puntos se acomode en todos los sentidos, ademas no veo el projecto de carla flores si esta? quiero que me digas que mas debe tener esta actividad?

### 2026-10-20 — Correct the KiltHub source and add a year-range filter

I clarified that the source is the exact KiltHub search URL below, not the separate collection endpoint:

> [https://kilthub.cmu.edu/search?q=Master%20of%20Science%20in%20Computational%20Design%20%28MSCD%29&sortBy=posted_date&sortType=desc&itemTypes=8&c659852ac71a7c66c40dc2ea47d0c6e9=Master%20of%20Science%20in%20Computational%20Design%20%28MSCD%29](https://kilthub.cmu.edu/search?q=Master%20of%20Science%20in%20Computational%20Design%20%28MSCD%29&sortBy=posted_date&sortType=desc&itemTypes=8&c659852ac71a7c66c40dc2ea47d0c6e9=Master%20of%20Science%20in%20Computational%20Design%20%28MSCD%29)

> este es el link de tesis que quiero ver mira que la sexta es la de carla, o si no agrega todas las tesis tambien poder hacer un eslider de a;o que pueda escoger desde x fecha hasta otra fecha

My earlier conclusion that Carla was absent was wrong: I had compared against the wrong KiltHub endpoint. The exact thesis search returns 86 results; its sixth result is *Playful computation: Encounters with ephemeral surfaces.*, by Carla Flores Travez. I synchronized the visible orbit to those 86 results, retaining nine older records locally but hiding them from the current archive view. Carla's record includes 94 pages and 23,648 extractable words. The year filter now uses a pair of sliders spanning 2018–2026. New records with public PDFs were also sent through the representative-figure extraction pass.

### 2026-10-20 — Restore the cluster-first orbit and combine the year controls

> no veo la nube como la de antes, no me ustan los dos sliders quiero que sea uno solo con dos puntos y que se vea el a;o en cada una

I restored category clusters as the opening arrangement while keeping the full 3D cloud available in the layout menu. The year range is now one visual track with two draggable handles and a year label positioned above each handle. I added a version query to the page assets so the browser requests the revised interface instead of reusing cached scripts.

### 2026-10-20 — Use matching range sliders for pages and words

> quiero que las pages y las words sea un slider iual que el de los a;os

I changed page-count and word-count filters into dual-handle range sliders that match the year control. Each slider displays the selected lower and upper bounds, filters the thesis records to that interval, and can be reset together with the year, category, and search filters.

### 2026-10-20 — Make thesis thumbnails and metric layouts clearer

> 1 las foticos de las tesis se ven muy chiquitas
> 2 quiero que debajo de la fotico se vea un numerito con el numero de palabras de la tesis, y el numero de paginas para las painas pon la P y las palabras W
> 3 POR QUE LA VISA NORMAL CONECTA CON ROSAFO CASI TODO?
> 4 POR QUE EL ARRANGE BY NO SE ENTIENDE QUIERO QUE SE VEA MAS EVIDENTE SI ES POR PAGINAS QUE SEA UNA GALAXIA MAS ORGANIZADA O PAGINAS
> 5 QUE ME FALTA PARA CUMPLIR CON LA ACTIVIDAD

I enlarged the small canvas figures, added a compact `W` / `P` count beneath each one, and made the thesis image itself selectable. I reduced the opacity of unselected relationship lines so the opening view is less tangled while keeping all field-match links visible; selecting a thesis still highlights its own connections. Page- and word-count arrangements now form five ordered groups and display the collection's low/high values. The assignment checklist is based on the course HW6 PDF; I still need to test the complete CRUD flow and record the demo before submission.

### 2026-10-20 — Focus the orbit on connected theses

> Perfecto me gusta, quiero que cuando toco una tesis que se relaciona con otras las iamenes que no se tocan se les baje la opacidad un poquito y la imagen se vea mas chiquita

When a thesis is selected, figures for theses with at least one currently visible relationship remain at normal size and opacity. Figures without a visible connection become smaller and slightly translucent; changing the relationship checkboxes updates which figures count as connected.

## One mistake from AI and how I corrected it

At first, Codex interpreted my interest in robots as a request to make a separate robot-arm research atlas. That was not my intention. I clarified that the source should be the MSCD thesis category on KiltHub, with robots only being one theme I might discover in the collection. After that correction, I changed the project into an MSCD thesis explorer and used the collection endpoint instead of unrelated robotics sources. This correction mattered because it made the data source, project purpose, and visual grouping much more specific.

## Before I submit

- [ ] Review the AI-assisted summary for every thesis against its original abstract and edit inaccurate wording.
- [ ] Review the extracted image for every thesis and replace any chart, title page, or weak figure with a more representative project render, interface, or prototype image from its thesis PDF. A first pass produced local figures for 82 records; two public entries have no downloadable PDF.
- [ ] Test Create, Read, Update, Delete, all filters, the orbit drag interaction, and source links. Add the exact test results here.
- [ ] Record the short demonstration video showing add, browse/filter, update, and delete operations.
- [ ] Add the GitHub repository link to my portfolio and complete the course submission form.

## 2026-10-21 - Vector-database assignment correction and semantic thesis exploration

Development notes below were recorded by Codex (GPT-6 in this session), not written as the student's reflection. The student should review this record and write their own required README explanations.

Important prompt, verbatim:

> siiiiiii quiero que hagamos eso quiero embending y poder hacer esto, Al seleccionar una tesis, conectar también sus vecinas semánticas; hacer que la fuerza de esas líneas refleje qué tan similares son.
>
> ademas visualmene me usta perooosi me gustaria que se pueda acer mas cosas y ver distintos tipos de organizacion, puede ser tambien como tutores de tesis o asesores de tesis.

The revised HW6 changes the central requirement from conventional CRUD to persistent vector retrieval. Earlier versions of this project used only SQLite metadata and exact category/year/keyword relations. This update adds actual locally computed multilingual embeddings and a persistent Chroma database rather than labeling those older links as semantic.

Implemented: 348 overlapping passages from the complete original abstracts of 86 theses; averaged thesis profiles; semantic text search with matching source excerpts; top-k thesis recommendations with a cosine cutoff; score-driven line thickness/opacity; PCA and selected-thesis neighborhood layouts; source-based advisor filtering/grouping and optional shared-advisor links. FastEmbed runs the multilingual MiniLM model locally without an API key. Public KiltHub Advisor(s) fields exist for 85 theses. Newline-separated names initially merged during HTML cleanup; inspection of the raw metadata revealed this and the parser was corrected to preserve separate people.

The model and Chroma were installed in a project virtual environment. Reproducible setup/build commands, ignored caches, embedding model details, projection limitations, and two observed Spanish semantic queries are documented in a clearly AI-generated technical README section. Codex helped implement and test this system; the source abstracts and advisor data come from KiltHub, not from generated model output.

Verification completed: 11 Python tests and 6 JavaScript tests passed. The model integration test opens the same vector store in separate processes to verify persistence and checks actual Spanish retrieval, metadata isolation, insertion, and removal. A live API test added temporary record 96, found it immediately through a Spanish meaning query, and removed only that test record; the catalogue and vector index returned to 86 theses and 348 passages. Browser checks confirmed ranked search results, Carla's source passage and eight semantic neighbors, plus labeled advisor groups. Explicit display aliases consolidate observed source name variations while retaining published strings and provenance.
