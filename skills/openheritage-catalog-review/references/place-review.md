# Reviewing a canonical place

A canonical place is OpenHeritage's gazetteer entry for a settlement or an
administrative, church or historical area, with its names over time, types,
parents, point, outline and external identifiers. Sources, photos and
researches link to it. Changing a place changes what every linked record shows,
so the bar is higher than for a Source.

## Find before anything

Name-based creation has no duplicate check, so search every way before deciding
a place is missing or wrong:

| GET | Use |
|---|---|
| `/api/canonical-places?query=…&date=YYYY-MM-DD&typeCode=…&skip=0&take=50` | names in every language; `date` resolves names, types and parents as of that day |
| `/api/canonical-places/by-external-identity?provider=wikidata&externalId=Q…` | `wikidata`, `katotth`, `koatuu`, `osm-node`, `osm-way`, `osm-relation`, `geonames` |
| `/api/canonical-places/nearby?latitude=…&longitude=…&radiusKm=…` | places near a point |
| `/api/canonical-places/at-point?latitude=…&longitude=…` | outlines containing a point, innermost first |
| `/api/canonical-places/{id}?date=YYYY-MM-DD` | one place, resolved for a date |
| `/api/canonical-places/{id}/children` | what lies under it |
| `/api/canonical-places/{id}/revisions` | who changed what; read before changing |
| `/api/place-types` | the type codes in use |
| `/api/osm/places?q=…&limit=10&language=uk` | OpenStreetMap settlements and areas, to create a missing place |

Places can also be searched anonymously through MCP (`search_places`,
`autocomplete_places`, `find_places_nearby`, `get_place`).

## Creating a missing place

Only from an OpenStreetMap pick: `POST /api/canonical-places/from-osm` with
`{"osmType": "node|way|relation", "osmId": 123}`. The server reads the element
itself, reuses a place that already carries that OSM id, accepts settlements
and administrative areas only, and creates it `Unverified`. Creation is rate
limited (about 30 an hour). A place OSM does not know (a vanished village, a
historical повіт) is not created by this workflow: keep the name on the Source
with `unresolved` and report it.

## Changing a place: PUT is the whole state

~~~bash
curl -sS "$BASE/api/canonical-places/$PLACE_ID" -H "$AUTH" -H "$UA" > place.json
# edit a copy, then:
curl -sS -X PUT "$BASE/api/canonical-places/$PLACE_ID" -H "$AUTH" -H "$UA" \
  -H "Content-Type: application/json" --data @place-update.json
~~~

- `version` is required; a stale one is 409.
- A collection you leave out or send as `null` (`names`, `typeAssignments`,
  `relations`, `externalIdentities`, `referenceLinks`, `notes`, `geometries`)
  is left alone. A collection you send is the **complete** list: items without
  `id` are added, items with a stored `id` are updated, and stored items whose
  `id` you leave out are **deleted**. So send only the collections you change,
  each with every stored item and its `id`.
- `point`, `existenceFrom`, `existenceUntil` are replaced when sent; clear them
  only with `clearPoint`, `clearExistenceFrom`, `clearExistenceUntil`, and only
  when the stored value is shown to be wrong.
- A member's change to a `Verified` place sets it to `Unverified` ("not
  reviewed yet") until a moderator verifies it again. Make such a change only
  on strong evidence, and list every such place in the report.
- Use exactly these values. An unknown name `kind` or `relationType` is
  refused with 422; an unknown `category` becomes `Other` and an unknown
  `confidence` is dropped, so check those two before sending.
  - name `kind`: `Official`, `Common`, `Historical`, `Exonym`, `Endonym`,
    `Church`, `Transliteration`, `SourceMention`, `Other`;
  - `relationType`: `AdministrativeParent`, `EcclesiasticalParent`,
    `GeographicParent`, `HistoricalParent`, `PoliticalSovereignty`,
    `MilitaryOccupation`, `CivilOccupation`, `ClaimedSovereignty`,
    `ContestedControl`, `Predecessor`, `Successor`, `Other`;
  - reference link `category`: `OfficialSite`, `SocialGroup`, `ArchiveCatalog`,
    `Article`, `Map`, `Tourism`, `ChurchSite`, `CemeterySite`, `CommunityWiki`,
    `Other`;
  - provenance `confidence`: `Definite`, `Probable`, `Possible`, `Speculative`.

~~~json
{
  "version": 12,
  "names": [
    { "id": "${STORED_NAME_ID}", "value": "Кропивницький", "languageCode": "uk",
      "kind": "Official", "isPreferred": true, "dateWindows": [{ "type": "after", "value": "2016-07-14" }] },
    { "value": "Єлисаветград", "languageCode": "uk", "kind": "Historical", "isPreferred": false,
      "dateWindows": [{ "type": "range", "value": "1784/1924" }],
      "provenance": { "citation": "${PUBLISHED_WORK_AND_PAGE}", "sourceUrl": "${PUBLISHED_URL}" } }
  ]
}
~~~

## Names

- Exactly one preferred name in the whole list; every name has a value and a
  language code.
- Add a historical name with the years it was used (`dateWindows`) and a
  citation of the published work or record it comes from. The citation names
  that work; it never says how you found it.
- Never derive or transliterate a form yourself, and never add a Russian form
  derived from another language. A Russian name is added only as `Historical`
  or `SourceMention` with a citation, exactly as a record writes it, and is
  never preferred.
- Do not rename a place to match a Source's spelling: the Source keeps its
  spelling in its own coverage `name`.

## Parents, types, points, identifiers

- Parents (`AdministrativeParent`, `EcclesiasticalParent`, …) carry the years
  they held. Before adding one, read the parent's own chain upward: the server
  rejects only a place that is its own parent, not longer cycles.
- Types come from `/api/place-types`; give a type the years it held when it
  changed (a village that became a town).
- Set or move a point only from the place's own outline, an authority record
  (Wikidata, KATOTTH, OSM) or a published map, with that source in the
  provenance; never from a Source's coverage or a guess.
- Add an external id only when the authority record clearly describes this
  place (name, location, type). The same id on two places means a duplicate:
  report it, do not move the id.

## Report, do not fix

Duplicates, wrong merges, a place that should be deleted, wrong verification,
and "Places to match" decisions are moderators' work. Report them to the member
with both place links and the evidence. A member may suggest a place for a
"Places to match" entry (`POST /api/unresolved-places/{id}/suggestions` with
`{"placeId": "…"}`, `note` left empty or a fact from the record) when the
member asked for it.
