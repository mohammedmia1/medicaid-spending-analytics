"""Stream cached XLSX values without opening million-row workbooks in memory."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def column_index(reference: str) -> int:
    """Convert Excel's letter column to a zero-based position."""
    result = 0
    for char in reference:
        if not char.isalpha():
            break
        result = result * 26 + ord(char.upper()) - ord("A") + 1
    return result - 1


def extract_sheet(workbook: Path, sheet_name: str, destination: Path) -> dict:
    """Export stored cell values, preserving strings, blanks and Excel errors.

    This reads cached formula results; it does not recalculate formulas.
    Source row positions are retained as `source_row` for traceability.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(workbook) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            with archive.open("xl/sharedStrings.xml") as stream:
                for _, element in etree.iterparse(stream, events=("end",), tag=NS + "si"):
                    strings.append("".join(element.itertext()))
                    element.clear()
                    while element.getprevious() is not None:
                        del element.getparent()[0]
        relationships = etree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {x.get("Id"): x.get("Target") for x in relationships}
        book = etree.fromstring(archive.read("xl/workbook.xml"))
        sheet = next(x for x in book.find(NS + "sheets") if x.get("name") == sheet_name)
        rid = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = targets[rid]
        member = target.lstrip("/") if target.startswith("/") else "xl/" + target
        count = 0
        last_row = 0
        error_cells = 0
        with archive.open(member) as stream, gzip.open(destination, "wt", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)
            header = None
            for _, row in etree.iterparse(stream, events=("end",), tag=NS + "row"):
                values = {}
                for cell in row:
                    if cell.tag != NS + "c":
                        continue
                    value = cell.findtext(NS + "v", default="")
                    kind = cell.get("t")
                    if kind == "s" and value:
                        value = strings[int(value)]
                    elif kind == "inlineStr":
                        value = "".join(cell.find(NS + "is").itertext())
                    elif kind == "e":
                        error_cells += 1
                    values[column_index(cell.get("r"))] = value
                number = int(row.get("r"))
                if header is None:
                    width = max(values) + 1
                    header = [values.get(i, "") for i in range(width)]
                    # Preserve duplicate headers with explicit suffixes.
                    seen = {}
                    for i, name in enumerate(header):
                        seen[name] = seen.get(name, 0) + 1
                        if seen[name] > 1:
                            header[i] = f"{name}__{seen[name]}"
                    writer.writerow(["source_row"] + header)
                elif any(values.values()):
                    writer.writerow([number] + [values.get(i, "") for i in range(len(header))])
                    count += 1
                    last_row = number
                row.clear()
                while row.getprevious() is not None:
                    del row.getparent()[0]
    return {"workbook": workbook.name, "sheet": sheet_name, "records": count,
            "last_populated_row": last_row, "error_cells": error_cells,
            "excel_row_limit_reached": last_row == 1048576, "output": destination.name}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    tasks = [
        ("(FINAL) FINAL CIS450 MEDICAID (1).xlsx", "STATE (cleaned ndc)", "utilization.csv.gz"),
        ("(FINAL) FINAL CIS450 MEDICAID (1).xlsx", "NDC Directory (OG)", "product_directory.csv.gz"),
    ]
    results = []
    for filename, sheet, output in tasks:
        result = extract_sheet(args.source_dir / filename, sheet, args.output_dir / output)
        results.append(result)
        print(json.dumps(result), flush=True)
    (args.output_dir / "extraction_manifest.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
