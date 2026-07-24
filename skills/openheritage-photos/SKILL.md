---
name: openheritage-photos
description: Search and read OpenHeritage historical photo assets, image variants, highlights, mapped photos, correction proposals, and people identified on photos, and perform authorized photo preservation workflows. Use for historical photographs and subjects depicted in them.
metadata:
  version: 1.0.0
---

# OpenHeritage Photos

Use this skill for the public historical-photo archive and people identified on photographs.

## Safety and setup

- Prefer anonymous discovery. Public lists normally contain approved photos.
- Restricted photos return 404 to unauthorized callers; do not treat that as proof the ID never existed.
- Do not record views, toggle appreciation, submit reports/corrections, edit, withdraw, or delete unless requested.
- Never expose private media or use moderation/admin endpoints without the required role.
- Reuse existing person-on-photo subjects instead of creating duplicates.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
COOKIE_JAR="\${OPENHERITAGE_COOKIE_JAR:-openheritage-cookies.txt}"
~~~

## Photo discovery

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/photo-assets | view, sort, period, location, repeated tagIds, text, sourceId, pageToken, pageSize 1-100 | PhotoAssetListResponseDto with opaque nextPageToken |
| /api/photo-assets/{id} | Photo GUID | PhotoAssetDto or 404 |
| /api/photo-assets/timeline-date-range | None | TimelineDateRangeDto |
| /api/photo-assets/highlights | limit clamped to 1-50 | PhotoAssetHighlightsResponseDto |
| /api/photo-assets/{id}/correction-proposals | Photo GUID | CorrectionProposalDto[] |

Pass nextPageToken unchanged to retrieve the next page. Use view=timeline to exclude undated photos. text performs text search; sourceId narrows to approved photos attached to a source.

~~~bash
curl -sS --get "$BASE/api/photo-assets" \
  --data-urlencode "view=timeline" \
  --data-urlencode "text=Kyiv school" \
  --data-urlencode "tagIds=$TAG_ID" \
  --data-urlencode "pageSize=24" | jq .
curl -sS "$BASE/api/photo-assets/highlights?limit=10" | jq .
~~~

## Photo map

GET /api/photo-assets/map is anonymous.

| Parameter | Rules |
|---|---|
| minLat, maxLat, minLon, maxLon | Required bounding box; latitude is clamped to -85..85 and longitude to -180..180; minimum must be below maximum |
| zoom | Optional, default 6 |
| preciseOnly | Optional boolean coordinate-quality filter |

The response is PhotoAssetMapResponseDto; invalid bounds return 422.

~~~bash
curl -sS --get "$BASE/api/photo-assets/map" \
  --data-urlencode "minLat=50.35" \
  --data-urlencode "maxLat=50.55" \
  --data-urlencode "minLon=30.35" \
  --data-urlencode "maxLon=30.75" \
  --data-urlencode "zoom=10" \
  --data-urlencode "preciseOnly=true" | jq .
~~~

## Media reads

| Anonymous GET | Response |
|---|---|
| /api/photo-assets/{id}/thumbnail | Cached JPEG-compatible thumbnail stream |
| /api/photo-assets/{id}/display | Cached display image stream |
| /api/photo-assets/{id}/back-image | Reverse-side image, normally WebP |
| /api/photo-assets/{id}/variants | PhotoAssetVariantListResponseDto |

Media routes return 404 when absent or restricted. Write binary output to a file:

~~~bash
curl -sS -L "$BASE/api/photo-assets/$PHOTO_ID/display" -o photo.jpg
curl -sS -L "$BASE/api/photo-assets/$PHOTO_ID/back-image" -o photo-back.webp
curl -sS "$BASE/api/photo-assets/$PHOTO_ID/variants" | jq .
~~~

## People on photos

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/photo-asset-resources/persons-on-photo | query, skip at least 0, limit clamped to 1-200 | PersonOnPhotoSearchResponseDto |
| /api/photo-asset-resources/persons-on-photo/{id} | Subject GUID | PersonOnPhotoDto or 404 |
| /api/photo-asset-resources/persons-on-photo/{id}/photos | skip at least 0, limit clamped to 1-100 | PersonOnPhotoPhotosResponseDto with approved photos and nextPageToken |

With no query, person search returns the latest subjects. With query, display-name matching is case-insensitive and results are ordered by display name.

~~~bash
curl -sS --get "$BASE/api/photo-asset-resources/persons-on-photo" \
  --data-urlencode "query=Petrenko" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=20" | jq .
curl -sS --get "$BASE/api/photo-asset-resources/persons-on-photo/$PERSON_ON_PHOTO_ID/photos" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=24" | jq .
~~~

## Rate limits and request pacing

- Keep one list, map, person, or media request in flight. Do not crawl the archive, prefetch cursors, or fan out image downloads.
- Request only the current map viewport and cancel superseded views. Fetch thumbnail/display/back-image media only after the user selects a photo; reuse a fetched variant instead of requesting it again.
- On 429, stop issuing calls. Honor Retry-After or a server-provided delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. Retry a photo mutation after 429 only with explicit user intent and the original idempotency key or clientFileId; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Authenticated preservation

Set OPENHERITAGE_USERNAME and OPENHERITAGE_PASSWORD only for protected work. POST JSON fields username, password, and useJwt=false to /api/users/login-password, retain the response cookie, and verify GET /api/users/me.

- Submit a photo with POST /api/photo-assets as multipart form data. Preserve the returned ID.
- Fetch current PhotoAssetDto before PATCH /api/photo-assets/{id}; only owners or privileged roles may edit.
- Upload or remove /back-image only with owner/role permission.
- Submit reports and correction proposals only when the user requests them. Moderators accept or decline proposals through protected resource routes.
- Record views and appreciation only as intentional user actions.
- Update or delete a person-on-photo only as its creator or a moderator; confirm identity and linked photos first.
- Withdrawal is reversible only according to server policy; permanent DELETE is admin-only.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, stop on 403, treat 404 as absent or concealed content, and honor rate limits on 429. Resolve mutation 409 conflicts or duplicates instead of retrying blindly; correct 422 validation. Logout after mutations.
