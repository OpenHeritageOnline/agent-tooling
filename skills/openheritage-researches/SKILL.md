---
name: openheritage-researches
description: Search and read public OpenHeritage genealogy research projects and their mapped places, and create or manage authorized personal research projects. Use for research questions, hypotheses, places, date ranges, people, DNA evidence, source links, and project visibility.
metadata:
  version: 1.4.0
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
| /api/researches | query (surname text, falls back to title/description), surname (repeatable; exact primary surname or variant, any case, no fallback), dateFrom, dateTo, placeName, onlyMine, latitude, longitude, radiusKm, related (research GUID), sortBy, sortDirection, page, pageSize 1-100 | ResearchListResponse |
| /api/researches/{researchId} | Research GUID | ResearchDetailsDto or 403/404 according to visibility |
| /api/researches/{researchId}/related | Research GUID | ResearchRelatedDto: researcherCount, researchCount, radiusKm |
| /api/researches/map-places | swLat default -85, swLng -180, neLat 85, neLng 180, zoom default 6 | ResearchMapPlacesResponse for accessible researches |

sortBy is CreatedAt or UpdatedAt (Relevance is still accepted and lists by creation date). sortDirection is Ascending or Descending. onlyMine is ignored for anonymous callers. Supply latitude, longitude, and radiusKm together for geographic filtering. A date filter matches when one entry date overlaps both ends of the range. When a list filter touches entries (surname, place, dates, area), each item's matchedEntryCount says how many of its entries meet all of them at once.

related lists researches by other owners that share a normalised surname (primary or variant) or have a place within 10 km of one of the given research's places; /related counts them and their distinct owners. Both count only researches the caller may see in the list, never Unlisted or Private ones of other people.

