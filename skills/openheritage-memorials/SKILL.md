---
name: openheritage-memorials
description: Search and read OpenHeritage memorials, cemeteries, cemetery photos, maps, nearby records, statistics, public contribution data, exports, and posters, and perform authorized preservation workflows. Use for graves, commemorated people, cemetery discovery, and memorial photo transcription.
metadata:
  version: 1.1.0
---

# OpenHeritage Memorials and Cemeteries

Use this skill for memorial, grave, cemetery, and related public contribution data.

## Safety and setup

- Prefer anonymous reads. Public reads exclude flagged or hidden content.
- Follow 308 redirects to canonical memorial or cemetery IDs and reuse the canonical ID.
- Before a full memorial or cemetery update, fetch the current resource and version; preserve arrays and fields not requested.
- Never upload, transcribe, flag, remove images, merge, split, withdraw, or delete without exact user intent.
- Reuse the same clientFileId or Idempotency-Key when retrying one file.
- Never use /api/admin/* or internal assistant tools.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
COOKIE_JAR="\${OPENHERITAGE_COOKIE_JAR:-openheritage-cookies.txt}"
~~~

## MCP public search and resources

For public discovery, prefer `https://openheritage.online/mcp` with
`search_memorials` and `search_cemeteries`. After selecting a record, use
`resources/templates/list` and `resources/read` for memorial details,
transcription statistics, external references, privacy-safe previews and image
variants, cemetery details and statistics, and cemetery photo galleries and
images. Resource URIs mirror the REST URLs documented below.

MCP reads are anonymous, resolve merged record IDs to canonical URIs, and
inline at most 10 MiB of binary content by default. Flagged memorials and their
media remain unavailable, and memorial image resources always apply configured
privacy redactions. Use REST for maps, nearby discovery, exports, posters,
authenticated reads, and all preservation workflows.

## Memorial discovery

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/v2/memorials/upload/defaults | None | UploadConfigurationDto: file limits, MIME types, concurrency and retries |
| /api/memorials/search | q, cemId, cemName, lang, fromDate, toDate, yearFrom, yearTo, yearType, repeated givenName/surname, hasOcr, myOnly, needsOcr, hasPhoto, coordinateFilter, sortBy, sortDir, skip, take 1-100 | MemorialSearchResponseDto |
| /api/memorials/search/paginated | Same filters and sorting as search, plus page and pageSize 1-100 | MemorialPageResponseDto with compact MemorialListItemDto items |
| /api/memorials/{id} | Memorial GUID | MemorialDto; 308 when merged |
| /api/memorials/{id}/preview | Memorial GUID | WebP primary-image thumbnail |
| /api/memorials/{id}/similar-images | threshold 50-100, maxResults 1-50 | SimilarImagesResponseDto |
| /api/memorials/{id}/transcription/stats | Memorial GUID | TranscriptionStatsDto |
| /api/memorials/{id}/external-references | Memorial GUID | ExternalReferenceDto[] |
| /api/memorials/validate-external-reference | required url | ExternalReferenceValidationResponseDto |
| /api/memorials/marker-types | None | MemorialMarkerTypeDto[] |
| /api/memorials/parse-plot-location | required text | CemeteryPlotLocationDto |
| /api/memorials/{id}/nearby | timeToleranceSeconds default 30, distanceRadiusMeters default 5 | NearbyMemorialsResponseDto |
| /api/memorials/{id}/nearby-discovery | radiusMeters greater than 0 and at most 100; limit 1-100 | PublicNearbyMemorialsResponseDto |

yearType is Any, Birth, or Death. coordinateFilter is NoCoordinates, ExifCoordinates, or OtherCoordinates. Sort fields include CreatedDate, UpdatedDate, PersonName, PersonBirthYear, PersonDeathYear, PersonCount, ImageCount, ImageSimilarity, and PersonAge; direction is Ascending or Descending.

myOnly requires an authenticated identity; anonymous requests ignore it and continue with the remaining public filters.

~~~bash
curl -sS --get "$BASE/api/memorials/search" \
  --data-urlencode "q=Petrenko" \
  --data-urlencode "yearFrom=1880" \
  --data-urlencode "yearTo=1950" \
  --data-urlencode "yearType=Any" \
  --data-urlencode "hasPhoto=true" \
  --data-urlencode "take=20" | jq .
curl -sS -L "$BASE/api/memorials/$MEMORIAL_ID" | jq .
curl -sS -L "$BASE/api/memorials/$MEMORIAL_ID/preview" -o memorial.webp
~~~

The authenticated GET routes transcription/can-transcribe, transcription-tasks, and next-for-editing are not anonymous discovery endpoints.

## Memorial map

GET /api/memorials/map accepts required swLat, swLng, neLat, neLng plus zoom default 18 and forceIndividual default false. Coordinates must be valid and southwest must be below/left of northeast. Zoom is clamped to 0-22.

The response is MemorialMapResponseDto.

- Below zoom 13, expect an empty memorial layer.
- Zoom 13-17 may return markers and clusters.
- Zoom 18-22 returns individual markers.

~~~bash
curl -sS --get "$BASE/api/memorials/map" \
  --data-urlencode "swLat=50.35" \
  --data-urlencode "swLng=30.35" \
  --data-urlencode "neLat=50.55" \
  --data-urlencode "neLng=30.75" \
  --data-urlencode "zoom=18" | jq .
~~~

## Public contributions

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/memorials/contributions/totals | None | MemorialTotalsDto with cemetery, memorial, person and image totals |
| /api/memorials/contributions/leaderboard | Optional year and month 1-12; defaults to current Kyiv month | MemorialContributionLeaderboardsDto |
| /api/memorials/contributions/{memorialId}/history | Memorial GUID | IReadOnlyCollection of MemorialContributionHistoryDto |
| /api/memorials/contributions/daily-stats | days default 365, capped by service at 365 | DailyContributionStatisticsDto |

Leaderboards intentionally mask or omit some user data. Do not attempt to reverse masked identities.

Do not aggregate leaderboard or contribution-history results into contributor profiles. If the user asks about a contributor, provide an already-known user-facing profile link instead.

## Cemetery discovery

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/cemeteries/search | query, skip, take 1-100, latitude, longitude, radiusKm, hasMemorials, missingOsm, missingUkName, missingAddr, comma-separated adminLevel1/adminLevel2, sortBy, sortDirection | CemeterySearchResponseDto |
| /api/cemeteries/admin-hierarchy-facets | None | Cached level-1 and level-2 filter facets |
| /api/cemeteries/{id} | Cemetery GUID | CemeteryDto; 308 when merged |
| /api/cemeteries/{id}/statistics | Cemetery GUID | CemeteryStatisticsDto |
| /api/cemeteries/{id}/surname-statistics | Cemetery GUID | Surname counts and gender breakdown |
| /api/cemeteries/validate-external-reference | required url | ExternalReferenceValidationResponseDto |
| /api/cemeteries/{id}/export/csv | Cemetery GUID | Public memorials as text/csv, one row per person |
| /api/cemeteries/{id}/export/jsonl | Cemetery GUID | Public memorials as application/x-ndjson |
| /api/cemeteries/{id}/poster.pdf | Optional locale | Printable A4 application/pdf |

sortBy is Name, CreatedDate, MemorialCount, or Distance. sortDirection is Ascending or Descending. Supply latitude, longitude, and radiusKm together for geographic search.

~~~bash
curl -sS --get "$BASE/api/cemeteries/search" \
  --data-urlencode "query=Baikove" \
  --data-urlencode "hasMemorials=true" \
  --data-urlencode "sortBy=Name" \
  --data-urlencode "sortDirection=Ascending" \
  --data-urlencode "take=20" | jq .
curl -sS -L "$BASE/api/cemeteries/$CEMETERY_ID/export/jsonl" \
  -o cemetery-memorials.jsonl
curl -sS -L "$BASE/api/cemeteries/$CEMETERY_ID/poster.pdf?locale=uk" \
  -o cemetery-poster.pdf
~~~

## Cemetery map and photos

GET /api/cemeteries/map accepts required swLat, swLng, neLat, neLng plus zoom default 11 and includeGeometry default false. Zoom is clamped to 0-22; low zoom returns clusters and high zoom returns individual cemeteries. Geometry increases payload size.

The response is CemeteryMapResponseDto.

| Anonymous GET | Response |
|---|---|
| /api/cemeteries/{cemeteryId}/photos | CemeteryGalleryDto |
| /api/cemeteries/{cemeteryId}/photos/{photoId}/thumbnail | Cached WebP-compatible thumbnail |
| /api/cemeteries/{cemeteryId}/photos/{photoId}/display | Cached WebP-compatible display image |

~~~bash
curl -sS --get "$BASE/api/cemeteries/map" \
  --data-urlencode "swLat=50.35" \
  --data-urlencode "swLng=30.35" \
  --data-urlencode "neLat=50.55" \
  --data-urlencode "neLng=30.75" \
  --data-urlencode "zoom=11" \
  --data-urlencode "includeGeometry=false" | jq .
curl -sS "$BASE/api/cemeteries/$CEMETERY_ID/photos" | jq .
~~~

## Rate limits and request pacing

- Keep one memorial, cemetery, map, gallery, export, or media request in flight. Do not crawl cemetery records, prefetch result pages, or parallelize image downloads.
- Request only the current map viewport and cancel superseded views. Download an export, poster, preview, or cemetery photo only after user selection; reuse the downloaded artifact.
- On 429, stop issuing calls. Honor Retry-After or a server-provided delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. Retry an upload or other mutation after 429 only with explicit user intent and the original clientFileId or Idempotency-Key; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Authenticated preservation

Set OPENHERITAGE_USERNAME and OPENHERITAGE_PASSWORD only for protected work. POST JSON fields username, password, and useJwt=false to /api/users/login-password, retain the response cookie, and verify GET /api/users/me.

- Prefer v2 upload: read defaults, POST /api/v2/memorials/upload/preview with a stable clientFileId, review proposed coordinates/warnings, then multipart POST /api/v2/memorials/upload using the same clientFileId.
- Use legacy POST /api/memorials/upload only for unsupported metadata and provide a stable Idempotency-Key.
- On exact-duplicate or visual-duplicate 409, stop and resolve relatedMemorialId/relatedImageId.
- Prefer incremental transcription endpoints for a person or note. Full PUT is a replacement and must preserve all existing people, notes, references and images.
- Cemetery creation requires authentication; cemetery updates and cemetery-photo changes require cemetery moderator/admin roles.
- External reference changes, image changes, markers, merges and splits require explicit intent and current-state inspection.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, stop on 403, verify IDs or redirects on 404, and honor rate limits on 429. On mutation 409, re-fetch and reconcile; on 422, correct validation. Logout after mutations.
