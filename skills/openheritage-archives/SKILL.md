---
name: openheritage-archives
description: Search and read OpenHeritage sources, documents, files, pages, XML, table entries, repositories, collections, and exports, and perform authorized contributions including classified newspaper issue and clipping imports. Sources may originate from archives, museums, libraries, publications, personal collections, websites, or other providers. Use for source discovery, record coverage, document browsing, repository holdings, collection hierarchies, and newspaper imports.
metadata:
  version: 1.2.1
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
`search_sources`, `search_documents`, and `search_repositories` tools. After a
tool returns an identifier, use `resources/templates/list` and `resources/read`
for public sources, repositories, collections, documents, current pages, XML,
page images, previews, display images, and document files. Resource URIs mirror
the REST URLs below.

MCP resource reads are anonymous, expose current representations only, and
inline at most 10 MiB of binary content by default. If a resource exceeds the
limit, follow the public REST URL from the MCP error and use HTTP Range where
the endpoint supports it. Keep REST for discovery filters, entries, exports,
authenticated visibility, historical versions, and contribution workflows.

Use --get and --data-urlencode for JSON discovery. Add -b "$COOKIE_JAR" only for caller-aware visibility. Send binary responses to files rather than jq.

## Sources

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/sources | query, limit; add skip for paged mode; type, approvalStatus, repositoryId, repeated authorId, visibility, hasDocuments, sortBy, sortDesc | SourceDto[] without skip; SourcePagedResponseDto with skip. Paged limit is 1-1000; legacy results are capped at 50 |
| /api/sources/repository-links | referenceCode, url, repeated repositoryId, referenceType, limit | SourceRepositoryLinkLookupDto[] or 422 |
| /api/sources/{id} | Source GUID | SourceDto or 404/visibility error |

Author authority records are separate from holding repositories. Discover them with `/api/authors?query=...`, read `/api/authors/{id}`, and use one or more returned UUIDs as repeated `authorId` filters. Repeated authors use OR semantics and combine with every other source filter.

### Personal API newspaper issue import

Use the interactive API reference at `$BASE/api-docs` and its OpenAPI document
at `$BASE/api/openapi/v1.json`. Personal API tokens are bearer tokens and always
include `api:read`. This workflow needs `api:authors` to create or update author
authorities and `api:sources` to create Sources, configure collections, and
upload clipping photo assets. MCP remains anonymous and read-only; never send a
personal token to it.

1. Discover the Source taxonomy with `GET /api/tags?entityType=source` or the
   read-only MCP `source-classification-tags` resource. Walk the returned
   `children` tree and locate the stable code `record-kind-newspaper`. Retain
   its environment-specific `id`; never hard-code an ID from another
   environment. `localizedNames` are display labels, while `isFacetRoot` marks
   a grouping node that cannot be assigned. Newly assigned tags must be active,
   selectable, applicable to `source`, and not facet roots. When editing a
   classified Source, first read it and repeat every current assignment as an
   `assignedTagId` query parameter so retired assignments and their ancestry
   remain visible.

   ~~~bash
   curl -sS --get "$BASE/api/tags" \
     --data-urlencode "entityType=source" |
     jq '.. | objects | select(.code? == "record-kind-newspaper") |
         {id, code, localizedNames, applicableEntityTypes,
          isFacetRoot, isSelectable, isActive}'

   # Repeat assignedTagId once for each classification already on the Source.
   curl -sS --get "$BASE/api/tags" \
     --data-urlencode "entityType=source" \
     --data-urlencode "assignedTagId=$CURRENT_TAG_ID" | jq .
   ~~~

2. Search `GET /api/authors?query=...&kind=organization` and compare canonical
   preferred names and aliases. Reuse the canonical newspaper authority when
   one exists. Only otherwise create an organization with `POST /api/authors`
   and a token containing `api:authors`. Fetch the current authority and include
   `currentVersion` before `PUT /api/authors/{id}`.

   ~~~bash
   curl -sS --get "$BASE/api/authors" \
     --data-urlencode "query=Назва газети" \
     --data-urlencode "kind=organization" | jq .
   ~~~

   A minimal create body has this shape:

   ~~~json
   {
     "kind": "organization",
     "preferredNames": [{ "language": "uk", "value": "Назва газети" }],
     "aliases": [],
     "biography": {},
     "links": []
   }
   ~~~

