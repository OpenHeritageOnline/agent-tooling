#!/usr/bin/env python3
"""Validate PAGE 2019-07-15 structure, coordinates, and TSV cleanliness."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
TSV_HEADER = "\t".join(
    (
        "level", "page_num", "block_num", "par_num", "line_num", "word_num",
        "left", "top", "width", "height", "conf", "text",
    )
)
TSV_ROW = re.compile(
    r"(?m)(?<!\S)[1-5]\t-?\d+\t-?\d+\t-?\d+\t-?\d+\t-?\d+"
    r"\t-?\d+\t-?\d+\t-?\d+\t-?\d+\t-?(?:\d+(?:\.\d*)?|\.\d+)"
    r"(?:\t[^\r\n]*)?(?=\r?$)"
)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def iter_inputs(values: list[str]) -> list[Path]:
    files: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.xml")))
        elif path.is_file():
            files.append(path)
        else:
            raise ValueError(f"Input does not exist: {path}")
    unique = []
    seen = set()
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def validate(path: Path) -> dict:
    errors: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        return {"path": str(path), "valid": False, "errors": [f"invalid XML: {error}"]}

    if root.tag != f"{{{PAGE_NS}}}PcGts":
        errors.append("root is not PAGE 2019-07-15 PcGts")
    page = next((node for node in root.iter() if local_name(node.tag) == "Page"), None)
    if page is None:
        errors.append("missing Page element")
        return {"path": str(path), "valid": False, "errors": errors}
    try:
        width = int(page.attrib["imageWidth"])
        height = int(page.attrib["imageHeight"])
        if width <= 0 or height <= 0:
            raise ValueError
    except (KeyError, ValueError):
        errors.append("invalid Page imageWidth/imageHeight")
        width = height = 0
    if not page.attrib.get("imageFilename"):
        errors.append("missing Page imageFilename")

    regions = [node for node in page.iter() if local_name(node.tag) == "TextRegion"]
    unicode_nodes = [node for node in page.iter() if local_name(node.tag) == "Unicode"]
    if not regions:
        errors.append("no TextRegion elements")
    if not any((node.text or "").strip() for node in unicode_nodes):
        errors.append("no non-empty Unicode text")
    unicode_text = "\n".join(node.text or "" for node in unicode_nodes)
    if TSV_HEADER.casefold() in unicode_text.casefold() or TSV_ROW.search(unicode_text):
        errors.append("embedded Tesseract TSV detected in Unicode text")

    ids = [node.attrib["id"] for node in page.iter() if node.attrib.get("id")]
    if len(ids) != len(set(ids)):
        errors.append("duplicate element IDs")
    for coords in (node for node in page.iter() if local_name(node.tag) == "Coords"):
        points = coords.attrib.get("points", "").split()
        if not points:
            errors.append("Coords element has no points")
            continue
        for point in points:
            try:
                x_text, y_text = point.split(",", 1)
                x, y = float(x_text), float(y_text)
            except ValueError:
                errors.append(f"invalid coordinate: {point}")
                continue
            if width and height and not (0 <= x <= width and 0 <= y <= height):
                errors.append(f"coordinate outside image bounds: {point}")

    return {
        "path": str(path),
        "valid": not errors,
        "imageWidth": width,
        "imageHeight": height,
        "regions": len(regions),
        "unicodeNodes": len(unicode_nodes),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="PAGE XML files or directories")
    parser.add_argument("--json", action="store_true", help="emit full JSON results")
    args = parser.parse_args()
    try:
        files = iter_inputs(args.inputs)
    except ValueError as error:
        parser.error(str(error))
    if not files:
        parser.error("no XML files found")
    results = [validate(path) for path in files]
    failures = [result for result in results if not result["valid"]]
    if args.json:
        print(json.dumps({"files": len(results), "failures": failures}, ensure_ascii=False, indent=2))
    else:
        for failure in failures:
            print(f"FAIL {failure['path']}: {'; '.join(failure['errors'])}", file=sys.stderr)
        print(f"PAGE XML: {len(results) - len(failures)}/{len(results)} valid")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
