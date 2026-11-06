---
name: openheritage-catalog-review
description: Review existing OpenHeritage Sources and canonical places on behalf of a signed-in member and correct or complete them from evidence — coverage dates and places, classification tags, repository references, translations, place names, parents and identifiers — with the member's Personal API token. Use when a member asks their agent to check, fix or backfill catalogue records. Use openheritage-source-import to create new Sources and openheritage-archives for read-only research.
metadata:
  version: 1.0.0
---

# OpenHeritage Catalog Review

Help a member keep the shared catalogue correct. You work as that member: every
change carries their name in the record's history, and readers see the result
at once. Write only what the evidence proves, in the words a careful archivist
would use, and leave everything else to the member's report.

Read [references/source-review.md](references/source-review.md) before the
first Source change and [references/place-review.md](references/place-review.md)
before the first place change. Use `openheritage-archives` for reading
documents and pages.

## Safety and setup

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
AUTH="Authorization: Bearer $OPENHERITAGE_API_TOKEN"
UA="User-Agent: <agent-name>/<version> (catalog review)"
~~~

- Ask the member to create a Personal API token at
  `https://openheritage.online/{locale}/profile/api-tokens` with `api:sources`
  (Sources), plus `api:places` only when place changes are wanted. Never ask
  for `api:destructive`: this workflow never deletes.
- Send the token only as `Authorization: Bearer $OPENHERITAGE_API_TOKEN`. Never
  put it in a URL, file, log, checkpoint or report, and never send it to MCP.
  MCP (`https://openheritage.online/mcp`) is anonymous: use it for search only.
- Start with `GET /api/users/me/identity` to learn which account and scopes the
  token carries. Read the live operation schemas at `$BASE/api/openapi/v1.json`
  (`x-api-required-scopes`) before the first write.
- A token always acts as a plain member, even when its owner is a moderator. It
  cannot approve, verify, merge, restore or match "Places to match" entries.
- Send a descriptive `User-Agent`; a bare client may be blocked.
- Never use `/api/admin/*`. Never delete, unlink a document, change a Source's
  type or visibility, or remove a fact you cannot show to be wrong.

## What you may change

| Record | Your agent may write | Otherwise |
|---|---|---|
| Sources the member created | any field except as below | — |
| Other members' `archive-case` Sources that are `public` and `Pending` or `Approved` | content fields; never `type` or `visibility` | 403: report it |
| `Rejected`, private, limited or non-public Sources of others; other Source types | nothing | report the proposed correction |
| Canonical places | names, types, parents, point, existence dates, external ids, reference links | merges, deletions, verification: report for moderators |

Consequences to tell the member before the first such write:

- A change to an `Approved` Source by someone who cannot approve sources sends
  it back to `Pending`, and the review status is public ("not reviewed yet").
- A change to a `Verified` place by a member resets it to `Unverified` until a
  moderator verifies it again.

Count both in the report.

## Nothing technical in OpenHeritage data

Every field you write is catalogue content for a reader of the record. Never
write into any field — descriptions, `scopeNote`, link `note` or `label`,
`unresolved.note`, place notes, provenance `citation`, change summaries:

- that an agent or AI made or checked the change, or for whom;
- how a fact was found (OCR, the page you read it on, search steps, tool or
  model names), confidence, doubt, "probably", "needs review", TODOs;
- timestamps, run or batch ids, checkpoint data, or text addressed to
  moderators.

A published citation or the archive's own catalogue URL is content and goes in
`referenceLinks` or the repository link. "Found on page 3 by OCR" is not. What
you checked, why you changed it, what stayed uncertain and what you skipped
belongs in the report to the member, and only there. A fact that needs a caveat
to be true is not proven: leave the field alone and report it.

## Which Sources, in what order

Agree the scope with the member first: their research, an archive, a fund or a
place. Then build a queue with `GET /api/sources` (paged mode, `skip=0`,
`limit` ≤ 100). Unknown parameter *names* are ignored silently, so confirm each
name below in the live OpenAPI document before trusting a filtered result.

| Parameter | Use |
|---|---|
| `approvalStatus=Pending` | the normal target |
| `missing=coverage-dates\|coverage-places\|place-link\|tags\|repository-reference` (repeatable, all must hold) | a specific gap |
| `minMissing=2` | Sources with several gaps at once |
| `hasDocuments=true` / `hasLinks=true` | something to check the record against |
| `placeId` + `includeDescendants=true`, `yearFrom`, `yearTo` | the member's research area |
| `repositoryId`, `query` | one archive; a fund or title |
| `createdAfter`, `createdBefore`, `updatedAfter`, `updatedBefore` | ISO 8601 instants |
| `sortBy=updatedAt&sortDesc=false` | longest untouched first |

1. **Research interest.** Read the member's own research projects
   (`GET /api/researches?onlyMine=true`, then each `GET /api/researches/{id}`):
   places with `canonicalPlaceId`, years and surnames. Turn them into `placeId`
   with `includeDescendants=true` and `yearFrom`/`yearTo`. Sources without a
   coverage place cannot match a place filter: reach them through the
   repositories of the Sources you matched and a `query` for the place names.
   With no research projects, ask the member for the archive, fund or place.