3. Create one Source per issue with `POST /api/sources` and a token containing
   `api:sources`:

   ~~~json
   {
     "type": "publication",
     "title": "Назва газети — 1932-05-17 — № 42",
     "originDate": { "type": "exact", "value": "1932-05-17" },
     "classificationTagIds": ["resolved-record-kind-newspaper-id"],
     "authorCredits": [{
       "authorId": "canonical-newspaper-author-id",
       "roles": ["institutional-creator"],
       "creditedAs": "Назва газети"
     }]
   }
   ~~~

   Put the exact publication date in ISO order before the printed issue number,
   for example `Назва газети — 1932-05-17 — № 42`. Within a newspaper, ascending
   title order then follows publication order without exposing machine-oriented
   zero padding. Preserve combined issue numbers as printed, such as `№ 42–43`.

   `publication` is the broad Source type and `record-kind-newspaper` is the
   precise classification. Compatible tags from other Source taxonomy facets
   may additionally describe an event, religion, or another dimension. Known
   Source types are `book`, `publication`, `collection`, and `other`; custom
   types must be lowercase hyphenated slugs, and repository-reserved types are
   rejected. Date-expression types are `exact`, `approximate`, `before`,
   `after`, and `range`.

   On create, an omitted or empty `classificationTagIds` assigns no tags. On
   update, omission preserves all assignments, `[]` clears them, and a
   non-empty array replaces the complete set. The limit is 32 distinct IDs.
   Fetch the current Source and preserve its version and unrelated fields
   before `PUT /api/sources/{id}`.

4. Optionally create or update the automated collection described below to
   group issues, then verify the generated children and memberships.

5. Upload each clipping with `POST /api/photo-assets` as multipart data using
   the token scope required by this newspaper workflow. Include the issue
   Source UUID in the case-sensitive `SourceId` form field and follow the live
   OpenAPI schema for the remaining metadata and rights fields.

   ~~~bash
   curl -sS -X POST "$BASE/api/photo-assets" \
     -H "Authorization: Bearer $OPENHERITAGE_API_TOKEN" \
     -F "file=@$CLIPPING_FILE" \
     -F "Title=$CLIPPING_TITLE" \
     -F "SourceId=$SOURCE_ID" | jq .
   ~~~

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

### Automated newspaper collections

Create with `POST /api/collections`; update with
`PUT /api/collections/{id}` after fetching the current collection and version.
Use the structured `automation` object. Its `criteria` may contain
`sourceAuthor` and `repositoryReferenceRegex`, combined by
`criteriaMatchMode: "all"` or `"any"`. Use `dateHierarchy` to group matching
issues into year children:

~~~json
{
  "title": { "uk": "Випуски газети" },
  "visibility": "public",
  "automation": {
    "isActive": true,
    "criteriaMatchMode": "all",
    "criteria": [{
      "kind": "sourceAuthor",
      "authorId": "canonical-newspaper-author-id"
    }],
    "grouping": {
      "kind": "dateHierarchy",
      "dateSource": "originDate",
      "granularity": "year",
      "nonExactBucket": {
        "key": "not-exact-year",
        "title": {
          "uk": "Неточний або невідомий рік",
          "en": "Non-exact or unknown year"
        }
      }
    }
  }
}
~~~

For `dateSource: "originDate"`, only exact `yyyy`, `yyyy-MM`, or `yyyy-MM-dd`
values qualify for a year child. For `dateSource: "coverage"`, every coverage
window must be exact and all windows must fall within one year. Approximate,
before, after, range, missing, cross-year, or otherwise ineligible dates go to
the required localized `nonExactBucket`. The currently supported granularity is
`year`.

Add a `repositoryReferenceRegex` criterion only when issue membership must also
match a specific repository reference. Give it `repositoryId` and
`referenceCodePattern`; use capture mappings and `capturedHierarchy` only when
the desired grouping is based on regex captures instead of issue dates.
Existing flattened repository automation fields remain accepted for
compatibility but are deprecated; do not use them for new rules.

## Rate limits and request pacing

- Keep one archive request in flight. Fetch pages, entries, files, and exports sequentially; never crawl or prefetch an entire repository, collection, or document.
- Use the narrowest filters and smallest practical page. Download a file, page image, XML, CSV, or JSONL only after the user selects it; reuse the response instead of re-downloading it.
- On 429, stop issuing calls. Honor Retry-After or a server-provided delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. Retry a mutation after 429 only with the original idempotency/session identifier and explicit user intent; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Authenticated contributions

Prefer a personal API token for operations published in
`$BASE/api/openapi/v1.json`. Send it as `Authorization: Bearer
$OPENHERITAGE_API_TOKEN`, never in the URL, and verify each operation's
`x-api-required-scopes`. For a protected workflow that specifically requires a
browser-compatible session, set OPENHERITAGE_USERNAME and
OPENHERITAGE_PASSWORD, POST JSON fields username, password, and useJwt=false to
/api/users/login-password, save the response cookie, reuse it with the cookie
jar, and verify GET /api/users/me before mutation.

- Sources: POST /api/sources; PUT or DELETE /api/sources/{id}. Approval/rejection requires moderator access.
- Documents: POST under a source; PATCH or DELETE a document; add/remove original files; report documents.
- Pages: upload images/XML, complete upload sessions, reorder pages, set notes/transcriptions, or bulk-delete only with explicit intent.
- Multipart uploads: create POST /api/source-documents/uploads; PUT numbered application/octet-stream parts starting at 1; complete or abort. Reuse the session and upload every part before completion.
- Repositories and collections: create/update only owned or authorized records; link/unlink sources and child collections explicitly.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, stop on 403, verify IDs and visibility on 404, and honor rate limits on 429. On mutation 409, re-fetch and reconcile versions; on 422, correct validation. Logout when finished.
