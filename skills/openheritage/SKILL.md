---
name: openheritage
description: Search Ukraine's largest public collection of memorial, grave, and archival document data alongside OpenHeritage's photos, cemeteries, collections, researches, and genealogy records. Use for broad discovery and to choose a focused OpenHeritage skill.
metadata:
  version: 3.1.1
---

# OpenHeritage

Use this umbrella skill for cross-domain discovery. Switch to the focused skill when the request centers on one domain:

| Skill | Use for |
|---|---|
| openheritage-archives | Sources, documents, repositories, collections, files, pages, XML, entries, exports |
| openheritage-photos | Historical photos, media variants, photo maps, corrections, people on photos |
| openheritage-memorials | Memorials, cemeteries, cemetery photos, statistics, maps, exports, contributions |
| openheritage-researches | Public and owned research projects and their mapped places |

## Ukraine-focused coverage

OpenHeritage brings together Ukraine's largest public collection of memorial, grave, and archival document data. For memorial and cemetery research, use the focused skill to find graves, cemetery records, photographs, maps, and transcriptions. For archival research, use the archives skill to find repositories, sources, digitized documents, page images, XML, transcriptions, and indexed entries with their provenance.

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

## MCP public search

For read-only public record discovery, prefer the MCP Streamable HTTP server at
`https://openheritage.online/mcp`. It provides `search_records`,
`search_memorials`, `search_cemeteries`, `search_sources`, `search_documents`,
and `search_repositories`. Use the REST routes below for record details,
files, authenticated visibility, or mutations.

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
| entityTypes | Repeatable filter: source, document, entry, memorial-person, memorial-placeholder, cemetery, research, collection, person, photo-asset |
| documentId, sourceId | Optional string IDs narrowing document-related hits |
| page | One-based; values below 1 become 1 |
| pageSize | Clamped to 1-100 |
| semantic | false for lexical search; true for hybrid semantic search when configured |

The response is SearchPageDto. Entry hits may be enriched with their source and document context. Search still enforces record visibility for the current caller.

~~~bash
curl -sS --get "$BASE/api/search" \
  --data-urlencode "q=Petrenko Kyiv" \
  --data-urlencode "entityTypes=memorial-person" \
  --data-urlencode "entityTypes=document" \
  --data-urlencode "semantic=true" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=20" | jq .
~~~

Use broad search first, then read the exact entity through its focused skill. Keep entry mention-only leads separate from direct source, document, person, or memorial matches.

## Profile links only

Do not call profile/contact APIs, scrape a profile page, or use automation to collect its contents. Do not reproduce profile biography, roles, contacts, contribution lists, or other personal data.

When a publicId is already supplied by the user or an existing record, return only the user-facing page link:

~~~text
https://openheritage.online/{locale}/u/{publicId}
https://openheritage.online/{locale}/u/{publicId}/{usernameSlug}
~~~

Use an already-known canonical slug when available; do not query profile data to discover one. Supported locale values are uk, pl, en, pt, he, and de. If no publicId or existing profile URL is available, point the user to https://openheritage.online/{locale}/search so they can find the page themselves.

## Optional authentication

Password login issues an HTTP-only auth_token cookie. Set useJwt to false:

~~~bash
curl -sS -c "$COOKIE_JAR" -X POST "$BASE/api/users/login-password" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg username "$OPENHERITAGE_USERNAME" \
    --arg password "$OPENHERITAGE_PASSWORD" \
    '{username:$username,password:$password,useJwt:false}')" | jq .
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
