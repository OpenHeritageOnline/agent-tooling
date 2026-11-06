# OpenHeritage Source model

Read this reference before creating or updating a generic Source. Request
examples are templates: resolve every identifier in the target environment and
check the live Personal API schema before sending them.

## Source-only records are complete records

A Source catalogs and cites material independently of digitization. Create a
Source without a SourceDocument when the available evidence establishes the
catalog unit but no usable digital representation exists. Common examples are:

- an archival case known from a finding aid but not digitized;
- a book or periodical issue known from a bibliography or library catalog;
- a repository reference supplied for future on-site research;
- a physical collection whose contents are described but not scanned; or
- a known webpage or external resource that should be cited without copying it.

After creation, `hasDocuments: false` is expected. Do not create a placeholder
document, upload a blank file, or imply that OpenHeritage holds a scan. A later
authorized workflow can add SourceDocuments without replacing the Source.

## Establish the Source boundary

Prefer the smallest stable catalog unit that can be cited and described without
losing provenance. An archival case is normally one Source; its individual
scans are pages or files of a SourceDocument, not separate Sources. A book is
normally one Source even when digitized in several files. Split Sources when
the repository catalog, title, origin, custody, or citation identity genuinely
changes.

Allowed Source types currently include `book`, `publication`, `collection`,
`other`, `archive-case`, `webpage`, and `personal-collection`. Confirm the live
schema because availability and permissions may differ by environment.

## Duplicate search

Before POST, search `GET /api/sources` with the narrowest useful title query and
compare complete candidates. When a repository reference exists, also query
`GET /api/sources/repository-links` with `repositoryId`, `referenceCode`, URL,
or `referenceType` as appropriate. Repeat `referenceCode` (up to 100) to check a
batch in one request: any listed code matches, and `limit` (1-100, default 20)
applies to each code. Codes match exactly and case-sensitively.

Compare:

- normalized title and Source type;
- repository ID plus reference code and URL;
- origin date and coverage;
- credited Author IDs and roles;
- languages and classification tag codes; and
- existing documents or external links.

Reuse one clear match. Stop on multiple plausible matches. A similar title in a
different repository or a matching bare archival call number is not proof of a
duplicate.

## Repository links and external references

Search `GET /api/repositories/selectable?query=...`, then verify the exact
institution, branch, type, and location. Do not create a repository merely to
finish an import.

A repository link represents a held physical or digital representation:

~~~json
{
  "repositoryId": "${REPOSITORY_ID}",
  "url": "${VERIFIED_ITEM_URL}",
  "note": "${EVIDENCED_NOTE}",
  "referenceCode": "${REPOSITORY_SCOPED_CODE}",
  "referenceType": "archive-signature",
  "accessType": "digital",
  "isPrimaryRepresentation": true,
  "enforceUniqueReferenceCode": true
}
~~~

- `referenceCode` is meaningful only with its repository. Preserve the official formatting and satisfy that repository's regex rules.
- Use `archive-signature` for archival hierarchy codes, `dgs` for a FamilySearch DGS number, `call-number` for library or storage call numbers, or `other` only when evidence does not fit a more specific live option.
- Use `physical`, `digital`, or `hybrid` for access according to the representation actually held.
- Mark the best representation as primary; do not mark several links primary without a real reason.
- Set `enforceUniqueReferenceCode` only when the selected repository treats that code as unique. The check runs on create only and compares the code exactly (case-sensitive) within that repository. A duplicate answers 409 with `code: duplicate_reference_code` and, when you may see the existing source, its id in `existingSourceId`; review that source instead of retrying with uniqueness disabled.
- A repository may restrict allowed URL hosts. Use the item URL on the repository's verified host, not an unrelated mirror or search-result URL.

If the holding repository is unknown, omit `repositoryLinks` and report the
omission. Put independent catalog pages, finding aids, citations, or related
resources in `referenceLinks`:

~~~json
{
  "url": "https://example.org/catalog/item",
  "label": "Catalog record",
  "note": "Describes the cited edition"
}
~~~

Reference links provide context; they do not assert custody.

## Authors and credits

An Author is a canonical authority record for a person or organization, not the
uploader and not automatically the holding repository.

1. Search `GET /api/authors?query=...` and filter by `kind=person` or
   `kind=organization` when known.
2. Compare preferred names, aliases, dates, locations, and existing credits.
3. Reuse one clear active match. Stop on multiple plausible matches.
4. Create an Author only when none exists, the evidence is sufficient, the user
   authorized it, and the token has `api:authors`.

Supported Source credit roles are `author`, `editor`, `compiler`, `translator`,
`cartographer`, `photographer`, `studio`, `collector`, `digitised-by`,
`publisher`, and `institutional-creator`. Use the smallest
evidenced set. `creditedAs` preserves the name or wording printed on the item;
it does not replace the canonical Author name.

~~~json
{
  "authorId": "${AUTHOR_ID}",
  "roles": ["compiler"],
  "creditedAs": "І. Петренко"
}
~~~

Omit an unknown Author rather than creating “Unknown,” crediting a repository,
or guessing from ownership. Creating or editing an Author's own classification
tags and life dates is separate from crediting that Author on a Source.

## Source classification tags

Read `GET /api/tags?entityType=source`. Traverse the returned tree and select by
stable `code`, then retain the target environment's UUID. A valid Source tag is
active, selectable, applicable to `source`, and not a facet root. Use only tags
supported by the material; Source type, repository, language, Author, and place
already have dedicated fields. At most 32 distinct non-empty IDs are accepted.

Do not create or reactivate taxonomy tags during an ordinary import. If the
needed concept is absent, omit it and report the taxonomy gap.

## Origin date and coverage

