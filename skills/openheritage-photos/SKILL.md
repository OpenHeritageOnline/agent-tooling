---
name: openheritage-photos
description: Search and read OpenHeritage historical photo assets, image variants, highlights, mapped photos, correction proposals, people identified on photos, and standalone newspaper clipping PhotoAssets, and perform authorized photo preservation workflows. Use for historical photographs and clippings, not complete newspaper issue ingestion.
metadata:
  version: 1.5.0
---

# OpenHeritage Photos

Use this skill for the public historical-photo archive, people identified on
photographs, and standalone newspaper clippings represented as PhotoAssets. Use
`openheritage-newspaper-import` for complete issue Sources, documents, ordered
page images, and PAGE XML.

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
| /api/photo-assets | view, sort, period, location, repeated tagIds, repeated authorId, text, sourceId, placeId, includeDescendants, addedFrom, addedTo, includeTotal, pageToken, pageSize 1-100 | PhotoAssetListResponseDto with opaque nextPageToken |
| /api/photo-assets/{id} | Photo GUID | PhotoAssetDto or 404 |
| /api/photo-assets/timeline-date-range | Repeated tagIds | TimelineDateRangeDto with minYear, maxYear, minMonth and maxMonth (yyyy-MM), totalDated, yearDensity and decadeDensity |
| /api/photo-assets/highlights | limit clamped to 1-50 (default 10) | PhotoAssetHighlightsResponseDto, most popular approved photo first |
| /api/photo-assets/{id}/correction-proposals | Photo GUID | CorrectionProposalDto[] |
| /api/photo-assets/{id}/nearby | limit 1-24, default 12 | PhotoAssetListResponseDto: other approved photos from the same place, nearest first |
| /api/photo-assets/{id}/appreciation | Photo GUID | PhotoAssetAppreciationStateDto (count; active is true only for a signed-in member who appreciates it) |

A photo's location is only its placeReference (placeText, geoJsonPoint, accuracyRadiusInMeters, and
canonicalPlaceId when the uploader linked a gazetteer place; reads add canonicalPlaceName). The link only
points at `/api/canonical-places/{id}`: placeText stays as the photo record writes it. GPS
from the uploaded file is not published (exifData carries no GPS for the public) and is never the
photo's location: on a scan it records where the scan was made.

Pass nextPageToken unchanged to retrieve the next page. Use view=timeline to exclude undated photos; there, period selects photos by the year or month they start in (period accepts yyyy, yyyy-MM, yyyy-MM-dd or a from/to pair), the same year the timeline-date-range yearDensity counts. text matches title, description, place text and the names of people identified on the photo, and a four-digit word also matches photos dated in that year; sourceId narrows to approved photos attached to a source. placeId narrows to approved photos linked to that canonical place; with includeDescendants=true also to photos linked to any place that has belonged to it administratively (read from MongoDB, so a new link is listed at once). Global search (/api/search) takes the same placeId and includeDescendants for photo hits. Repeated authorId values use OR semantics and combine with the other filters. addedFrom and addedTo (yyyy-MM-dd, UTC days, inclusive) narrow to photos added in that range; addedFrom after addedTo answers 422. includeTotal=true adds total (approved photos matching; the unfiltered count is cached) and totalCapped=true when a filtered count stopped at 10,000.

Each list item has identifiedPeopleCount, the number of distinct named people identified on the photo. highlights ranks approved photos by 30-day views plus appreciations over the whole archive (cached for ten minutes); its items also carry displayUrl, the display-size rendition for the featured first photo.

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
| tagIds | Optional repeated tag GUIDs |

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

