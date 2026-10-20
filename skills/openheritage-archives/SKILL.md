---
name: openheritage-archives
description: Search and read OpenHeritage sources, documents, files, pages, XML, table entries, repositories, collections, and exports. Sources may originate from archives, museums, libraries, publications, personal collections, websites, or other providers. Use for source discovery, record coverage, document browsing, repository holdings, and collection hierarchies. Use openheritage-source-import for generic ingestion and openheritage-newspaper-import for complete newspaper issues.
metadata:
  version: 1.10.0
---

# OpenHeritage Sources and Documents

Use the public REST API to discover provenance and document content. An
OpenHeritage source is a general provenance entity: it may represent material
from an archive, museum, library, publication, personal collection, website, or
another provider. Do not assume a source or repository is archival; inspect its
type and metadata.

## Safety and setup

- Prefer anonymous GETs. Authentication expands visibility only when policy permits.
- Separate direct source/document hits from text mentions inside entries.
- Before PUT or PATCH, fetch current state and version. Preserve fields the user did not ask to change.
- Never delete, reassign, reject, unlink, or abort without explicit intent.
- Only an upload-session owner may inspect, complete, or abort that session.
- Never use /api/admin/* or internal assistant tools.
- For Personal API mutations, follow the live OpenAPI operation and send the
  personal token only in the Authorization bearer header.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
COOKIE_JAR="\${OPENHERITAGE_COOKIE_JAR:-openheritage-cookies.txt}"
~~~

## MCP public search

For public discovery, prefer `https://openheritage.online/mcp` and its
`search_sources`, `search_documents`, and `search_repositories` tools. To find
words, names or phrases inside transcribed pages, use `search_page_text` with a
required `query` and optional `documentId`, `sourceId` and `semantic` (default
true: keyword and meaning-based matches). Each hit names its document, page
number and page key and links to `/documents/{documentId}/pages/{pageKey}`.
After a tool returns an identifier, use `resources/templates/list` and `resources/read`
for public sources, repositories, collections, documents, current pages, XML,
page images, previews, display images, and document files. Resource URIs mirror
the REST URLs below.

MCP resource reads are anonymous, expose current representations only, and
inline at most 10 MiB of binary content by default. If a resource exceeds the
limit, follow the public REST URL from the MCP error and use HTTP Range where
the endpoint supports it. Keep REST for discovery filters, entries, exports,
authenticated visibility, historical versions, and contribution workflows.

Use --get and --data-urlencode for JSON discovery. Add -b "$COOKIE_JAR" only for caller-aware visibility. Send binary responses to files rather than jq.

## Reading a source's documents

A Source holds zero or more SourceDocuments; a document holds ordered pages.
Each page may carry an image, a transcription, a contributor note and research
metadata (title, description, reference links). Read in this order and stop as
soon as you have the answer:

1. **Search first; it is cheap.** Platform search is an index lookup, far
   cheaper than reading pages, images or files. To find a name, place, date or
   phrase inside a source, call `search_page_text` (MCP) or `GET /api/search`
   with `entityTypes=page`, narrowed by `sourceId` or `documentId`, and
   `allPages=true` for every matching page rather than one per document. The
   page index covers transcriptions, PDF text layers, page notes and page
   metadata titles and descriptions. Each hit gives `documentId`, `pageKey`,
   `pageNo` and the matched passage, so you can jump straight to the page.
   Run several narrow searches (spelling variants, Cyrillic and Latin forms,
   `semantic=false` for exact words) before reading pages in sequence.
2. **List the source's documents**: `GET /api/sources/{sourceId}/documents`.
   Each SourceDocumentDto gives `title`, `documentType`, `pageCount`,
   `hasPageImages`, `hasEntries`, `entryCount` and `originalAssets`. Pick the
   document from that metadata. If `hasEntries` is true, query `/entries` with
   filters: it is structured and usually cheaper than reading pages.
3. **Read page metadata to navigate.** `GET .../pages` returns every active
   page in order with `pageNo`, `pageKey`, `metadata.title`,
   `metadata.description`, `note`, `currentImage` (size and dimensions) and the
   full `transcription`. For a long document, project only what you need
   instead of keeping the whole response:

   ~~~bash
   DOC="$BASE/api/sources/$SOURCE_ID/documents/$DOCUMENT_ID"
   curl -sS "$DOC/pages" | jq '[.[] | {pageNo, pageKey,
     title: (.metadata.title // [] | map(.text) | join(" / ")),
     note: .note.text,
     hasImage: (.currentImage != null),
     textChars: (.transcription.fullText // "" | length)}]'
   ~~~

   Page titles often name the section, year, parish or register part, so use
   them (and `pageNo`) to find the right range rather than reading every page.
4. **Read the transcription text** of the selected page:
   `GET .../pages/{pageKey}` → `transcription.fullText`, plus `zones` (regions
   and lines with coordinates) and `transcription.source`: `page-xml`, `ocr`,
   `pdf-text` or `manual` (typed or corrected by a person). Use `GET .../pages/{pageKey}/xml`
   only when the user needs the PAGE XML itself.
5. **Fetch an image only when text is missing or must be checked** against the
   original. Prefer `/preview` (small WebP) to see the layout, then `/display`
   (JPEG derivative; 404 means none exists, fall back to `/image`), and
   `/image` (original, possibly a large TIFF) only when full resolution is
   needed. `currentImage.fileSizeBytes` tells you the cost before you download.
   Pages without an image come from a PDF text layer; see below.
6. **Original files** (`originalAssets`, such as a PDF or an archive) are the
   most expensive read. Fetch them with HEAD first and use Range requests.

Through MCP, the same steps are `search_page_text` → resources
`source-document-pages` → `source-document-page` → `source-document-page-preview`,
`-display` or `-image`. When you cite a page to the user, link
`https://openheritage.online/{locale}/documents/{documentId}/pages/{pageKey}`,
adding `?q=<query>` to highlight the searched words.

## Sources

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/sources | query, limit; add skip for paged mode; type, approvalStatus, repositoryId, repeated authorId, visibility, hasDocuments, sortBy=createdAt\|title\|reference (natural fund/opys/case order; sources without a reference last in both directions), sortDesc, locale (author names), includeCounts=true (adds approvedPhotoCount, the source's approved photos) | SourceDto[] without skip; SourcePagedResponseDto with skip. Paged limit is 1-1000; legacy results are capped at 50. Paged rows also carry documentCount, pageCount and previewDocumentId |
| /api/sources/repository-links | referenceCode, url, repeated repositoryId, referenceType, limit | SourceRepositoryLinkLookupDto[] or 422 |
| /api/sources/{id} | Source GUID; locale | SourceDto or 404/visibility error |

List and detail responses fill `repositoryLinks[].repositoryName`/`repositoryShortName` for repositories you may see, and `authorCredits[].displayName`/`kind`/`placeName`, so there is no need to look each one up.

A Source's detail (`/api/sources/{id}`) carries its title and descriptions in every language: `title` is the original title's text and `descriptions` the original and human versions, while `titleVersions` and `descriptionVersions` give each version with its kind — `{ "uk": { "text": "…", "kind": "original" }, "en": { "text": "…", "kind": "human" } }`. List rows carry only `title` and `descriptions`. `inferred: true` marks a language guessed for a text saved before versions (the title's is the first entry of `languages`, else `uk`); `kind: machine` is an unreviewed machine translation, never a person's. Quote the original when citing a Source, and say which language a translation is in. `languages` stays the language of the material itself, not of its title.

Author authority records are separate from holding repositories. Discover them with `/api/authors?query=...`, read `/api/authors/{id}` (its `externalIdentifiers` carry Wikidata, VIAF and ISNI ids with their URLs), and use one or more returned UUIDs as repeated `authorId` filters. `/api/authors/{id}/overview?locale=` sums up the author's visible works: source, map, photo and scanned-page counts, credit roles, five-year periods, canonical places, repositories, related authors and the first six sources by date as slim rows; it is cached for a few minutes. Repeated authors use OR semantics and combine with every other source filter.

For authorized creation of catalog-only Sources, repository references,
coverage, and optional SourceDocuments, original files, pages, or PAGE XML, use
`openheritage-source-import`.

For complete newspaper issue preparation, organization authority creation,
automated year collections, issue cataloguing, and ordered image/PAGE XML
uploads, use `openheritage-newspaper-import`. For a standalone newspaper
clipping represented as a PhotoAsset, use `openheritage-photos`.

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

### Pages from a PDF text layer

When an uploaded PDF has a text layer, each PDF page becomes a document page with **no image**:
`currentImage` is `null`, `sourceAssetId` names the PDF original asset, `assetPageNo` is the
one-based page inside that PDF, and `transcription.source` is `pdf-text`. Such page keys look like
`pdf-{first 8 hex digits of the asset id}-{page, 5 digits}`. The `/image`, `/preview` and `/display`
endpoints return 404 for these pages; read the text from the page's transcription, and fetch the PDF
itself from `/files/{sourceAssetId}` (single Range requests are supported). A browser opens it at
the page with the `#page={assetPageNo}` fragment. A PDF without a text layer produces no pages.

### Searching page text

Page transcriptions (from PAGE XML uploads, from `PUT /pages/{pageKey}/transcription`, and
from the text layer of uploaded PDFs), page notes and page titles are indexed for search within
seconds of being saved. Hits from a PDF text layer carry `transcriptionSource: "pdf-text"`.
Search them through the global search endpoint with `entityTypes=page`:

~~~bash
curl -sS --get "$BASE/api/search" \
  --data-urlencode "q=Петренко" \
  --data-urlencode "entityTypes=page" \
  --data-urlencode "documentId=$DOCUMENT_ID" \
  --data-urlencode "allPages=true" | jq '.hits[].page'
~~~

Page hits carry `page.documentId`, `page.pageKey`, `page.pageNo` and the matched
passage in `highlights.text`. Without `allPages=true`, global search returns one
hit per document (its best-matching page); with it, one hit per matching page.
Link a reader to `/documents/{documentId}/pages/{pageKey}?q=<query>` to open the
page with the searched words marked.

## Repositories

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/repositories | query (matches the name, the short name and other-language names), limit; add skip for paged mode; type, visibility, country, onlyMine, sortBy, sortDesc | RepositoryDto[] or RepositoryPagedResponseDto |
| /api/repositories/selectable | query, limit | Repositories visible for source linking |
| /api/repositories/{id} | Repository GUID | RepositoryDto; `profile` holds the optional facts an archive page shows: other-language names, founding year, kind, locality, reading-room hours, copy-request note and holdings as the archive states them (all optional) |
| /api/repositories/selectable/{id} | Repository GUID | Selectable RepositoryDto |
| /api/repositories/{id}/sources | query, page zero-based, pageSize 1-100, sortBy, sortDirection=asc|desc | RepositorySourceReferenceListResponseDto; items carry referenceCode, url and referenceType, and totalCount counts only sources the caller may see |
| /api/repositories/{id}/summary | Repository GUID | RepositorySummaryDto: public sources, pages scanned, fonds, first and last year, transcribed and scanned source counts, the ten largest fonds. Served from a cache and rebuilt in the background; `ready` is false until the first build |
| /api/repositories/{id}/collections | parentId (a collection GUID of the repository), limit | RepositoryCollectionNodeListDto: child fonds or opys with source counts and years |
| /api/repositories/{id}/collections/{collectionId}/cases | limit | RepositoryCaseListDto: the first public sources of the collection |
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
| /api/collections | query, parentCollectionId, onlyMine, visibility, origin, sortBy, sortDirection, page, pageSize 1-100, locale (orders a Title sort by that language's titles) | CollectionListResponse |
| /api/collections/{id} | Collection GUID, locale | CollectionDetailsDto with parentCollectionChain and the automation's author and repository names |
| /api/collections/{id}/sources | query, page, pageSize 1-100; view=rows with group=case\|year\|place and locale for slim rows | CollectionSourceMembersResponse (`rows` for view=rows) |
| /api/collections/{id}/stats | Collection GUID | CollectionStatsDto: visible sources and child collections, year span, repositories, scanned pages (cached a few minutes) |
| /api/collections/{id}/children | scope=Direct|Descendants, query, page, pageSize 1-100, locale | CollectionListResponse |
| /api/collections/by-source/{sourceId} | page, pageSize 1-100 | Collections containing an accessible source |

Visibility values are Public, Unlisted, Private. Origin values are Manual, Imported, SystemGenerated. Sort by CreatedAt, UpdatedAt, Title, or ItemCount; direction is Ascending or Descending. Titles sort with numbers compared as numbers ("Fund 127" before "Fund 1000"). Slim rows in `group=case` follow the reference code in the same natural order; `year` and `place` put rows without a year or place last. Collection lists name no owner accounts. Supplying parentCollectionId, including an empty value, activates parent filtering.

onlyMine requires an authenticated identity; it never exposes another caller's private repository or collection.

~~~bash
curl -sS --get "$BASE/api/collections/$COLLECTION_ID/children" \
  --data-urlencode "scope=Descendants" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=25" | jq .
~~~

## Record coverage by place

Answer "which records survive for this place, and when" with the coverage endpoints, which read the
source availability index (it fills a moment after a source is saved). Selections take 1-20
repeated `placeId` (catalog place UUIDs from `/api/canonical-places?query=`), optional repeated
`facet=root:value` (prefix `!` to exclude, for example `record-kind:census`) and
`includePossible=true|false` (sources whose locations only name the place).

| Endpoint | Parameters | Returns |
|---|---|---|
| /api/source-coverage/matrix | placeId..., facet..., includePossible | SourceCoverageMatrixDto: `decades`, one row per record kind (`code`, `counts` per decade, `before`, `after`, `undated`, `total`), `decadeTotals`, `distinctTotal`, `places` (per place `key`, `count`, `minYear`, `maxYear`, `kindCount`). Every number counts distinct sources; a source spanning decades counts in each decade but once in a row total. Cached for a minute |
| /api/source-coverage/summary | placeId..., facet..., includePossible | Linked/possible totals, open-ended buckets and the facet vocabulary (record-kind names per language) |
| /api/source-coverage/results | placeId..., repeated year (a decade is ten values) or bucket=before|after|undated, optional group=record-kind:... (omit for every kind), page, pageSize 1-100 | SourceCoverageResultsDto; items carry `firstYear`/`lastYear` clipped to the selected years, `pageCount`, `documentCount`, `digitised`, `hasEntries`; page 1 adds `placeCounts` |
| /api/source-coverage/suggested-places | limit 1-12 | Catalog places with the most public coverage |
| POST /api/source-coverage/export/csv | JSON: placeIds, locations, facets, includePossible, years or bucket or allFiniteYears | text/csv |

An empty matrix cell means nothing is catalogued yet, not that the records were lost. A 503 means
the index is rebuilding; retry after the `Retry-After` seconds.

```bash
curl -sS --get "$BASE/api/source-coverage/matrix" \
  --data-urlencode "placeId=$PLACE_ID" | jq '{decades, rows: [.rows[] | {code, total}], distinctTotal}'
```

## Rate limits and request pacing

- Keep one archive request in flight. Fetch pages, entries, files, and exports sequentially; never crawl or prefetch an entire repository, collection, or document.
- Searches are cheap: prefer several narrow `search_page_text` or `/api/search` calls to reading a document page by page.
- Use the narrowest filters and smallest practical page. Download a file, page image, XML, CSV, or JSONL only after the user selects it; reuse the response instead of re-downloading it.
- On 429, stop issuing calls. Honor Retry-After or a server-provided delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. Retry a mutation after 429 only with the original idempotency/session identifier and explicit user intent; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Authenticated contributions

Use `openheritage-source-import` for generic Source and SourceDocument creation,
including Source-only catalog/reference records with no digital files. The
summary below identifies available contribution areas but is not an import
workflow.

Prefer a personal API token for operations published in
`$BASE/api/openapi/v1.json`. Send it as `Authorization: Bearer
$OPENHERITAGE_API_TOKEN`, never in the URL, and verify each operation's
`x-api-required-scopes`. For a protected workflow that specifically requires a
browser-compatible session, set OPENHERITAGE_USERNAME and
OPENHERITAGE_PASSWORD, POST JSON fields username and password to
/api/users/login-password, save the response cookie, reuse it with the cookie
jar, and verify GET /api/users/me before mutation.

- Sources: POST /api/sources; PUT or DELETE /api/sources/{id}. Approval/rejection requires moderator access.
- Coverage locations (and author locations, `PUT /api/authors/{id}` `locations`) keep the place name as the record writes it in `name`, with `canonicalPlaceId` when a gazetteer place is proven. A name that cannot be matched yet may join the shared "Places to match" queue: send `unresolved` `{area?, reason: ambiguous|vanished|renamed|other, candidates?: [placeId], note?}` on that location. Reads return its `unresolvedPlaceId`; send it back (or leave it out — the stored entry is kept while the name stays the same). A moderator's match later sets `canonicalPlaceId` and keeps `name` unchanged.
- Documents: POST under a source; PATCH or DELETE a document; add/remove original files; report documents.
- Pages: upload images/XML, complete upload sessions, reorder pages, set notes/transcriptions, or bulk-delete only with explicit intent.
- Multipart uploads: create POST /api/source-documents/uploads; PUT numbered application/octet-stream parts starting at 1; complete or abort. Reuse the session and upload every part before completion.
- Repositories and collections: create/update only owned or authorized records; link/unlink sources and child collections explicitly.
- Collection titles and descriptions are multilingual: reads return `titleVersions` and `descriptionVersions` (`{tag: {text, kind: original|human|machine, by?, from?, inferred?}}`, the original first) beside `title`, `description` and the known `originalTitle`/`originalDescription`. On create or PUT, send versions with exactly one `original` (any BCP 47 tag; the API accepts Russian, as the original or as a human version beside another original — the interface and machine translation never create Russian translations) or the language → text fields with `originalTitle`/`originalDescription` naming the real original language — never key a title `uk` when it is not Ukrainian. Versions win when both are sent. A PUT that leaves out `originalTitle`, `originalDescription`, `description` or the versions, or sends an empty `title`, keeps what is stored; an empty `descriptionVersions` clears the description. Only moderators move a settled original.
- Several sources into one collection: POST /api/collections/{id}/sources with `{"sourceIds": [...]}` (at most 500); the response lists `added`, `alreadyPresent` and `notFound`.
- CSV of sources (signed in): POST /api/sources/export/csv with `{"sourceIds": [...]}`, or with the /api/sources filters (query, type, approvalStatus, repositoryId, visibility, hasDocuments, authorIds, hasLocationName, hasCoordinates, hasCanonicalPlace, hasNoLocation, sortBy, sortDesc) and no ids; at most 5,000 rows.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, skip the inaccessible resource on 403, verify IDs and visibility on 404, and honor rate limits on 429. Record the 403 and continue with other accessible resources; do not treat it as a reason to stop the whole search, evidence that the record is absent, or permission to bypass access controls. Do not repeatedly retry the denied resource without a relevant change in access. On mutation 409, re-fetch and reconcile versions; on 422, correct validation. Logout when finished.