`originDate` answers when this Source itself was created, issued, or published.
Coverage answers which dates and places the Source content concerns.

Date expressions use `{ "type", "value" }`:

- `exact`: `1897`, `1897-04`, or `1897-04-23`;
- `approximate`: the same date forms when explicitly approximate;
- `before` or `after`: one supported date token; or
- `range`: two supported tokens separated by `/` or an en dash, such as `1897/1902`.

Never turn a catalog date range into an exact date. Omit a date when the
evidence does not justify even an approximate or bounded expression.

A coverage segment groups date windows and locations that apply together:

~~~json
{
  "dateWindows": [
    { "type": "range", "value": "1897/1902" }
  ],
  "locations": [
    {
      "canonicalPlaceId": "${PLACE_ID}",
      "name": "${EVIDENCED_HISTORICAL_NAME}",
      "geoJsonPoint": {
        "type": "Point",
        "coordinates": [30.5234, 50.4501]
      }
    }
  ],
  "scopeNote": "Parish registers represented by this Source"
}
~~~

Search canonical places with the relevant historical date. Select one
automatically only when there is exactly one active result whose identity and
name match the evidence. Coordinates are `[longitude, latitude]`.

If no canonical match is proven, retain an evidenced place `name`; include a
point only when reliable and omit `canonicalPlaceId`. If no place is known, use
an empty locations array. Use separate segments when different date windows
apply to different places. Do not flatten uncertain relationships into one
segment.

## Languages and descriptions

Use normalized language tags for languages materially present in the Source.
Descriptions are localized `{language,text}` values and should state factual
provenance, completeness, gaps, and catalog context. Do not put passwords,
tokens, private contact data, or unsupported conclusions in descriptions.

## Language versions of the title and descriptions

The title and descriptions each come twice: `title` (the original title's text)
and `descriptions` (`{language,text}` of the original and human versions), and
`titleVersions` and `descriptionVersions` with every version and its kind —
`{ "uk": { "text": "…", "kind": "original" }, "en": { "text": "…", "kind": "human", "from": "uk" } }`.
Tags are any well-formed BCP 47 tag (`uk`, `pl`, `la`, `yi-Latn`, `x-ruthen`),
returned in canonical case. Exactly one version is the original. `inferred: true`
marks a language guessed for a title or description saved before versions
existed: the title's is the Source's first `languages` entry, else `uk`.
Editing that text under the same language keeps the guess (`by` names the
editor); moving the original to another language, or sending
`"inferred": false` on it, states the language. Send `false` only when the
language is actually known.
`kind: machine` marks an unreviewed machine translation; never present it as a
person's translation.

To write languages explicitly, send `titleVersions` and `descriptionVersions`
(they win over `title` and `descriptions`; `title` may then be empty). Send only
`text`, `kind` (`original` or `human`), optionally `from`, and `inferred: false`
to confirm a guessed language; the server records who wrote each version. Rules: exactly one original per text; the API accepts Russian
(`ru` and its variants) as the original, as written in the source, or as a human
version beside another original (the interface and machine translation never
create Russian translations); only moderators move an original that is settled. Names of people,
places, archival references and quotations are written as printed, never
translated.

Sending only the older fields keeps working: a `title` that differs from what is
stored replaces the original title's text and keeps its translations (a title
sent back unchanged changes nothing); `descriptions` keeps the original of a
language still sent and replaces the set of languages. On `PUT`, leaving
`titleVersions` or `descriptionVersions` out (or null) keeps the stored
versions.

## Source creation template

Omit unresolved optional values instead of copying placeholders:

~~~json
{
  "type": "archive-case",
  "visibility": "public",
  "title": "${CATALOG_TITLE}",
  "descriptions": [
    {
      "language": "uk",
      "text": "${FACTUAL_PROVENANCE_AND_SCOPE}"
    }
  ],
  "repositoryLinks": [
    {
      "repositoryId": "${REPOSITORY_ID}",
      "url": null,
      "note": null,
      "referenceCode": "${REFERENCE_CODE}",
      "referenceType": "archive-signature",
      "accessType": "physical",
      "isPrimaryRepresentation": true,
      "enforceUniqueReferenceCode": true
    }
  ],
  "referenceLinks": [],
  "coverageSegments": [],
  "originDate": null,
  "languages": ["uk"],
  "classificationTagIds": ["${TAG_ID}"],
  "authorCredits": []
}
~~~

Create with `POST /api/sources`. Read `GET /api/sources/{id}` afterward and
verify every resolved relationship. An empty `documents` array and
`hasDocuments: false` are a successful Source-only result.

To change an existing Source, use `PATCH /api/sources/{id}` with the `version`
you read and only the fields to change, e.g. `{"version": 4, "title": "…"}`.
Everything left out keeps what is stored; an array you send replaces that set
(`[]` clears it). A stale `version` is 409: re-read and reapply.

`PUT /api/sources/{id}` replaces the whole Source. Left out on `PUT`,
`repositoryLinks`, `referenceLinks`, `coverageSegments` and `descriptions` are
cleared, `visibility` becomes `public`, and a missing `version` skips the
concurrency check; omitted `titleVersions`, `descriptionVersions`, `languages`,
`classificationTagIds`, `authorCredits` and `originDate` keep what is stored.
Use `PUT` only when you mean to send the complete Source.

Edits and review: the creator and source moderators may edit a Source in any
status; other accounts a `public` `archive-case` Source that is `Pending` or
`Approved` (not `Rejected`), without changing type or visibility. A Personal
API token always edits as a plain member, even when its owner moderates. When an account that cannot approve sources
changes an `Approved` or `Rejected` Source, it goes back to `Pending` for review.
A request that changes nothing saves nothing (no new `version`).
