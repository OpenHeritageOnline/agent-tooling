# OpenHeritage SourceDocument ingestion

Read this reference only when the requested import includes a meaningful
digital or external-only document representation. A catalog/reference Source
without documents is already a valid completed outcome.

## Decide whether to create a document

Create a SourceDocument when at least one of these exists:

- an original digital file to preserve;
- an ordered set of page images;
- PAGE XML, transcription, or structured entries tied to those pages;
- a meaningful external-only representation with evidenced rights metadata; or
- a distinct digital part that needs its own title, rights, visibility, or processing.

Do not create an empty placeholder document. Do not create one document per
page or scan unless each is genuinely an independent document. A Source may
receive documents later without changing its citation identity.

## Document metadata and rights

Current document types include `GenericDocument`, `CaseFile`, `Book`,
`Register`, `Directory`, `Index`, `Spreadsheet`, and `Table`. Select the closest
live value supported by the material; do not infer a specialized type merely
from a filename.

Create with `POST /api/sources/{sourceId}/documents` and `api:documents`:

~~~json
{
  "title": "${DOCUMENT_TITLE}",
  "description": "${DIGITAL_REPRESENTATION_AND_COMPLETENESS}",
  "documentType": "CaseFile",
  "visibility": "public",
  "rights": {
    "declarationType": "OpenLicenseOrPublicDomain",
    "sourceReference": "${EVIDENCE_FOR_DECLARATION}",
    "uploaderConfirmedResponsibility": true,
    "originalUrl": "${ORIGINAL_URL}",
    "authorOrRepository": "${RIGHTS_HOLDER_OR_REPOSITORY}",
    "licenseLabel": "${VERIFIED_LICENSE}",
    "rightsNote": "${FACTUAL_NOTE}"
  }
}
~~~

Include rights values only after the user confirms them or supplies evidence.
Supported declaration types currently include `OwnWork`, `PermissionGranted`,
`OpenLicenseOrPublicDomain`, and `ExternalLinkOnly`; verify the live schema.
Document visibility cannot be more public than its parent Source. Do not claim
public-domain or license status from age alone.

For an external-only representation, record the supported external URL and
rights/visibility mode from the live contract. Do not download or rehost files
when the evidence or permission supports linking only.

## Original files and page representations

An original asset preserves the supplied document-level file, such as a PDF,
TIFF, spreadsheet, or archive. Page images support ordered viewing and
page-level XML, metadata, or transcription. They serve different purposes and
may coexist.

- Upload a document original through `/api/sources/{sourceId}/documents/{documentId}/files` when its size and type fit the live direct-upload contract.
- For large content, use a chunked upload only when the operation is present in the live Personal API for the caller. Never invent or call an unpublished session endpoint with a Personal API token.
- Hash every local input before upload. After upload, verify filename, MIME type, byte length, asset ID, and downloadable bytes or hash when available.
- Preserve originals. Normalize derivative page images separately and record the transformation.

## Ordered pages

Use stable page keys such as `001`, `002`, … in intended display order. Retain
covers, blank pages, inserts, and duplicates when they are part of the object;
record exclusions explicitly rather than silently renumbering evidence.

For each page:

1. Upload the image to `/pages/{pageKey}/image` using the multipart fields from the live schema.
2. Set localized page metadata only when evidenced.
3. Upload PAGE XML to `/pages/{pageKey}/xml` only after offline validation.
4. Checkpoint the page key, returned page ID, image/XML version IDs, sizes, and hashes.

After all pages are present, list them and reorder only when the returned order
differs from the complete intended key list. Never bulk-delete or replace pages
as part of an ordinary retry.

## PAGE XML and derived text

Use the schema version accepted by the live endpoint. Coordinates must match
the uploaded image dimensions and remain within page bounds. Preserve Unicode,
reading order, region/line/word structure, and source-language text. Tesseract
TSV or plain text is not PAGE XML.

Before a large batch, upload one representative image/XML pair and verify:

- schema acceptance and version;
- image dimensions and coordinate bounds;
- parsed transcription text and reading order;
- correct page association; and
- absence of TSV headers or other conversion artifacts.

If PAGE XML is unavailable, page images alone are valid. Do not generate empty
XML merely to mark OCR as complete. Structured entries or manual transcriptions
are separate representations and should be added only when requested and
supported by the live Personal API.

## Resume and verification

Checkpoint after document creation and every successful upload. On restart:

1. Read the current SourceDocument and page list.
2. Match originals by asset ID plus filename, size, and hash where available.
3. Match pages by stable page key and current representation metadata.
4. Resume from the first absent or unverified item.
5. Stop on conflicting content instead of overwriting it.

For updates, fetch the document and include `currentVersion` where supported.
On 409, reload and reconcile. On 422, correct the payload. On 429, honor
`Retry-After`; retry a mutation only when stable upload/session identity and a
state read prove it was not already applied.

Finish by verifying the Source-to-document relationship, document type,
visibility, rights, original assets, page count/order, images, XML, and parsed
text. Report missing representations honestly. A document import can be
complete without OCR, and a Source import can be complete without any document.