- Below zoom 14 the response holds grid clusters (`clusters`, at most 500 cells, each with `count`, `approximateCount`, the centroid and the thumbnail of its most recently added photo) and single-photo cells as `points`. From zoom 14 up every photo is a point (at most 1500). `totalInViewport` is the true number of matching photos in the box, not only the ones drawn.
- Each point carries `dateExpression` (the photo's date, when it has one) and `isApproximate`; a cluster is approximate when `approximateCount` equals `count`.
- A cluster's `items` is always empty. Read a cluster's photos with `/api/photo-assets/map/photos?clusterId=`.
- Pins sit on a photo's place reference only; coordinates inside a file's EXIF data are never a photo's location.

GET /api/photo-assets/map/photos is anonymous and returns the photos in a viewport as a paged list, for a side list next to the map.

| Parameter | Rules |
|---|---|
| minLat, maxLat, minLon, maxLon | Same bounding box rules as the map; invalid bounds return 422 |
| zoom | Optional, default 6; it picks the clustering grid that `clusterId` belongs to, so pass the zoom the cluster came from |
| preciseOnly, repeated tagIds | Same filters as the map |
| sort | `newest` (default, most recently added first), `oldest`, `date-asc` or `date-desc`; a sort only orders, photos without a date stay in the list |
| clusterId | Optional `clusterId` from the map response; the list is then that grid cell's photos and the bounding box is ignored |
| pageToken, pageSize | Pass `nextPageToken` unchanged for the next page; pageSize 1-100, default 36 |

The response is PhotoAssetListResponseDto; an invalid bounding box or `clusterId` returns 422 Problem Details.

~~~bash
curl -sS --get "$BASE/api/photo-assets/map/photos" \
  --data-urlencode "minLat=50.35" \
  --data-urlencode "maxLat=50.55" \
  --data-urlencode "minLon=30.35" \
  --data-urlencode "maxLon=30.75" \
  --data-urlencode "zoom=10" \
  --data-urlencode "sort=newest" | jq '.items[] | {id, title, dateExpression}'
~~~

## Media reads

| Anonymous GET | Response |
|---|---|
| /api/photo-assets/{id}/thumbnail | Cached JPEG-compatible thumbnail stream |
| /api/photo-assets/{id}/display | Cached display image stream |
| /api/photo-assets/{id}/full | Full-resolution WebP rendered from the original (never upscaled); the dto's fullUrl |
| /api/photo-assets/{id}/back-image | Reverse-side image, normally WebP |
| /api/photo-assets/{id}/variants | PhotoAssetVariantListResponseDto: approved alternative scans, colourised and other versions |

Use the dto's downloadUrl to save a photo: it is the full-resolution rendition when the licence
allows reuse and the display rendition otherwise. The untouched uploaded file
(/api/photo-assets/{id}/original, the dto's originalUrl) is served only to the photo's owner and
moderators. Fetch /full only when the user needs detail; it can be large and is rendered on first
request. Media routes return 404 when absent or restricted. Write binary output to a file:

~~~bash
curl -sS -L "$BASE/api/photo-assets/$PHOTO_ID/display" -o photo.jpg
curl -sS -L "$BASE/api/photo-assets/$PHOTO_ID/back-image" -o photo-back.webp
curl -sS "$BASE/api/photo-assets/$PHOTO_ID/variants" | jq .
~~~

## Faces on a photo

PhotoAssetDto.personOnPhotoIdentifications lists the faces. Each has a faceNumber (left to right,
then top to bottom by its boundingArea; faces without an area last), a state ("Confirmed" or
"Suggested"), an optional boundingArea in normalized coordinates of the displayed image
({x, y, w, h}), and personOnPhotoId/personOnPhotoName - both empty for a face not identified yet,
and only a name while a suggested new person waits for review. Treat suggested faces as unverified.

| Signed-in POST | Body | Result |
|---|---|---|
| /api/photo-assets/{id}/identifications | {boundingArea?, personOnPhotoId? or personOnPhotoName?, confidence?, rationaleNote?} - an area, a person, or both | 201 PersonOnPhotoIdentificationDto: Suggested for members, Confirmed for the photo's owner or a moderator |
| /api/photo-assets/{id}/identifications/{identificationId}/review | {decision: "accept" or "decline"} | Owner or moderator only; accepting creates a proposed new person, declining removes the suggestion |

Identify faces only when the user asks, reuse an existing person-on-photo id where the person is
already known, and never review a suggestion on the user's behalf without an explicit decision.

## People on photos

A person on photos is public while at least one approved photo shows them with a confirmed face.
Anyone else (only on pending or withdrawn photos, only suggested, or on no photo) is left out of
the list and the sitemap, and their page answers 404 except to their creator and moderators.

| Anonymous GET | Parameters | Response |
|---|---|---|
| /api/photo-asset-resources/persons-on-photo | query, skip at least 0, limit clamped to 1-200 | PersonOnPhotoSearchResponseDto: public people, newest first, or by name with query; each with photoCount and faceCropUrl |
| /api/photo-asset-resources/persons-on-photo/{id} | Subject GUID | PersonOnPhotoDto (photoCount, faceCount, faceCropUrl) or 404 |
| /api/photo-asset-resources/persons-on-photo/{id}/photos | skip at least 0, limit clamped to 1-100 | PersonOnPhotoPhotosResponseDto: approved photos where the person's face is confirmed, total, nextPageToken, and faces[] (the person's faceNumber, state, boundingArea and the photo's personCount, by photoAssetId) |
| /api/photo-asset-resources/persons-on-photo/{id}/faces | Subject GUID | PersonOnPhotoFacesResponseDto: the person's faces on approved photos, suggested first, with cropUrl, confirmedCount and suggestedCount; canReview is true where the signed-in caller owns the photo or moderates |
| /api/photo-asset-resources/persons-on-photo/{id}/co-appearing | limit 1-50 (default 20) | PersonOnPhotoCoAppearanceResponseDto: other people confirmed on the same approved photos, most shared photos first |
| /api/photo-asset-resources/persons-on-photo/{id}/record-links | Subject GUID | PersonOnPhotoRecordLinksResponseDto: "Also found as" links to memorial people and public researches, each Confirmed or Suggested, with title, subtitle and path |
| /api/photo-assets/{id}/faces/{identificationId} | w = 96, 192 or 384 | A square WebP crop of one marked face, cut from the original and never upscaled; use the cropUrl/faceCropUrl the API returns |

With no query, person search returns the latest public people. With query, display-name matching
is case-insensitive and literal, results are ordered by display name, and pages never overlap.
Signed-in members naming a face may add all=true to search every person, listed or not.

~~~bash
curl -sS --get "$BASE/api/photo-asset-resources/persons-on-photo" \
  --data-urlencode "query=Petrenko" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=20" | jq .
curl -sS --get "$BASE/api/photo-asset-resources/persons-on-photo/$PERSON_ON_PHOTO_ID/photos" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=24" | jq .
curl -sS "$BASE/api/photo-asset-resources/persons-on-photo/$PERSON_ON_PHOTO_ID/faces" | jq '.items[] | {photoTitle, faceNumber, state}'
~~~

Contributions about a person (signed in; only when the user asks):

| Signed-in call | Body | Result |
|---|---|---|
| POST /api/photo-asset-resources/persons-on-photo/{id}/record-links | {targetType: "MemorialPerson" or "Research", targetId, memorialPersonId?} | 201 link: Confirmed for the person's creator or a moderator, Suggested otherwise; 409 when already linked |
| POST /api/photo-asset-resources/persons-on-photo/{id}/record-links/{linkId}/review | {decision: "accept" or "decline"} | Creator or moderator only; decline removes the link |
| POST /api/photo-asset-resources/persons-on-photo/{id}/correction-proposals | {kind: "Name", "Dates", "WrongFace" or "SameAs", proposedValue?, proposedBirthDate?, proposedDeathDate?, explanation} | 201 proposal; the person stays unchanged until it is reviewed |
| GET /api/photo-asset-resources/persons-on-photo/{id}/correction-proposals | - | Open proposals, for the creator and moderators |
| POST /api/photo-asset-resources/person-correction-proposals/{proposalId}/review | {decision} | Creator or moderator only; accepting a Name or Dates proposal applies it |

A memorial link may leave out memorialPersonId when the memorial commemorates one person. Only
public researches can be linked. Same-person votes on a suggested face use the photo's
/identifications/{identificationId}/review route above.

## Rate limits and request pacing

- Keep one list, map, person, or media request in flight. Do not crawl the archive, prefetch cursors, or fan out image downloads.
- Request only the current map viewport and cancel superseded views. Fetch thumbnail/display/back-image media only after the user selects a photo; reuse a fetched variant instead of requesting it again.
- On 429, stop issuing calls. Honor Retry-After or a server-provided delay; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. Retry a photo mutation after 429 only with explicit user intent and the original idempotency key or clientFileId; never retry an unkeyed mutation.
- A 429 during login may be an account lockout. Do not retry credentials; wait for the server-directed delay or ask the user to retry later.

## Authenticated preservation

For operations exposed by the Personal API, inspect
`$BASE/api/openapi/v1.json` and send the personal token as an Authorization
bearer header. Tokens always include `api:read`; a standalone newspaper
clipping workflow uses `api:sources` to create or resolve its issue Source and
upload the clipping PhotoAsset. Include the issue UUID in the exact multipart
field `SourceId`. Never send the token to MCP or put it in a URL. Do not use
this PhotoAsset workflow to represent all pages of a complete issue.

For a protected workflow that specifically requires a browser-compatible
session, set OPENHERITAGE_USERNAME and OPENHERITAGE_PASSWORD, POST JSON fields
username and password to /api/users/login-password, retain the
response cookie, and verify GET /api/users/me.

- Submit a photo with POST /api/photo-assets as multipart form data. For a newspaper clipping, first create or resolve its issue Source and include that Source UUID in the multipart `SourceId` field; preserve the returned ID.
- A photo's title and description may be written in several languages. Reads give `title` and `description` (the originals' texts) plus `titleVersions` and `descriptionVersions` — `{ "uk": { "text": "…", "kind": "original" }, "en": { "text": "…", "kind": "human" } }`; `inferred: true` marks a language guessed for a text saved before versions (Ukrainian), `kind: machine` an unreviewed machine translation, never a person's. To name the languages on upload, add multipart fields `TitleVersions[uk].Text`, `TitleVersions[uk].Kind` (`original` or `human`), optionally `TitleVersions[en].From`, and the same for `DescriptionVersions`; they win over `Title` and `Description` (`Title` may then be empty). Exactly one original per text. The API accepts Russian: Russian may be the original, and a Russian text a person wrote beside another original is kept as a human version; the interface and machine translation never create Russian translations. Names, places and inscriptions are written as printed, never translated. Without versions, `Title` and `Description` are stored as Ukrainian originals marked inferred.
- When the place cannot be matched to a gazetteer place yet, keep its name as written: send the name as `PlaceReference.PlaceText` plus `PlaceReference.Unresolved.Reason` (`ambiguous`, `vanished`, `renamed` or `other`) and optionally `PlaceReference.Unresolved.Area`, `PlaceReference.Unresolved.Candidates[i]` (canonical place GUIDs) and `PlaceReference.Unresolved.Note`. The name joins the shared "Places to match" queue (`/api/unresolved-places`, read by signed-in members); reads return its `unresolvedPlaceId`. When a moderator matches the name, the photo gains `canonicalPlaceId` while `placeText` stays as written.
- To link the photo to a gazetteer place, add the multipart field `PlaceReference.CanonicalPlaceId` (a canonical place GUID found through `/api/canonical-places?query=`). The place must exist and be active, or the answer is 422 with `code` `unknown_canonical_place`. An empty `PlaceReference.PlaceText` then takes the place's preferred name; the place's point is never copied into the photo's point.
- A 409 with `code` `duplicate_photo` means the file, or a visually similar one, is already in the archive: the Problem Details carry `existingPhotoAssetId`, `duplicateKind` (`exact` or `visual`) and `similarity` (0-1). Show the existing photo to the user; only when they confirm the new file is another scan, crop or copy of it, submit again with `DuplicateClassification=variant` and `BasePhotoAssetId` set to that id. A 422 with `code` `unsupported_file_type` or `file_too_large` explains the file problem in `detail`.
- Photo author credits (`AuthorCredits[i].Roles[j]`) accept `photographer`, `studio`, `collector`, `digitised-by` and `publisher` besides the general roles (`author`, `editor`, `compiler`, `translator`, `cartographer`, `institutional-creator`); one credit may carry several roles.
- Fetch current PhotoAssetDto before PATCH /api/photo-assets/{id}; only owners or privileged roles may edit. `titleVersions` and `descriptionVersions` (JSON, same shape as reads) win over `title` and `description`; leaving them out or null keeps the stored versions; a plain `title` or `description` that differs from what is stored replaces the original's text and keeps its translations; only moderators move a settled original to another language. On an update, leaving placeReference out keeps the place; a placeReference with empty placeText, no geoJsonPoint and no canonicalPlaceId clears it; canonicalPlaceId links or relinks a gazetteer place (422 `unknown_canonical_place` when it is not active).
- Upload or remove /back-image only with owner/role permission.
- Submit reports and correction proposals only when the user requests them. Moderators accept or decline proposals through protected resource routes.
- Record views and appreciation only as intentional user actions.
- Update (PUT) or delete a person-on-photo only as its creator or a moderator (others get 403 and should propose a correction); confirm identity and linked photos first. Deleting a person keeps their marked faces on the photos as unnamed faces.
- Withdrawal is reversible only according to server policy; permanent DELETE is admin-only.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, stop on 403, treat 404 as absent or concealed content, and honor rate limits on 429. Resolve mutation 409 conflicts or duplicates instead of retrying blindly; correct 422 validation. Logout after mutations.