2. **Priority tiers**, each `approvalStatus=Pending`, `minMissing=2` before `1`:
   1. `hasDocuments=true` — the pages are the evidence;
   2. `hasDocuments=false&hasLinks=true` — a catalogue page or scan to check;
   3. Sources with almost no information — last, and usually only reported.
3. **Order** inside a tier: `sortBy=updatedAt&sortDesc=false`. Continue a run
   with `updatedAfter=<updatedAt of the last row>` instead of a growing `skip`.
4. **Leave fresh work alone.** Add `updatedBefore=<now − 2 hours>`, and check
   `updatedAt` again on the read just before writing: someone may still be
   editing that Source.
5. **New arrivals** (optional extra pass):
   `createdAfter=<now − 3 days>&createdBefore=<now − 1 day>&approvalStatus=Pending`.
6. Touch an `Approved` Source only when the member points at it or names its
   fund.

A 503 with `Retry-After` on a review filter means the search index cannot answer
now; wait as directed instead of paging the whole catalogue.

~~~bash
# two hours ago, UTC: GNU date -d '2 hours ago', BSD/macOS date -v-2H
CUTOFF=$(date -u -d '2 hours ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-2H +%Y-%m-%dT%H:%M:%SZ)
curl -sS --get "$BASE/api/sources" -H "$AUTH" -H "$UA" \
  --data-urlencode "approvalStatus=Pending" --data-urlencode "type=archive-case" \
  --data-urlencode "hasDocuments=true" --data-urlencode "minMissing=2" \
  --data-urlencode "placeId=$PLACE_ID" --data-urlencode "includeDescendants=true" \
  --data-urlencode "updatedBefore=$CUTOFF" \
  --data-urlencode "sortBy=updatedAt" --data-urlencode "sortDesc=false" \
  --data-urlencode "skip=0" --data-urlencode "limit=50" \
  | jq '.items[] | {id, title, approvalStatus, updatedAt, documentCount}'
~~~

## Workflow

1. **Agree scope and limits** with the member: which records, which fields,
   whether `Approved` Sources and `Verified` places may be touched, and how
   many records per run.
2. **Build the queue** as above and keep it in a local checkpoint.
3. **Read each record fully**: `GET /api/sources/{id}` (keep `version` and
   `updatedAt`), `GET /api/sources/{id}/revisions` (what others changed and
   why it looks the way it does), then its documents and pages
   (`openheritage-archives`, "Reading a source's documents").
4. **Gather evidence** for each intended change (see the references). No
   evidence, no write.
5. **Show the first proposed changes** — field, old value, new value, evidence —
   for the first few records and wait for the member's go-ahead. Continue
   without asking only within what the member approved.
6. **Write** one record at a time: `PATCH /api/sources/{id}` with the `version`
   you read and only the fields you change; `PUT /api/canonical-places/{id}`
   with the whole place. Never `PUT` a Source.
7. **Read back** and compare with what you sent. A change that does nothing
   returns the same `version`.
8. **Checkpoint** the record id, the new version and the next action.
9. **Report** at the end (see below).

## Stop and ask

Stop writing and ask the member when:

- 401, or 403 on a record you expected to be editable (the rights changed or
  the token lacks a scope);
- several candidates fit a place, an archive or a duplicate Source;
- the evidence contradicts what another member wrote recently (a revision of
  the last weeks): report it rather than overwrite;
- a change would remove information rather than add or correct it;
- the record is outside the agreed scope.

## Rate limits and request pacing

- Keep one request in flight. Read a record, decide, write, read back, then
  move on; never crawl a repository or prefetch whole documents.
- Use the narrowest filters and a small page; prefer `search_page_text` (MCP)
  or `GET /api/search` with `entityTypes=page` to reading pages in sequence.
- On 429, stop issuing calls. Honor Retry-After or `X-RateLimit-Reset`; otherwise use full-jitter backoff with ceilings of 1, 2, then 4 seconds and make at most three retries.
- Do not automatically retry 409 or 422. On 409 re-read the record and apply
  your change again only if it still fits; on 422 correct the request from the
  `errors` it names. Retry a mutation after 429 only with explicit user intent; never retry an unkeyed mutation.
- After an unknown outcome (timeout, dropped connection), read the record
  before deciding whether the write happened.

## Report to the member

Keep it in the conversation or a local file the member chooses, never in
OpenHeritage. For each record: link
(`https://openheritage.online/{locale}/sources/{id}` or `/places/{id}`), what
changed (old → new), the evidence, and what you left alone and why. Then totals:
records read, changed, unchanged, skipped (403, out of scope, no evidence);
Sources returned to review; places reset to Unverified; proposed corrections
the member or a moderator must make (duplicates, merges, rejected or private
Sources, taxonomy gaps, missing repositories).
