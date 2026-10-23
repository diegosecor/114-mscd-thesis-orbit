# Code guide

This English guide complements the inline comments. Start with the data flow:

1. Import public catalogue records into SQLite with `scripts/import_collection.py`.
2. Enrich available metrics, figures, and advisors with the enrichment scripts.
3. `semantic.py` splits original abstracts into passages and writes local embeddings to Chroma.
4. `app.py` serves filtered records, semantic search, neighbors, and map data.
5. `static/app.js` transforms world coordinates into an interactive canvas view.

## Server and data

- `app.py`: metadata schema, validation, parameterized SQL, JSON HTTP routes, and CRUD. Its database context commits or rolls back metadata and always closes the connection. Vector writes are separate storage operations, not a distributed transaction; synchronization repairs mismatched profile fingerprints on later reads.
- `semantic.py`: model caching, passage provenance, normalized thesis profiles, cosine retrieval, persistence, and approximate PCA coordinates. Index mutations invalidate derived maps and groups. Similarity scores are not probabilities.
- `research_clusters.py`: deterministic spherical k-means over original 384-dimensional profiles. Farthest-first seeds and ID ordering stabilize repeated runs. At most seven groups are an exploratory heuristic, not official academic categories. Labels are distinctive title terms extracted after clustering. Adding or editing content may change groups; UI filters do not recluster.
- `advisors.py`: explicitly recorded source-name aliases; missing advisors are never guessed.

## Browser

- `static/line-colors.mjs`: null overrides preserve dynamic source palettes. Native color-input events set one per-type override, update the matching legend sample/text, and invalidate the cached connection layer without touching point colors or semantic scores.

- `static/zoom.mjs`: normalizes wheel pixel/line/page units, applies bounded proportional steps, and clamps manual zoom to 0.25–8× without changing orbit rotation.

Rendering caches in `app.js` avoid rebuilding all connections on hover and avoid repeatedly scaling source figures or measuring captions. The scene signature includes camera, canvas resolution, catalogue/position references, selection, semantic neighbors, toggles, and width values. Thumbnail keys include source URL, metrics, dimensions, fading, readiness, and pixel ratio; the cache is bounded at 256 appearances. Metric bounds are cached per immutable fetched result array. Pointer input skips hit-testing during a drag, redraws hover only when its target changes, and coalesces drag/zoom frames. These optimizations retain original drawing order, all relation lanes, and full device resolution.

- `static/line-widths.mjs`: preserves baseline dotted/solid/semantic widths and applies independent per-type presentation multipliers. The editor in `app.js` never toggles visibility or alters positions; resetting creates fresh defaults for every type.

- `static/index.html`: accessible controls, result lists, thesis details, and add/edit form.
- `static/styles.css`: shared colors, CAD typography, overlays, paired slider handles, and responsive rules. Canvas dimensions stay fixed when details open.
- `static/app.js`: local UI state, API requests, filter serialization, layouts, camera rotation, perspective projection, layered rendering, hit testing, and form interactions. Request version counters prevent stale results from replacing a newer search/selection. Only the explicitly selected neighborhood mode rearranges on selection.
- `static/relations.mjs`: exact category/year/keyword/advisor links with independent reasons and stable colors; it does not invent semantic matches.
- `static/constellations.mjs`: pure grouping-display helpers, fixed group centers, and median length calculations excluding missing values. Topic × Length uses the chosen count for vertical position and point size; ordinary constellation mode uses a spherical arrangement.

## Preparation scripts

- `import_collection.py`: paginated public source search, deduplication, editable starter categories, optional PDF metrics, and visible-source synchronization. A deliberately limited import also limits visible records.
- `enrich_documents.py`: cached downloads, heuristic figure candidates, review contact sheets, human figure overrides, missing metrics, and image provenance. Figure-ranking scores are not embeddings.
- `enrich_advisors.py`: source Advisor(s) parsing with preserved separators and bounded network concurrency.
- `build_vectors.py`: reproducible entry point to synchronize persisted embeddings and derived map data.
- `seed_ai_summaries.py`: optional initial curated drafts; rerunning overwrites the original seed summaries.
- `seed_archive_summaries.py`: optional additional drafts; fills empty summaries only. Both require source review.

## Tests

API tests use a temporary metadata database and mocked vectors. Integration tests use a real encoder and isolated Chroma store in separate processes. Import tests simulate source pagination. Cluster tests check coverage, deterministic grouping, and degenerate inputs. JavaScript tests check exact relation semantics, stable selection/orbit framing, and filtered constellation summaries without needing a browser.

This is a local educational application, not an authenticated public deployment. Document length and abstract similarity must not be interpreted as research quality or a complete measure of research scope.
