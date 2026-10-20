---
name: openheritage
description: Discover public genealogy records across OpenHeritage with global search and safe links to user-facing profile pages. Use for broad searches spanning archives, photos, memorials, cemeteries, canonical places, collections, researches, authors, or people, and to choose a focused OpenHeritage skill.
metadata:
  version: 3.13.0
---

# OpenHeritage

Use this umbrella skill for cross-domain discovery. Switch to the focused skill when the request centers on one domain:

| Skill | Use for |
|---|---|
| openheritage-archives | Sources, documents, repositories, collections, files, pages, XML, entries, exports |
| openheritage-source-import | Catalog-only Sources, repository references, Authors, tags, coverage, optional SourceDocuments and files |
| openheritage-newspaper-import | Complete newspaper issue preparation, cataloguing, automated collections, page uploads, PAGE XML, verification, and repair |
| openheritage-photos | Historical photos, media variants, photo maps, corrections, people on photos |
| openheritage-memorials | Memorials, cemeteries, cemetery photos, statistics, maps, exports, contributions |
| openheritage-researches | Public and owned research projects and their mapped places |

## Safety and setup

- Prefer anonymous reads. Authenticate only when caller-specific visibility or a mutation is required.
- Treat public search results as discovery leads, not proof of identity or relationship.
- Never use /api/admin/*, internal assistant tools, or destructive endpoints without explicit user intent.
- Never collect, retrieve, summarize, or enumerate profile or contact data. Point the user to the relevant OpenHeritage page instead.
- Follow visibility rules: anonymous calls return public/approved data; authentication may add records visible to that caller.
- Do not print credentials, cookies, or auth headers.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
COOKIE_JAR="\${OPENHERITAGE_COOKIE_JAR:-openheritage-cookies.txt}"
~~~

## Personal API

Use the Personal API for user-authorized contributions. Its interactive
documentation is at `https://openheritage.online/api-docs`, and the OpenAPI 3
document is at `https://openheritage.online/api/openapi/v1.json`. Read the live
operation schema, `x-api-required-scopes`, and multipart field names before a
mutation instead of guessing a request shape.

Personal API tokens are bearer tokens and always include `api:read`. Add only
the write scopes needed for the requested work. Generic Source creation and
optional SourceDocument ingestion follow `openheritage-source-import`. A
complete newspaper issue import normally needs `api:authors` for the canonical
newspaper authority,
`api:sources` for issue Sources and the automated Collection, and
`api:documents` for the issue document, page images, metadata, and PAGE XML.
Standalone clipping PhotoAssets follow `openheritage-photos`. Never send a
personal token to MCP: MCP is anonymous and read-only.

~~~bash
curl -sS -H "Authorization: Bearer $OPENHERITAGE_API_TOKEN" \
  "$BASE/api/authors?query=Newspaper%20name" | jq .
~~~

Do not print, persist, or pass the token in a URL. A 401 means the bearer token
is missing or invalid; a 403 means it lacks the operation's required scope or
the caller lacks record-level authority.

## MCP public search

For read-only public record discovery, prefer the MCP Streamable HTTP server at
`https://openheritage.online/mcp`. It provides `search_records`,
`search_memorials`, `search_cemeteries`, `search_sources`, `search_documents`,
`search_repositories`, and `search_places`. Canonical places are searched through
`search_places` rather than the federated `search_records` index. It accepts a
required text query plus optional latitude, longitude, radiusKm, typeCode, and
hasCoordinates filters.
It also provides `search_authors`, `search_collections` and `search_page_text`,
which searches the transcribed text of document pages, including the text layer of
uploaded PDFs, and links each hit to its page; all MCP tools and resources are anonymous and read-only. The source-classification resource mirrors
`/api/tags?entityType=source`.

After selecting a place, use `resources/templates/list` and `resources/read` for
canonical place details, children, revisions and revision comparisons, external
identity matches, and the active place-type catalog. Place resource URIs mirror
`/api/canonical-places` and `/api/place-types`. Use the REST routes below for
other record details, files, authenticated visibility, or mutations.

What OpenHeritage holds in and around a place comes from anonymous
`GET /api/canonical-places/{id}/records-summary` (or
`GET /api/canonical-places/records-summary?ids=…` for up to six places):
public sources and photos counted by canonical id for the place and every
place that has belonged to it (with year ranges, the most common source types
and how many photos have a point), and cemeteries (with their public memorials)
and public researches counted inside the place's current boundary (`areaKind`
`boundary`) or within `radiusKm` (5) of a settlement's point (`radius`). A
null card means the number is not known, never zero. A plain places list
(`GET /api/canonical-places` without a query or filter) reads MongoDB, so a new
place is listed at once; deleted and merged places are listed only for
moderators and administrators. Deleting a place is for moderators and
administrators, and for its creator while no source or photo refers to it
(403 otherwise, 409 `resource_in_use` while referenced).

A searched places list (`GET /api/canonical-places?query=`) marks with
`matchedName` the stored historical, church or source-mention name the query
matched when it is not the display name (`value`, `kind`, `dateWindows` as
years, `citation`); `temporalContextDates` only adds the administrative path
valid at those dates and never filters, while `date` does filter. The known
places at a point come from anonymous
`GET /api/canonical-places/at-point?latitude=&longitude=&temporalContextDates=`:
`containing` lists active places whose outline holds the point, innermost
first, and `nearest` the closest place with a point within 5 km
(`distanceKm`). A signed-in member turns an OpenStreetMap element into a place
with `POST /api/canonical-places/from-osm` `{osmType: node|way|relation,
osmId}`: a place already carrying that OSM id is reused (200, `created`
false); otherwise the server reads the element itself and creates the place
Unverified with `datasetKey` `openstreetmap` (201). Never send place content
for an OSM pick, and never call Nominatim directly; creating places is limited
per hour (429). OpenStreetMap search for people stays
`GET /api/osm/places?q=` (server-side, cached, one request a second).

Place names records keep as written ("Places to match") are read by signed-in
members at `GET /api/unresolved-places?status=open|matched|dismissed&query=&area=&reason=ambiguous|vanished|renamed|other&sort=records|newest`
(only names public records use, with no uploader or record links; each item
has `asWritten`, `area`, `reason`, `candidates`, `suggestions`,
`publicUseCount`, `status`, `matchedPlace`, `version`, `firstSeenAt`,
`addedByCount` (a count of people, never who) and, when dismissed, `dismissedAs`
`notAPlace|differentPlaces`; the list also returns `areas` (value and count,
most names first) and `reasonCounts` for the filter chips),
`GET /api/unresolved-places/{id}/uses` (some of the public records that use the
name, `kind` photo|source|author|research, with `kindCounts`) and
`GET /api/unresolved-places/{id}/history`. Members suggest a place with
`POST /api/unresolved-places/{id}/suggestions` `{placeId, note}`; only
moderators and administrators `match` `{placeId, version, confirmSeveral?}`,
`dismiss` `{version, dismissal?: notAPlace|differentPlaces}` or `undo`
`{version}` (POST `/api/unresolved-places/{id}/…`; 409 on a stale version). A
match links every record that uses the name and keeps each record's text as
written. Items also carry `assignedUseCount` and `openUseCount` (public records
linked and not linked yet: "4 of 7 matched"), `matchMode` `none|whole|records`
and `nameMatches {kind: none|single|several, count, areaIgnored}` (how many
gazetteer places have the name; on the list from the latest ranking, null
before one). A whole `match` of a name several places have answers 422 unless
`confirmSeveral` is true, and is refused while records are matched one by one;
both dismissals are refused then too.

Moderators and administrators only (403 otherwise) also match a name's records
one by one, each from its own clues. `GET /api/unresolved-places/{id}/board`
returns `ranking {state: queued|running|ready, rankedAt}`, `nameMatches`
(+ `others`, up to 20 places for the map), `totals {publicUses, assigned,
privateUses}`, `buckets[]` (`key` `assigned:{placeId:N}`,
`suggested:{placeId:N}:high|medium` or `none`; `kind`, `place`, `confidence`,
`count`, `strong`, `clueSummary`, the first 20 `rows` and `after`), `pending[]`
(steps whose links are still being written) and `runId`. Suggestions are worked
out in the background (a name never ranked is queued when its board is read;
`POST …/board/rank` asks again, 202); poll the board while `ranking.state` is
not `ready` or `pending` is not empty. Page a group with
`GET …/board/rows?bucket=&after=&take=` (≤ 100). Each row has `kind`
photo|source|author|research, `recordId`, `itemId` (a research place), `title`,
`year`, `currentPlace`, `suggestion {placeId, confidence, clues[]}` and
`pending`; a clue is `{kind: point|pointArea|far|recordPlace|recordPoint|siblings|containerRegion|repository|conflict,
distanceKm, place, ancestor, count, share, container: source|collection|day|archive}`
and never a sentence. A low-confidence suggestion inside `none` is only a hint:
never confirm it in bulk. Link records with `POST …/assignments`
`{placeId (null unlinks), usages: [{kind, recordId, itemId?}] (≤ 5,000) | bucket + runId + excluded[], basis: picked|suggested|hint|rest|moved|unlinked}`;
a bucket is a group key, `suggested:{placeId:N}` (a place's strong and likely
groups as one step), `none` with a picked place, or `fit` (a name one place
has: every unlinked record no `far` or `conflict` clue holds back). The answer
is `{place, stepId, assigned, skipped, remaining}` (`remaining`: confirm the
same bucket again); 409 means the suggestions changed, read the board again.
The links are written in the background. Every step is in the history with
`stepId`, `scope`, `usageCount`, `basis` and `canUndo`; undo one with
`POST …/steps/{stepId}/undo` `{version}`, and stop a whole match from linking
new records (the records keep their links) with `POST …/split` `{version}`.

The states the places of a map area belonged to over time come from anonymous
`GET /api/canonical-places/map/eras?west=&south=&east=&north=&zoom=&locale=`
(the "States over time" band of the places map at `/{locale}/places/map`).
Each era names a state (`placeId`, `name` in the locale, else Ukrainian),
its `from` and `until` dates (null: no recorded start, or it still holds),
the `relationType` it was read from (`AdministrativeParent`: the root of the
places' recorded administrative chains; `PoliticalSovereignty`: a
sovereignty relation) and `placeCount`, the places of the area it holds.
Eras are derived from recorded relations only; an empty list means none is
recorded, never that the area had no state.

Public JSON reads use:

~~~bash
curl -sS --get "$BASE/api/search" \
  --data-urlencode "q=Petrenko Kyiv" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=20" | jq .
~~~

Repeat an option such as entityTypes by repeating --data-urlencode. Add -b "$COOKIE_JAR" only for caller-aware reads. Use -L for resources that may return 308.

## Global search

GET /api/search is anonymous federated lexical or hybrid search.

| Parameter | Rules |
|---|---|
| q | Required non-empty query |
| entityTypes | Repeatable filter: source, document, page, entry, memorial-person, memorial-placeholder, cemetery, research, collection, person, photo-asset, author |
| documentId, sourceId | Optional string IDs narrowing document-related hits |
| page | One-based; values below 1 become 1 |
| pageSize | Clamped to 1-100 |
| semantic | false for lexical search; true for hybrid semantic search when configured |
| allPages | false (default) groups page-text hits one per document, showing its best page; true returns one hit per matching page |
| locale | Interface language (uk, en, de, …); hit titles follow it: a written version in that language, else the original |
| textLanguages | Repeatable BCP 47 tag (uk, en, yi-Latn, x-ruthen): only records whose own title, description or question is written — as the original or a person's translation, never a machine one — in any of them. Researches, sources and photos carry it; other record types leave the search while it is set. Not the same as language, a source's content language |

The response is SearchPageDto. A hit may carry titleVersions (the original and human versions of its title, keyed by tag, never machine) and titleLanguage (the tag of the title shown); quote the title in that language and do not present a translation as the original. Entry hits may be enriched with their source and document context. Search still enforces record visibility for the current caller.

~~~bash
curl -sS --get "$BASE/api/search" \
  --data-urlencode "q=Petrenko Kyiv" \
  --data-urlencode "entityTypes=memorial-person" \
  --data-urlencode "entityTypes=document" \
  --data-urlencode "semantic=true" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=20" | jq .
~~~

Use broad search first, then read the exact entity through its focused skill. To read inside a source's documents (pages, transcriptions, images), follow "Reading a source's documents" in openheritage-archives: search page text first, navigate by page metadata, read transcriptions, and fetch images only when needed. Searches are cheap; prefer them to paging through documents. Keep entry mention-only leads separate from direct source, document, person, or memorial matches.

## Genealogy map items

GET /api/map/items is anonymous and lists what the genealogy map shows in a viewport, grouped by layer, as a short list for a side panel. It is for orientation ("which archives, cemeteries, sources and researches lie around this place"), not for harvesting; read an entity through its focused skill.

| Parameter | Rules |
|---|---|
| bbox | Required minLongitude,minLatitude,maxLongitude,maxLatitude; west greater than east crosses the antimeridian |
| zoom | Required, 0-22 |
| layers | Repeatable: source, research, cemetery, repository; omit for all four |
| take | Items per layer, 1-50, default 8 |
| types, authors, yearFrom, yearTo | Source layer only, as on /api/map/sources |

The response is { layers: [{ layer, total, totalIsEstimate, failed?, items }] }. An item has id, entityId, label, href (a path without a locale prefix), latitude, longitude and, where known, subtitle (a settlement or an archival reference), place, country, type, count (an archive's sources, a cemetery's memorials, a research's entries), yearFrom, yearTo and placeCount. A layer whose search failed has failed set and no items; the other layers are still returned.

GET /api/map/items/details?layer=repository&ids={ENTITY_ID} describes up to 100 publicly visible entities of one layer with a stats array of { key, value } figures: for an archive sources, fonds and earliest (a year), for a cemetery memorials and publicMemorials, for a source earliest, latest and references, for a research places, entries and surnames. Entities that are not public are left out.

~~~bash
curl -sS --get "$BASE/api/map/items" \
  --data-urlencode "bbox=30.0,49.5,32.0,50.5" \
  --data-urlencode "zoom=9" \
  --data-urlencode "layers=repository" \
  --data-urlencode "layers=cemetery" \
  --data-urlencode "take=5" | jq .
~~~

## Profile links only

Do not call profile/contact APIs, scrape a profile page, or use automation to collect its contents. Do not reproduce profile biography, roles, contacts, contribution lists, or other personal data.

When a publicId is already supplied by the user or an existing record, return only the user-facing page link:

~~~text
https://openheritage.online/{locale}/u/{publicId}
https://openheritage.online/{locale}/u/{publicId}/{usernameSlug}
~~~

Use an already-known canonical slug when available; do not query profile data to discover one. Supported locale values are uk, en, de, es, fr, it, hu, pl, pt, ro, sk, tr, cs, kk, ka, and he. A profile page names the member by their username unless they chose to show their full name; never infer or add a real name. If no publicId or existing profile URL is available, point the user to https://openheritage.online/{locale}/search so they can find the page themselves.

## Optional browser-session authentication

Use a personal API token for operations exposed by the OpenAPI document. For a
workflow that specifically requires a browser-compatible session, password
login issues an HTTP-only auth_token cookie:

~~~bash
curl -sS -c "$COOKIE_JAR" -X POST "$BASE/api/users/login-password" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg username "$OPENHERITAGE_USERNAME" \
    --arg password "$OPENHERITAGE_PASSWORD" \
    '{username:$username,password:$password}')" | jq .
curl -sS -b "$COOKIE_JAR" "$BASE/api/users/me" | jq .
~~~

Logout after authenticated work:

~~~bash
curl -sS -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
  -X POST "$BASE/api/users/logout" | jq .
~~~

## Rate limits and request pacing

- Start with one in-flight request per resource flow. Fetch pages sequentially; never prefetch, crawl, or enumerate a whole dataset.
- Narrow every query and use the smallest practical page. Fetch detail records, binary files, and media only after the user selects them; reuse results already fetched in the task.
- For viewport maps, request only the current bounds and cancel superseded views. Keep one map request or binary stream active at a time.
- On 429, stop issuing calls. Honor Retry-After or any server-provided retry delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. Retry a mutation after 429 only when the user requested it and the request has its original idempotency key or clientFileId; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Errors

- 400: correct malformed or missing parameters.
- 401: authenticate again only when the requested route requires it.
- 403: stop; the caller lacks access.
- 404: confirm the ID or accept that visibility may intentionally conceal a record.
- 409: reconcile version, duplicate, or state conflicts; never blind-retry.
- 422: correct validation details.
- 429: honor retry guidance and rate limits.