ResearchDetailsDto also carries question (localized, optional), hypotheses (statement, state Open/Supported/Disputed, evidence) and linkedRecords (source, document, memorial or photo with its title and the owner's note). Linked records and record evidence the caller may not see are left out of the response, so an absent record is not proof that none is linked.

### Language versions of the title, description and question

Each text comes twice: title, description and question as language → text (original and human versions), and titleVersions, descriptionVersions and questionVersions with every version and its kind — `{ "uk": { "text": "…", "kind": "original" }, "en": { "text": "…", "kind": "human", "by": "<user id>" } }`. List items carry titleVersions and descriptionVersions. Tags are any well-formed BCP 47 tag (uk, yi-Latn, rue, cu, x-ruthen, ru-x-prerev), returned in canonical case. Exactly one version is the original; `inferred: true` marks a kind guessed from a text stored before versions existed (the original is then Ukrainian, else the first language). Kind machine marks an unreviewed machine translation; never present it as a person's translation.

To write, send the *Versions field (it wins over the language → text field when both are sent); send only text, kind (original or human) and optionally from; the server records by. Rules: exactly one original; Russian (ru and its variants) is accepted — as the original, or as a human version beside another original, credited to its writer (the interface and machine translation never create Russian translations); machine versions are written only by the translation service (send a stored one back unchanged, or as human once reviewed); only moderators move an original that is settled (not inferred, with translations). A client that sends only the language → text dictionary keeps the kind of each language already stored; new languages become translations.

### Machine translation

When an administrator has turned machine translation on (GET /api/configuration → machineTranslation.enabled), a signed-in caller may ask for a research's title, description or question in an interface language: POST /api/translations/research/{researchId}/{field}/{language} with field title, description or question and language one of uk, en, de, es, fr, it, hu, pl, pt, ro, sk, tr, cs, kk, ka, he — never ru (machine translation never produces Russian; translating from a Russian original is fine). 200 returns MachineTranslationDto `{ status: "ready", version: { text, kind, from } }` (kind machine, or the written version that already exists in that language); 202 `{ status: "pending" }` means the local model is translating it — poll GET on the same path every few seconds (it never starts one; 404 translation_not_requested when nobody asked yet, status failed when the attempt failed and may be asked again). Each original text is translated once per language and stored on the research as a kind machine version for every reader; asking again never calls the model. 503 machine_translation_disabled means the switch is off; 422 means the field, language or text cannot be translated (no original, already that language, too long); 429 means the hourly limit (60 requests) was reached — wait, do not retry at once. Personal API tokens need only read access. Names, inscriptions and quoted archival text are never sent; machine text is never shown to search engines. Always label a machine version as machine translation, keep the original beside it, and never send one back as kind human unless a person reviewed it.

Do not filter, group, or enumerate public projects by another user's identity. Point profile-related requests to an already-known user-facing profile page.

~~~bash
curl -sS --get "$BASE/api/researches" \
  --data-urlencode "query=Petrenko" \
  --data-urlencode "placeName=Kyiv" \
  --data-urlencode "dateFrom=1880" \
  --data-urlencode "dateTo=1920" \
  --data-urlencode "sortBy=UpdatedAt" \
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

Set OPENHERITAGE_USERNAME and OPENHERITAGE_PASSWORD only for protected work. POST JSON fields username and password to /api/users/login-password, store the HTTP-only response cookie, and verify GET /api/users/me.

| Operation | Endpoint | Rules |
|---|---|---|
| Create | POST /api/researches | Authenticated caller becomes owner; validate references |
| Replace | PUT /api/researches/{researchId} | Full aggregate replacement; owner-authorized; include current version |
| Delete | DELETE /api/researches/{researchId} | Owner-authorized and destructive |
| Add hypothesis | POST /api/researches/{researchId}/hypotheses | statement (≤ 1000), state, evidence[]; returns the hypothesis |
| Change hypothesis | PUT /api/researches/{researchId}/hypotheses/{hypothesisId} | Same body; replaces its statement, state and evidence |
| Remove hypothesis | DELETE /api/researches/{researchId}/hypotheses/{hypothesisId} | Destructive; confirm with the user |
| Link record | POST /api/researches/{researchId}/linked-records | recordType source, document, memorial or photo; recordId; optional note (≤ 500) |
| Unlink record | DELETE /api/researches/{researchId}/linked-records/{linkedRecordId} | Destructive; confirm with the user |

Evidence kinds are record (recordType and recordId), url (an http or https address and optional label) and haplogroup (dnaType and a haplogroup that one of the research's entries already carries). A hypothesis holds at most 20 pieces of evidence and a research at most 50 hypotheses and 200 linked records. A record you link or cite must exist and be visible to you; a duplicate link answers 409. These edits reload the research themselves, so they need no version.

PUT replaces the whole aggregate except the title, description, question, hypotheses and linkedRecords: each of these is kept as stored when the request leaves it out or sends null (an empty title also keeps it), and replaced when sent (an empty description, question, versions value or list clears it). Prefer the hypothesis and linked-record endpoints over sending those lists in a PUT.

With a personal API token, reads need api:read; creating, replacing and the hypothesis and link edits need api:researches; deleting a research, a hypothesis or a link also needs api:destructive.

A research place keeps its own `name` (the spelling the records give) and `location`, and may link the gazetteer place it is with `canonicalPlaceId` (it must be an active canonical place). A name that cannot be matched yet may join the shared "Places to match" queue: send `unresolved` `{reason: ambiguous|vanished|renamed|other, area?, candidates?: [placeId], note?}` on that place. Reads return `canonicalPlaceId` and `unresolvedPlaceId`; a place sent without them keeps the stored links while its name stays the same. Only names from Public researches count towards the public queue; matching updates every research place of the entry.

Research access values are Public, NonPublic, Unlisted, and Private. Status values include InProgress, Finished, and OnHold. Date entries may represent a specific year, range, before-year, or after-year. Preserve the title, description and question with their versions, places, surnames, entries, DNA entries, links, and notes unless the user requests a change; leave question, hypotheses and linkedRecords out of a PUT unless the user asked to change them.

For an update:

1. GET the exact research with the cookie.
2. Confirm ownership and identity.
3. Modify only requested fields in the complete aggregate.
4. PUT with the current version.
5. On 409, re-fetch and reconcile rather than retrying stale content.
6. Re-fetch after success and report the canonical research ID.

For reads, correct malformed parameters on 400, authenticate only when needed on 401, stop on 403, distinguish inaccessible projects from unknown IDs on 404, and honor rate limits on 429. On mutation 409, reload and reconcile; on 422, correct validation including invalid referenced IDs. Logout after mutation.
