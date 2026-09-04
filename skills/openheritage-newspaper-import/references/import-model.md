# Newspaper import model

Read this reference before cataloguing a complete newspaper issue or making any
OpenHeritage import mutation. The JSON bodies are templates: replace every
`${...}` value with data resolved in the target environment, and re-check the
live OpenAPI document before sending them.

## Stable relationships

The import creates or reuses this graph:

~~~text
Organization Author
  -> imported root Collection automation (SourceAuthor + OriginDate year)
  -> issue Source (publication + institutional-creator credit)
       -> GenericDocument
            -> ordered page image versions
            -> PAGE XML versions
~~~

The root Collection owns the automation rule. Its year and fallback children
are system-generated and receive matching Sources asynchronously.

## Organization Author

Search `GET /api/authors?query=...&kind=organization`. Normalize whitespace and
case, compare preferred names and aliases, and use a place qualifier when it
distinguishes newspapers with the same title. Reuse one clear match; stop on
multiple plausible matches. Create with `POST /api/authors` only when none
exists and the caller authorized it.

~~~json
{
  "kind": "organization",
  "preferredNames": [
    { "language": "uk", "value": "Газета «Назва» (Місце)" }
  ],
  "aliases": [
    { "language": "uk", "value": "Назва" }
  ],
  "biography": {
    "uk": "Фактичний опис видавця, органу-засновника та місця видання."
  },
  "links": []
}
~~~

Add `establishedDate` or `dissolvedDate` only when supported by evidence; use
the live `DateExpressionDto` shape. Before `PUT /api/authors/{id}`, fetch the
Author and include `currentVersion` while preserving every unrelated field.

## Imported Collection with Author/year automation

Search owned/imported collections using the localized title, then compare the
stable `origin.reference` and automation Author ID. Reuse one exact match; stop
on conflicts. A new collection uses `POST /api/collections` with `api:sources`:

~~~json
{
  "title": {
    "uk": "Випуски газети «Назва» (Місце)"
  },
  "description": [
    {
      "lang": "uk",
      "text": "Оцифровані випуски газети з перевіреної фізичної підшивки.",
      "format": "plainText"
    }
  ],
  "descriptionFormat": "plainText",
  "visibility": "public",
  "origin": {
    "type": "imported",
    "label": "OpenHeritage newspaper import",
    "reference": "${STABLE_SERIES_IMPORT_MARKER}"
  },
  "automation": {
    "isActive": true,
    "criteriaMatchMode": "all",
    "criteria": [
      {
        "kind": "sourceAuthor",
        "authorId": "${AUTHOR_ID}"
      }
    ],
    "grouping": {
      "kind": "dateHierarchy",
      "dateSource": "originDate",
      "granularity": "year",
      "nonExactBucket": {
        "key": "not-exact-year",
        "title": {
          "uk": "Неточний або невідомий рік",
          "en": "Non-exact or unknown year"
        }
      }
    }
  }
}
~~~

Only exact `yyyy`, `yyyy-MM`, or `yyyy-MM-dd` origin dates qualify for a year
child. Approximate, before, after, range, missing, or invalid dates go to the
fallback child. Do not send deprecated flattened automation fields. Before
`PUT /api/collections/{id}`, fetch the collection, include `version`, and
preserve unrelated fields.

Automation is asynchronous. Poll `GET /api/collections/{id}/children`, then
`GET /api/collections/{childId}/sources`, with bounded waits. The root can have
zero direct Sources even while generated children contain all issues. Never
manually link an issue to a generated child.

## Classification, repository, and publication place

Resolve the active selectable Source taxonomy tag whose stable code is
`record-kind-newspaper`; retain its environment-specific ID. Never assign a
facet root, inactive tag, or ID copied from an example.

When the holding repository is known, search `/api/repositories/selectable`,
verify the exact institution, and add one primary physical representation:

~~~json
{
  "repositoryId": "${REPOSITORY_ID}",
  "url": null,
  "note": null,
  "referenceCode": null,
  "referenceType": null,
  "accessType": "physical",
  "isPrimaryRepresentation": true,
  "enforceUniqueReferenceCode": false
}
~~~

Use a real URL or reference code only when supplied or verified. If no holding
repository is known, send no repository link and report the omission.

Represent publication place and area of coverage in a coverage segment. Search
canonical places and select one automatically only when the complete result has
exactly one active, exact-name match. Copy its ID, display name, and point:

