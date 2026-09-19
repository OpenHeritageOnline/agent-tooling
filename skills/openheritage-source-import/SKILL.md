---
name: openheritage-source-import
description: Create and verify OpenHeritage Sources as catalog or repository-reference records, and optionally ingest SourceDocuments, original files, ordered page images, and PAGE XML. Use for authorized generic source imports with repository provenance, authors, classification tags, coverage dates, and places. Use openheritage-newspaper-import for complete newspaper issues.
metadata:
  version: 1.0.0
---

# OpenHeritage Source Import

Create durable provenance records without inventing unavailable evidence. A
Source is independently useful and does not require a SourceDocument.

Use a Source by itself as a catalog record, archival citation, bibliography
entry, repository reference, or description of known material whose digital
files are unavailable. `hasDocuments: false` is valid and does not make the
Source incomplete. Never create an empty placeholder SourceDocument. Add a
SourceDocument later only when a meaningful digital file, page set, structured
table, transcription, or external-only document representation is available.

Use `openheritage-newspaper-import` instead for complete newspaper issues,
publication-authority setup, automated year collections, and newspaper OCR.

## Authorization and live contracts

- Read the live Personal API at `$BASE/api-docs` and `$BASE/api/openapi/v1.json` before mutation. It is authoritative for request schemas, multipart fields, limits, and `x-api-required-scopes`.
- Source-only creation requires `api:sources`; document creation or upload also requires `api:documents`; creating or updating an Author additionally requires `api:authors`. Personal API tokens already include `api:read`.
- Send a token only as `Authorization: Bearer $OPENHERITAGE_API_TOKEN`. Never put it in a URL, file, log, checkpoint, or report, and never send it to MCP.
- Creating repositories, taxonomy tags, or canonical places is outside this workflow unless the user separately requests and authorizes it. Link existing records or retain conservative unresolved data.
- Confirm the target environment, visibility, provenance, rights, and intended record boundary immediately before the first mutation.

~~~bash
BASE="\${OPENHERITAGE_BASE_URL:-https://openheritage.online}"
~~~

## Workflow

1. Inventory the evidence and decide the Source boundary. Do not create one Source per scan when the scans are representations of one catalog unit.
2. Search for duplicate Sources by title, type, repository, reference code, origin date, and Author when known. Reuse one verified match; stop on multiple plausible matches.
3. Resolve repository links, external references, Authors, classification tags, languages, origin date, and coverage segments from evidence in the target environment.
4. Present the proposed Source and omitted unknown fields to the user when ambiguity would materially change the record.
5. Create the Source, then read it back and checkpoint its ID and version.
6. Stop successfully if no digital representation is available. Report that the Source is a catalog/reference record with no documents.
7. If a real document representation exists, create and populate one or more SourceDocuments according to their intellectual and digital boundaries.
8. Read back the Source, documents, files, pages, XML, and derived text that were actually created; deliver a verification report.

Before creating or updating a Source, read [references/source-model.md](references/source-model.md). Read [references/document-ingestion.md](references/document-ingestion.md) only when a SourceDocument or digital content is part of the requested import.

## Source and document boundaries

- A **Source** is the catalog and provenance unit: an archival case, book, publication, collection, webpage, or other cited body of material.
- A **SourceDocument** is an optional digital document beneath a Source. It carries document-specific metadata, rights, files, pages, XML, structured entries, and transcriptions.
- One Source may have no documents, one document, or several documents. Split documents only when the digital objects or intellectual parts need independent titles, rights, visibility, page order, or processing.
- Do not upload a file merely to make a Source appear complete. Do not create a SourceDocument whose only content is a promise that files may arrive later.

## Evidence rules

- Repository links identify where a physical or digital representation is held. Repository reference codes are scoped to that repository, never globally unique by assumption.
- External reference links provide contextual or catalog URLs. They do not prove custody and do not replace a repository link.
- Authors are reusable person or organization authority records. Credit only evidenced creators or contributors, using supported roles and `creditedAs` for the printed byline or imprint.
- Classification tags describe evidenced Source categories. Select only active, selectable tags applicable to Sources; never use a facet root or an environment-specific ID copied from an example.
- `originDate` is when the Source itself was created or published. Coverage date windows and places describe what its contents cover. Do not substitute one for the other.
- Preserve an unresolved historical place name when no single canonical place is proven. Never choose among ambiguous places or infer coordinates.

## Checkpoints and safe retries

- Keep a manifest outside the source material containing input hashes, resolved IDs, request identity, returned Source/document versions, uploaded asset IDs, page keys, and the next intended action. Never store secrets in it.
- Keep one mutation in flight. After an unknown outcome, read current state and compare IDs, versions, filenames, sizes, and hashes before retrying.
- Fetch before PUT or PATCH, include the current version field where supported, and preserve every unrelated field.
- Stop and reconcile on 409. Correct the request on 422; do not retry it unchanged. Stop on 401 or 403 and request the missing authorization.
- Do not delete or replace an existing representation merely to repeat an import. Upload a new version only when the API models versioning and the user requested the change.

## Rate limits and request pacing

- Keep one import request in flight and use the narrowest discovery query. Do not enumerate repositories, Authors, tags, places, Sources, or documents in bulk.
- On 429, stop issuing calls and honor `Retry-After` or the server-provided reset. Otherwise use bounded full-jitter backoff and make at most three read retries.
- Retry a mutation after 429 only when it has a stable operation or upload-session identity and current state proves it was not applied; never retry an unkeyed mutation.

## Completion report

Report created and reused IDs, the Source version and visibility, repository and
reference decisions, Authors and roles, classification tag codes, origin and
coverage interpretation, languages, omitted unknowns, and verification results.
State explicitly whether the result is:

- a complete catalog/reference Source with no SourceDocuments; or
- a Source with verified SourceDocuments and the uploaded or external digital representations.
