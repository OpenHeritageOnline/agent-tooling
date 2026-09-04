# PAGE XML generation and repair

Read this reference whenever newspaper OCR will be generated, uploaded, or repaired.

## Required representation

- Generate PAGE XML namespace/schema `2019-07-15`.
- Set `Page.imageFilename`, `imageWidth`, and `imageHeight` to the normalized preservation image.
- Use OCR languages appropriate to the content; mixed Ukrainian/Russian newspapers commonly require `ukr+rus`.
- Record the OCR engine/version, languages, page segmentation mode, and confidence threshold in PAGE metadata.
- Represent detected regions, lines, and words with coordinates scaled to the normalized full-resolution image.
- Filter implausible or low-confidence words according to the recorded threshold, while retaining a non-empty readable projection.
- Add reading order when region order is known.

## Tesseract TSV is not quoted CSV

Tesseract's TSV output is tab-delimited raw text. OCR text may contain a literal double quote. Do not let an RFC-style CSV parser treat that quote as the start of a quoted multiline field: it can swallow later TSV rows and embed them inside a PAGE `<Unicode>` value.

With Python's `csv` module, disable quoting explicitly:

~~~python
csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE)
~~~

Reject generated XML when any `<Unicode>` value contains either:

- the Tesseract header `level, page_num, block_num, …` separated by tabs; or
- a 12-column Tesseract data row beginning with level `1`–`5` and numeric geometry/confidence fields.

Run the bundled validator against every generated file:

~~~bash
python3 scripts/validate_page_xml.py path/to/xml-or-directory
~~~

Schema validation is still required when the PAGE XSD is locally available:

~~~bash
xmllint --noout --schema pagecontent-2019-07-15.xsd page.xml
~~~

## Large-batch gate

Before a batch upload:

1. Validate every XML offline.
2. Upload one representative page to the target environment.
3. Read the page DTO and downloaded XML back.
4. Confirm the server accepted the schema, parsed non-empty OCR, retained the expected coordinates, and reports no TSV contamination.
5. Only then continue sequentially with checkpoints.

## Repairing already uploaded XML

Prefer faithful regeneration from the preserved OCR TSV or rerun OCR using the recorded settings. Do not merely delete arbitrary lines unless regeneration is impossible and the remaining transcription has been evaluated for completeness.

For a safe repair:

- identify only contaminated current XML versions;
- capture the current image and XML version IDs as preconditions;
- regenerate and validate a separate XML file;
- re-fetch the page immediately before mutation;
- upload the repaired XML as a new version;
- confirm the image version did not change;
- download the new current XML and compare its SHA-256;
- verify the parsed full text has no TSV signature;
- checkpoint old/new XML version IDs after every success.

Leave already clean XML versions untouched. On a version mismatch, stop and reconcile instead of overwriting a concurrent edit.