~~~json
{
  "canonicalPlaceId": "${CANONICAL_PLACE_ID}",
  "name": "${CANONICAL_PLACE_NAME}",
  "geoJsonPoint": {
    "type": "Point",
    "coordinates": [28.4682, 49.2331]
  }
}
~~~

The coordinate order is `[longitude, latitude]`; the numeric pair above is
illustrative and must be replaced. If no canonical match exists but a supplied
name and point are reliable, omit `canonicalPlaceId` and retain the name and
point. If only a name is known, omit both `canonicalPlaceId` and
`geoJsonPoint`. If the place is unknown, use an empty `locations` array rather
than guessing.

## Issue Source

Search before creation using normalized title, printed number, origin date,
Author ID, and repository when available. Reuse one exact match; stop on
multiple matches. Preserve combined issue numbers as printed and say
`[номер не читається]` rather than reconstructing an unreadable number.

Create with `POST /api/sources` and `api:sources`:

~~~json
{
  "type": "publication",
  "visibility": "public",
  "title": "Газета «Назва» (Місце). № 42 від 17 травня 1932 р.",
  "descriptions": [
    {
      "language": "uk",
      "text": "Випуск із фізичної підшивки, використаної для оцифрування."
    }
  ],
  "repositoryLinks": [
    {
      "repositoryId": "${REPOSITORY_ID}",
      "url": null,
      "note": null,
      "referenceCode": null,
      "referenceType": null,
      "accessType": "physical",
      "isPrimaryRepresentation": true,
      "enforceUniqueReferenceCode": false
    }
  ],
  "referenceLinks": [],
  "coverageSegments": [
    {
      "dateWindows": [
        { "type": "exact", "value": "1932-05-17" }
      ],
      "locations": [
        {
          "canonicalPlaceId": "${CANONICAL_PLACE_ID}",
          "name": "${CANONICAL_PLACE_NAME}",
          "geoJsonPoint": {
            "type": "Point",
            "coordinates": [28.4682, 49.2331]
          }
        }
      ],
      "scopeNote": "Місце видання та район висвітлення"
    }
  ],
  "originDate": { "type": "exact", "value": "1932-05-17" },
  "languages": ["uk"],
  "classificationTagIds": ["${NEWSPAPER_TAG_ID}"],
  "authorCredits": [
    {
      "authorId": "${AUTHOR_ID}",
      "roles": ["institutional-creator"],
      "creditedAs": "Назва"
    }
  ]
}
~~~

The coverage date normally repeats the issue origin date. When the masthead
does not support an exact date, do not invent one: use the supported non-exact
date expression or omit it, adjust the title honestly, and expect the
Collection fallback bucket. Before a Source update, fetch it, include its
`version`, and preserve descriptions, links, coverage, language,
classifications, and credits outside the requested change.

## Document and pages

Create one `GenericDocument` beneath the issue Source with
`POST /api/sources/{sourceId}/documents` and `api:documents`:

~~~json
{
  "title": "Газета «Назва» (Місце). № 42 від 17 травня 1932 р.",
  "description": "OpenHeritage newspaper import: ${STABLE_ISSUE_IMPORT_MARKER}",
  "documentType": "GenericDocument",
  "visibility": "public"
}
~~~

Add the `rights` object only after the caller confirms the declaration, source,
license label, and uploader responsibility; follow the live schema rather than
inventing legal facts.

For each page key in display order:

1. Upload the image to `/pages/{pageKey}/image` as multipart fields `file` and optional `qualityNote`, or complete a caller-owned chunked upload session at `/image/complete`.
2. Set metadata with `PUT /pages/{pageKey}/metadata`; titles are localized `{lang,text}` values, descriptions are `{lang,text,format}`, and reference links must be evidenced.
3. Upload validated PAGE XML to `/pages/{pageKey}/xml` as multipart fields `file` and `schemaVersion=2019-07-15`, or complete a chunked session at `/xml/complete`.
4. Checkpoint the page ID/key plus current image and XML version IDs and hashes.

After all uploads, list pages and call `/pages/reorder` only if the returned
order differs from the complete intended key list. Read each image and XML back,
verify bytes and metadata, and read `/xml/transcription` to confirm non-empty
parsed text and no Tesseract TSV signature.
