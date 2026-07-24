---
name: openheritage-researches
description: Search and read public OpenHeritage genealogy research projects and their mapped places, and create or manage authorized personal research projects. Use for research questions, hypotheses, places, date ranges, people, DNA evidence, source links, and project visibility.
metadata:
  version: 1.0.0
---

# OpenHeritage Researches

Use this skill for research-project discovery and owner-authorized project management. Research projects organize hypotheses and leads; they are not themselves archival proof.

## Safety and setup

- Prefer anonymous discovery and public projects.
- Keep research context separate from direct source, document, memorial, or photo evidence.
- Do not expose private or unlisted research content.
- Before replacing a research, fetch its full current details and version. Preserve embedded entries the user did not ask to change.
- Never delete a research without explicit user intent.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
COOKIE_JAR="\${OPENHERITAGE_COOKIE_JAR:-openheritage-cookies.txt}"
~~~

## Research discovery

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/researches | query, dateFrom, dateTo, placeName, onlyMine, latitude, longitude, radiusKm, sortBy, sortDirection, page, pageSize 1-100 | ResearchListResponse |
| /api/researches/{researchId} | Research GUID | ResearchDetailsDto or 403/404 according to visibility |
| /api/researches/map-places | swLat default -85, swLng -180, neLat 85, neLng 180, zoom default 6 | ResearchMapPlacesResponse for accessible researches |

sortBy is CreatedAt, UpdatedAt, or Relevance. sortDirection is Ascending or Descending. onlyMine is ignored for anonymous callers. Supply latitude, longitude, and radiusKm together for geographic filtering.

Do not filter, group, or enumerate public projects by another user's identity. Point profile-related requests to an already-known user-facing profile page.

~~~bash
curl -sS --get "$BASE/api/researches" \
  --data-urlencode "query=Petrenko" \
  --data-urlencode "placeName=Kyiv" \
  --data-urlencode "dateFrom=1880" \
  --data-urlencode "dateTo=1920" \
  --data-urlencode "sortBy=Relevance" \
  --data-urlencode "page=1" \
  --data-urlencode "pageSize=20" | jq .
curl -sS "$BASE/api/researches/$RESEARCH_ID" | jq .
~~~

Anonymous reads return public projects. Authentication may add owned, shared, or otherwise accessible projects. A 403 means the project exists but is not visible to the caller; a 404 means the ID is unknown.

## Research map

The map endpoint returns unique places with coordinates from accessible researches within the requested viewport.

~~~bash
curl -sS --get "$BASE/api/researches/map-places" \
  --data-urlencode "swLat=49.0" \
  --data-urlencode "swLng=28.0" \
  --data-urlencode "neLat=52.0" \
  --data-urlencode "neLng=32.0" \
  --data-urlencode "zoom=7" | jq .
~~~

Use map results as navigation aids. Coordinate proximity does not prove that a project covers the same jurisdiction or historical place.

## Rate limits and request pacing

- Keep one research list, detail, or map request in flight. Fetch pages sequentially; never crawl, prefetch, or enumerate a user's projects.
- Use narrow place, date, and text filters. Request only the current map viewport and cancel superseded views; reuse results already fetched in the task.
- On 429, stop issuing calls. Honor Retry-After or a server-provided delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409, 422, or any research mutation. After 429, wait, re-fetch the current version, and seek fresh user confirmation; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Authenticated project management

Set OPENHERITAGE_USERNAME and OPENHERITAGE_PASSWORD only for protected work. POST JSON fields username, password, and useJwt=false to /api/users/login-password, store the HTTP-only response cookie, and verify GET /api/users/me.

| Operation | Endpoint | Rules |
|---|---|---|
| Create | POST /api/researches | Authenticated caller becomes owner; validate references |
| Replace | PUT /api/researches/{researchId} | Full aggregate replacement; owner-authorized; include current version |
| Delete | DELETE /api/researches/{researchId} | Owner-authorized and destructive |

Research access values are Public, NonPublic, Unlisted, and Private. Status values include InProgress, Finished, and OnHold. Date entries may represent a specific year, range, before-year, or after-year. Preserve localized title/description dictionaries, people, places, tasks, source/document references, DNA entries, and notes unless the user requests a change.

For an update:

1. GET the exact research with the cookie.
2. Confirm ownership and identity.
3. Modify only requested fields in the complete aggregate.
4. PUT with the current version.
5. On 409, re-fetch and reconcile rather than retrying stale content.
6. Re-fetch after success and report the canonical research ID.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, stop on 403, distinguish inaccessible projects from unknown IDs on 404, and honor rate limits on 429. On mutation 409, reload and reconcile; on 422, correct validation including invalid referenced IDs. Logout after mutation.
