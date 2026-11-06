# Reviewing a Source

Field-by-field checks for an existing Source. The creation rules and full JSON
shapes are in `openheritage-source-import` (`references/source-model.md`); this
file says what to check and how to change it without losing anything.

## Evidence

Use, in this order:

1. the Source's own pages: the case cover, title page, first and last register
   pages, the inventory line pasted inside the cover;
2. the holding archive's finding aid or catalogue page for that unit (its
   repository link `url`, or the archive's site);
3. the Source's existing reference links (Wikisource, FamilySearch, a printed
   catalogue).

Never use memory, analogy with a neighbouring case, or a pattern of reference
codes as evidence. A fact stated only in another OpenHeritage record is a lead
to check, not proof. When sources disagree, write nothing and report both.

## Changing a Source: PATCH

~~~bash
curl -sS -X PATCH "$BASE/api/sources/$SOURCE_ID" -H "$AUTH" -H "$UA" \
  -H "Content-Type: application/json" --data @patch.json
~~~

- Send `version` (as read) and only the fields you change; everything left out
  keeps what is stored.
- An array you send **replaces** the stored set; `[]` clears it. To add one
  coverage segment, tag or link, send the full stored array plus the addition,
  each stored item unchanged (keep every `canonicalPlaceId`, `unresolvedPlaceId`,
  point and name).
- A stale `version` is 409: re-read and decide again.
- Validation failures are 422 `validation_failed` with field-addressed
  `errors`; fix the body, do not retry it unchanged.

~~~json
{
  "version": 7,
  "coverageSegments": [
    {
      "dateWindows": [{ "type": "range", "value": "1850/1875" }],
      "locations": [
        { "name": "Єлисаветград", "canonicalPlaceId": "${PLACE_ID}" }
      ]
    }
  ]
}
~~~

## Coverage

- `originDate` is when the Source itself was made; coverage is the dates and
  places its content is about. Do not copy one into the other.
- Date expressions: `exact` (`1897`, `1897-04`, `1897-04-23`), `approximate`,
  `before`, `after`, `range` (`1897/1902`). Never turn a range into an exact
  date; omit what the evidence does not bound.
- **Fewest segments.** Each place appears once, its years merged into
  contiguous ranges (several date windows on one segment for gaps — never fill
  a gap), and places sharing exactly the same periods share one segment. Never
  one segment per year. When adding to existing coverage, merge and collapse
  the stored and new coverage together.
- **Names stay as written.** A location's `name` is the place as the Source
  names it (Єлисаветград, not Кропивницький; a village as the register spells
  it). The canonical place supplies the link and the point; it never replaces
  the name. Do not translate or modernise a name.
- Add `canonicalPlaceId` only when exactly one active place fits the name,
  the date and the area the Source gives (повіт, parish, gubernia). Search with
  the Source's date (`GET /api/canonical-places?query=…&date=1870-01-01`).
- Otherwise keep the name and send
  `unresolved: {area, reason: ambiguous|vanished|renamed|other, candidates, note}`
  so it joins the shared "Places to match" queue, where moderators decide.
  `area` is the administrative context the Source prints; `candidates` are
  place ids that fit; `note` stays empty unless it states a fact from the
  Source (e.g. the parish), never your process.
- Never add coordinates you inferred. A point comes from the canonical place.
- A metrical book is written in one parish church: the villages its parish
  served are coverage locations, not authors.

## Repository references

- Link an existing repository (`GET /api/repositories?query=…`,
  `GET /api/repositories/{id}`); never create one in this workflow. If the
  holder is not on OpenHeritage, report it.
- The archive code is fund–opys–case joined by hyphens, as the case cover
  stamps it (`227-2-1366`), the fund keeping its letter prefix in the form
  sibling Sources of that fund use (`Р8985-1-194`). Check a few Sources of the
  same fund (`repositoryId` + `sortBy=reference`) for the house form and the
  repository's `referenceCodeRegexRules` before writing.
- When a catalogue prints another form (`ф. 227, оп. 1 т. 2, спр. 1366`), keep
  the cover code as the primary link and add the catalogue form as a second,
  non-primary link in the same repository, its `note` quoting the printed
  citation.
- A link to an archive unit carries the unit's page on the archive's own site
  in `url`. Fill a missing URL on the existing link; never overwrite a
  different URL, never add a second link for the same unit.
- `referenceType` and `accessType` values are lower case (`archive-signature`,
  `dgs`, `call-number`, `other`; `physical`, `digital`, `hybrid`).
- Before adding or changing a code, look it up:
  `GET /api/sources/repository-links?repositoryId=…&referenceCode=…`. Updates
  have no duplicate check. If another Source already holds the code, do not
  change either: report the pair as a possible duplicate.

## Classification tags

- Read the tree once: `GET /api/tags/tree?entityType=source`. Select by stable
  `code`; use the UUID of that environment. A usable tag is active, selectable,
  applicable to `source` and not a facet root; at most 32 per Source.
- Add a tag only for what the material shows (a metrical book, a confession
  list, a revision tale). Type, repository, language, author and place have
  their own fields: never tag them.
- Remove a tag only when the material shows it is wrong.
- A concept missing from the taxonomy is a report item; tags cannot be created
  with a token.

## Title, descriptions and translations

- The original title and description stay in the language the Source prints
  them in, Russian included: a Russian original stays the original, never
  replaced by a translation. Members cannot move an original to another
  language; the API refuses it.
- You may add translations in other languages as `human` versions, Ukrainian
  and English first, when they are missing:

  ~~~json
  {
    "version": 7,
    "titleVersions": {
      "ru": { "text": "Метрическая книга …", "kind": "original" },
      "uk": { "text": "Метрична книга …", "kind": "human", "from": "ru" },
      "en": { "text": "Metrical book …", "kind": "human", "from": "ru" }
    }
  }
  ~~~

  Send every stored version back unchanged beside the new ones.
- Never create a Russian translation, and never derive a Russian form of a
  name. Names of people and places, archival references and quotations inside
  a translation stay as printed.
- A translation renders the stored original only: it adds no facts and is
  never evidence for another field. Add translations to Sources you are already
  reviewing; a missing translation alone does not put a Source in your queue.
- Correct a title only from the case cover or the archive's catalogue, keeping
  its wording; do not "improve" style.

## Authors

Change author credits only with clear evidence (a printed compiler, the parish
church that kept a register) and an existing Author
(`GET /api/authors?query=…`). Creating Authors needs `api:authors` and is
outside this workflow: report the missing Author.

## Read-back checklist

After each `PATCH`, `GET /api/sources/{id}` and check: the new `version`; every
field you sent; every stored item of each array you sent is still there; no
`canonicalPlaceId` was lost; `approvalStatus` (Pending after a change to an
Approved Source); and that no field holds anything but catalogue content.
