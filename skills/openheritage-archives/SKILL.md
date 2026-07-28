---
name: openheritage-archives
description: Search, retrieve, and research OpenHeritage archival sources, documents, original files, pages, images, XML, table entries, repositories, collections, and exports, including OCR and content parsing to answer user questions, and perform authorized archival contributions. Use for archive catalogs, record coverage, document browsing and analysis, repository holdings, and collection hierarchies.
metadata:
  version: 1.2.0
---

# OpenHeritage Archives

Use the public REST API to discover archival provenance and document content.

## Safety and setup

- Prefer anonymous GETs. Authentication expands visibility only when policy permits.
- Separate direct source/document hits from text mentions inside entries.
- Before PUT or PATCH, fetch current state and version. Preserve fields the user did not ask to change.
- Never delete, reassign, reject, unlink, or abort without explicit intent.
- Only an upload-session owner may inspect, complete, or abort that session.
- Never use /api/admin/* or internal assistant tools.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
COOKIE_JAR="\${OPENHERITAGE_COOKIE_JAR:-openheritage-cookies.txt}"
~~~

## MCP public search

For public discovery, prefer `https://openheritage.online/mcp` and its
`search_sources`, `search_documents`, and `search_repositories` tools. Keep
using the REST routes below for record detail, pages, files, exports, and all
authenticated contribution workflows.

Use --get and --data-urlencode for JSON discovery. Add -b "$COOKIE_JAR" only for caller-aware visibility. Send binary responses to files rather than jq.

## Sources

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/sources | query, limit; add skip for paged mode; type, approvalStatus, repositoryId, visibility, hasDocuments, sortBy, sortDesc | SourceDto[] without skip; SourcePagedResponseDto with skip. Paged limit is 1-1000; legacy results are capped at 50 |
| /api/sources/repository-links | referenceCode, url, repeated repositoryId, referenceType, limit | SourceRepositoryLinkLookupDto[] or 422 |
| /api/sources/{id} | Source GUID | SourceDto or 404/visibility error |

~~~bash
curl -sS --get "$BASE/api/sources" \
  --data-urlencode "query=metric books Kyiv" \
  --data-urlencode "hasDocuments=true" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=25" \
  --data-urlencode "sortBy=updatedAt" \
  --data-urlencode "sortDesc=true" | jq .
~~~

## Ukrainian archival call numbers (Фонд–Опис–Справа)

Treat `Фонд 1 Опис 2 Справа 3` (often written `Ф. 1, Оп. 2, Спр. 3` or `1-2-3`) as a **repository-scoped archival reference**, not a global identifier. The same triple may occur in many archives, branches, or revised inventories. Never identify an archive, a source, or a person from a bare `1-2-3`.

1. Keep the supplied wording and every suffix: `спр. 3а`, volume (`т.`), and sheet/page (`арк.`) can distinguish a different unit. Do not drop leading zeroes or silently convert `01-02-003` to `1-2-3`.
2. First establish the holding archive: ask for or use its official name/acronym and city or branch (for example, `ЦДІАК, Київ`). Search `/api/repositories?query=...`, inspect the returned repository, and retain its UUID as `REPOSITORY_ID`. If several repositories match, ask the user to choose; do not search all of them.
3. Try the exact reference-code lookup within that repository. It is an exact stored-value match, so begin with the form the user supplied; if it fails, make only a few deliberate format variants such as `1-2-3` and `Ф. 1, Оп. 2, Спр. 3`, one request at a time. Do not generate a formatting permutation crawl.
4. For each result, follow its `sourceId` with `/api/sources/{sourceId}` and verify the returned repository link, call number, title, dates, locality, and record type. Report it as a possible match until those details agree with the user's case.
5. If no exact code is stored, use `/api/repositories/{REPOSITORY_ID}/sources?query=` with a meaningful textual discriminator such as locality, parish, record type, or year. Avoid broad numeric searches such as `1 2 3`: they are noisy and do not prove a match.

~~~bash
# First find the actual holding archive; keep its UUID, not just its acronym.
curl -sS --get "$BASE/api/repositories" \
  --data-urlencode "query=ЦДІАК Київ" \
  --data-urlencode "limit=10" | jq .

# Exact, archive-scoped lookup for фонд 1, опис 2, справа 3.
curl -sS --get "$BASE/api/sources/repository-links" \
  --data-urlencode "repositoryId=$REPOSITORY_ID" \
  --data-urlencode "referenceCode=1-2-3" \
  --data-urlencode "limit=10" | jq .

# Inspect a candidate before presenting it as the requested archival unit.
curl -sS "$BASE/api/sources/$SOURCE_ID" | jq .

# Only after the exact lookup fails, narrow a repository-local fallback by meaning.
curl -sS --get "$BASE/api/repositories/$REPOSITORY_ID/sources" \
  --data-urlencode "query=метрична книга Київ 1897" \
  --data-urlencode "page=0" \
  --data-urlencode "pageSize=25" | jq .
~~~

## Documents

Cross-source discovery:

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/source-documents | q, skip, limit 1-100, documentType, status, hasPageImages, hasEntries, sourceId, effectiveVisibility, sortBy, sortDesc | DocumentSearchPagedResponseDto |
| /api/source-documents/{documentId} | Document GUID | SourceDocumentDto or 403/404 |

Source-scoped reads:

| Anonymous read | Parameters | Response |
|---|---|---|
| GET /api/sources/{sourceId}/documents | Source GUID | SourceDocumentDto[] |
| GET /api/sources/{sourceId}/documents/{documentId} | Source and document GUIDs | SourceDocumentDto |
| HEAD /api/sources/{sourceId}/documents/{documentId}/files/{assetId} | IDs | Content-Length, Content-Type, Accept-Ranges, optional ETag |
| GET /api/sources/{sourceId}/documents/{documentId}/files/{assetId} | IDs; optional single Range: bytes=start-end | Original file; 200 or 206, 416 for invalid range |

~~~bash
curl -sS --get "$BASE/api/source-documents" \
  --data-urlencode "q=revision lists" \
  --data-urlencode "hasEntries=true" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=25" | jq .

curl -sS -L \
  -H "Range: bytes=0-1048575" \
  "$BASE/api/sources/$SOURCE_ID/documents/$DOCUMENT_ID/files/$ASSET_ID" \
  -o document-part.bin
~~~

Visibility is evaluated for the source and document. A 403 means the record exists but is inaccessible; a 404 can also conceal inaccessible content.

## Pages, XML, and entries

Use the base path /api/sources/{sourceId}/documents/{documentId}.

| Anonymous GET | Parameters | Response |
|---|---|---|
| /pages | None | DocumentPageDto[] |
| /pages/{pageKey} | Page key | DocumentPageDto |
| /pages/{pageKey}/image | Optional versionId; optional single Range header | Original page image, 200/206 |
| /pages/number/{pageNo}/preview | One-based page number | WebP preview |
| /pages/{pageKey}/preview | Page key | WebP preview |
| /pages/{pageKey}/display | Page key | JPEG display derivative; 404 means fall back to /image |
| /pages/{pageKey}/xml | Optional versionId | application/xml |
| /entries | page, pageSize; repeated sort=column:asc|desc; repeated filter=column:pattern | DocumentEntryPagedResponseDto |

Entry filters combine with AND. Unquoted patterns are regex searches; wrap the pattern in double quotes for an exact value. Multiple sorts apply in order.

~~~bash
DOC="$BASE/api/sources/$SOURCE_ID/documents/$DOCUMENT_ID"
curl -sS "$DOC/pages" | jq .
curl -sS "$DOC/pages/$PAGE_KEY/display" -o page.jpg
curl -sS "$DOC/pages/$PAGE_KEY/xml" -o page.xml
curl -sS --get "$DOC/entries" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=50" \
  --data-urlencode "sort=entryNo:asc" \
  --data-urlencode 'filter=surname:"Petrenko"' | jq .
~~~

The path form /pages/{pageKey}/xml/{versionId} is authenticated; do not present it as an anonymous endpoint.

## Research document contents

A request to inspect, transcribe, parse, summarize, or answer a question about a named or selected document authorizes retrieval of the accessible pages or original files needed for that answer. Keep retrieval proportional to the question; do not download unrelated pages or treat the request as permission to crawl the document.

Choose the best available representation:

1. Inspect the document metadata and `/pages` list. Preserve the source ID, document ID, asset ID or page key, and displayed page number throughout the analysis.
2. For page-backed documents, start with existing structured content: `/entries`, page XML, and any transcription in the page metadata. Fetch a page preview or display image when visual confirmation is useful; use the original `/image` only when the derivative is missing or too low-quality for accurate reading.
3. Use an original file when the document has no page records, its embedded text or structure is better suited to the question, or the user asks for whole-file analysis. Select the relevant asset from the document metadata, use HEAD to check its media type and size, then download it through `/files/{assetId}`. Use a Range request only for format inspection or a genuinely partial read, not as a substitute for a complete file that must be parsed.
4. Parse text-bearing PDF, XML, JSON, CSV, spreadsheet, or word-processing files with an appropriate local parser. For PDFs, inspect embedded text first and render or OCR only the scanned pages that need it. OCR page images or image-only files when no reliable text or transcription exists.
5. Search or filter the extracted content for the user's names, places, dates, events, or fields. Read enough surrounding content to interpret a hit correctly, and compare it with the image when layout, handwriting, ditto marks, columns, or OCR ambiguity could change the meaning.
6. Answer from the retrieved evidence. Identify the source and document and cite the page number plus page key, or the original filename plus asset ID. Distinguish verbatim document text, existing transcription or XML, agent-produced OCR, normalized spelling or dates, and inference. State uncertainty and include plausible alternatives for unclear handwriting; never silently turn OCR output into authoritative transcription.

Reuse downloaded material during the task and remove temporary copies when they are no longer needed. Do not publish or reproduce an entire copyrighted document when a focused excerpt or summary answers the question.

## Repositories

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/repositories | query, limit; add skip for paged mode; type, visibility, country, onlyMine, sortBy, sortDesc | RepositoryDto[] or RepositoryPagedResponseDto |
| /api/repositories/selectable | query, limit | Repositories visible for source linking |
| /api/repositories/{id} | Repository GUID | RepositoryDto |
| /api/repositories/selectable/{id} | Repository GUID | Selectable RepositoryDto |
| /api/repositories/{id}/sources | query, page zero-based, pageSize 1-100, sortBy, sortDirection=asc|desc | RepositorySourceReferenceListResponseDto |
| /api/repositories/{id}/sources/export/csv | Repository GUID | text/csv |
| /api/repositories/{id}/sources/export/jsonl | Repository GUID | newline-delimited JSON |

~~~bash
curl -sS --get "$BASE/api/repositories/$REPOSITORY_ID/sources" \
  --data-urlencode "query=parish" \
  --data-urlencode "page=0" \
  --data-urlencode "pageSize=50" | jq .
curl -sS "$BASE/api/repositories/$REPOSITORY_ID/sources/export/csv" \
  -o repository-sources.csv
~~~

## Collections

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/collections | query, parentCollectionId, onlyMine, visibility, origin, sortBy, sortDirection, page, pageSize 1-100 | CollectionListResponse |
| /api/collections/{id} | Collection GUID | CollectionDetailsDto |
| /api/collections/{id}/sources | query, page, pageSize 1-100 | CollectionSourceMembersResponse |
| /api/collections/{id}/children | scope=Direct|Descendants, query, page, pageSize 1-100 | CollectionListResponse |
| /api/collections/by-source/{sourceId} | page, pageSize 1-100 | Collections containing an accessible source |

Visibility values are Public, Unlisted, Private. Origin values are Manual, Imported, SystemGenerated. Sort by CreatedAt, UpdatedAt, Title, or ItemCount; direction is Ascending or Descending. Supplying parentCollectionId, including an empty value, activates parent filtering.

onlyMine requires an authenticated identity; it never exposes another caller's private repository or collection.

~~~bash
curl -sS --get "$BASE/api/collections/$COLLECTION_ID/children" \
  --data-urlencode "scope=Descendants" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=25" | jq .
~~~

## Rate limits and request pacing

- Keep one archive request in flight. Fetch pages, entries, files, and exports sequentially; never crawl or prefetch an entire repository, collection, or document.
- Use the narrowest filters and smallest practical page. Download a file, page image, XML, CSV, or JSONL only after the user selects it; reuse the response instead of re-downloading it.
- On 429, stop issuing calls. Honor Retry-After or a server-provided delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. Retry a mutation after 429 only with the original idempotency/session identifier and explicit user intent; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Authenticated contributions

Set OPENHERITAGE_USERNAME and OPENHERITAGE_PASSWORD only for protected work. POST JSON fields username, password, and useJwt=false to /api/users/login-password, save the response cookie, reuse it with the cookie jar, and verify GET /api/users/me before mutation.

- Sources: POST /api/sources; PUT or DELETE /api/sources/{id}. Approval/rejection requires moderator access.
- Documents: POST under a source; PATCH or DELETE a document; add/remove original files; report documents.
- Pages: upload images/XML, complete upload sessions, reorder pages, set notes/transcriptions, or bulk-delete only with explicit intent.
- Multipart uploads: create POST /api/source-documents/uploads; PUT numbered application/octet-stream parts starting at 1; complete or abort. Reuse the session and upload every part before completion.
- Repositories and collections: create/update only owned or authorized records; link/unlink sources and child collections explicitly.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, stop on 403, verify IDs and visibility on 404, and honor rate limits on 429. On mutation 409, re-fetch and reconcile versions; on 422, correct validation. Logout when finished.
