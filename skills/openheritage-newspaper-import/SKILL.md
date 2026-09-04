---
name: openheritage-newspaper-import
description: Prepare, catalog, OCR, import, repair, and verify complete scanned newspaper issues in OpenHeritage. Use for issue-level publication Sources, newspaper organization authors, automated year collections, repository and publication-place provenance, ordered document pages, PAGE XML, and resumable imports. Do not use for standalone newspaper clipping PhotoAssets.
metadata:
  version: 1.0.0
---

# OpenHeritage Newspaper Import

Import complete newspaper issues as reproducible preservation records. Create one
`publication` Source and one `GenericDocument` per issue, then upload its page
images and PAGE XML in reading order. Use `openheritage-photos` instead when the
deliverable is a standalone clipping PhotoAsset.

## Authorization and preservation

- Treat original scans as immutable. Hash them before processing and make normalized working copies in a separate directory.
- Before any mutation, confirm the target environment, holding repository when known, rights declaration, visibility, issue granularity, and publication-place evidence.
- Read the live Personal API at `$BASE/api-docs` and `$BASE/api/openapi/v1.json`; verify operation schemas, multipart fields, limits, and `x-api-required-scopes` instead of relying on examples alone.
- A full import normally needs `api:authors`, `api:sources`, and `api:documents` in addition to the token's `api:read`. Never send a Personal API token to MCP or put it in a URL, file, log, or report.
- Resolve every taxonomy, author, collection, repository, and canonical-place ID in the target environment. Never copy an ID from an example or another environment.
- Never delete an existing page image or XML version during import or repair. Upload a new version and preserve the audit trail.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
~~~

## Workflow

1. Inventory and normalize scans; determine issue boundaries from visual evidence.
2. Search for and reuse exactly one newspaper organization Author, or create it when authorized.
3. Search for and reuse the newspaper's imported root Collection, or create it with Author/year automation.
4. Resolve the newspaper classification, holding repository, publication place, and duplicate issue Sources.
5. Create or reuse one Source and one `GenericDocument` per issue.
6. Upload ordered page images, localized page metadata, and validated PAGE XML sequentially.
7. Read back the collection, Source, document, pages, images, XML, and parsed OCR; then deliver an import report.

Before cataloguing or calling the API, read [references/import-model.md](references/import-model.md). Before generating, uploading, or repairing OCR, also read [references/page-xml.md](references/page-xml.md).

## Inventory and issue boundaries

1. Natural-sort input files, exclude operating-system artifacts, decode every image, and record original SHA-256, dimensions, EXIF orientation, and capture metadata.
2. Identify covers, blank leaves, inserts, duplicates, and issue boundaries visually. A regular physical pattern is supporting evidence, not proof.
3. Transcribe the printed issue number and date from the masthead. Never infer an unreadable value solely from sequence; mark unreadable numbers and incomplete or special issues explicitly.
4. Record every input in a checkpoint manifest, including exclusions and reasons.
5. Normalize copies losslessly according to EXIF orientation, reset the orientation tag, preserve other metadata when possible, and use deterministic filenames.

Prefer:

~~~text
<series>-YYYY-MM-DD-no-NNN-pPPP.jpg
<series>-date-unknown-no-unknown-cCCC-pPPP.jpg
~~~

## Checkpoints and idempotency

- Search before every Author, Collection, Source, and document creation. Reuse one exact match and stop on multiple plausible matches.
- Give the imported Collection a stable series reference and put the same series/issue marker in the document description.
- Fetch current state and version before PUT or PATCH and preserve fields outside the requested change.
- Keep one mutation in flight. After each success, checkpoint request identity, returned IDs, versions, hashes, and the next intended action.
- After an unknown mutation outcome, read current state before retrying. Do not retry 409 or 422 blindly.
- On 429, wait until the later of `Retry-After` and `X-RateLimit-Reset`, add jitter, and retain the original idempotency or upload-session identifier.
- For interrupted chunked uploads, inspect and resume only a session owned by the caller. Abort a session only with explicit intent.

## Upload and verification gates

- Use page keys `001`, `002`, … in display order. Upload the normalized image, set localized page metadata, then upload PAGE XML for that same key.
- Use direct multipart page uploads when accepted by the live API. For files requiring chunking, create one upload session, upload every numbered part starting at 1, and complete it against the intended page image or XML endpoint.
- Validate every XML file offline. Before a large batch, upload one representative image/XML pair, read it back, and confirm schema acceptance, dimensions, coordinates, parsed text, and absence of TSV contamination.
- Verify collection automation asynchronously: exact issue dates belong in the generated year child; missing or non-exact dates belong in the generated fallback child. Do not manually add Sources to generated children.
- Verify Source title, date, language, classification, Author credit, coverage location, repository link, visibility, document rights, page count and order, downloadable original hashes, XML version/schema/hash, parsed OCR, and preview fallback behavior.
- Leave already clean XML untouched during repair. On any concurrent version mismatch, stop and reconcile.

Deliver a report listing created and reused IDs, issue dates/numbers, collection buckets, excluded or ambiguous material, page/XML totals, Author/repository/place/rights decisions, verification results, unresolved conflicts, and the checkpoint-manifest location.
