"""Replay the two recovered, hash-pinned TASK219AA exports without network.

Inventory is evidence about these bytes, not an official namespace witness.
Private archive paths and non-identity row contents never enter the result.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .task283_tda_tce_namespace_dossier import Task283Stop, require

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SOURCES = {
    "empenhado": {
        "sha256": "08c10cb019f93ec408b4b8d30afa5474594a13a36d030e988a1503007c175735",
        "cells": ["B2", "C2", "B3", "C3", "B4", "C4", "A19", "B19", "A20", "B20"],
        "dimensions": None,
    },
    "detail": {
        "sha256": "1ed530c19958cc27b19ed5b418e4482cdd1c53fcdf7b8689029ba2ac62c1d2f3",
        "cells": ["B2", "C2", "B3", "C3", "A5", "A6"],
        "dimensions": None,
    },
}


def _inventory(payload: bytes, selected_cells: list[str]) -> dict:
    """Bounded OOXML inventory; callers cannot obtain a PROVEN result here."""
    require(len(payload) <= 1_000_000, "ARCHIVE_SIZE_LIMIT")
    with ZipFile(io.BytesIO(payload)) as archive:
        entries = archive.infolist()
        require(len(entries) <= 32, "ARCHIVE_MEMBER_LIMIT")
        require(len({entry.filename for entry in entries}) == len(entries), "ARCHIVE_DUPLICATE_MEMBER")
        require(sum(entry.file_size for entry in entries) <= 2_000_000, "ARCHIVE_EXPANSION_LIMIT")
        names = sorted(entry.filename for entry in entries)
        xml = {name: archive.read(name) for name in names if name.endswith((".xml", ".rels"))}
        require(not any(b"<!DOCTYPE" in value or b"<!ENTITY" in value for value in xml.values()), "ARCHIVE_XML_ENTITY")
        workbook = ET.fromstring(xml["xl/workbook.xml"])
        sheets = workbook.findall("s:sheets/s:sheet", NS)
        require(len(sheets) == 1, "ARCHIVE_SHEET_COUNT")
        worksheet_names = [name for name in names if name.startswith("xl/worksheets/") and name.endswith(".xml")]
        require(worksheet_names == ["xl/worksheets/sheet1.xml"], "ARCHIVE_SHEET_PATH")
        sheet = ET.fromstring(xml[worksheet_names[0]])
        shared = ET.fromstring(xml["xl/sharedStrings.xml"])
        strings = ["".join(t.text or "" for t in item.findall(".//s:t", NS)) for item in shared]
        cells = {}
        for cell in sheet.findall(".//s:c", NS):
            address = cell.attrib["r"]
            require(address not in cells, "ARCHIVE_DUPLICATE_CELL")
            value = cell.find("s:v", NS)
            text = value.text if value is not None else ""
            cells[address] = strings[int(text)] if cell.get("t") == "s" else text
        external = 0
        for name, value in xml.items():
            if name.endswith(".rels"):
                external += sum(node.get("TargetMode") == "External" for node in ET.fromstring(value))
        dimension = sheet.find("s:dimension", NS)
        core = ET.fromstring(xml["docProps/core.xml"])
        return {
            "zip_members": names,
            "sheet": sheets[0].get("name"),
            "sheet_state": sheets[0].get("state", "visible"),
            "dimensions": dimension.get("ref") if dimension is not None else None,
            "hidden_rows": sum(row.get("hidden") in ("1", "true") for row in sheet.findall(".//s:row", NS)),
            "hidden_columns": sum(col.get("hidden") in ("1", "true") for col in sheet.findall(".//s:col", NS)),
            "defined_names": len(workbook.findall("s:definedNames/s:definedName", NS)),
            "formulas": len(sheet.findall(".//s:f", NS)),
            "external_relationships": external,
            "core_creation_or_modification_timestamp_present": any(node.tag.rsplit("}", 1)[-1] in ("created", "modified") for node in core),
            "selected_cells": {address: cells.get(address) for address in selected_cells},
            "exact_cell_3286_present": "3286" in cells.values(),
            "exact_cell_3286_2026_present": "3286-2026" in cells.values(),
            "namespace_witness_proven": False,
        }


def inspect_recovered_export(kind: str, payload: bytes) -> dict:
    require(kind in SOURCES, "ARCHIVE_KIND")
    source = SOURCES[kind]
    digest = hashlib.sha256(payload).hexdigest()
    require(digest == source["sha256"], "ARCHIVE_SHA256_MISMATCH")
    result = _inventory(payload, source["cells"])
    require(result["dimensions"] == source["dimensions"], "ARCHIVE_DIMENSIONS")
    return {"kind": kind, "sha256": digest, "bytes": len(payload), **result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in SOURCES:
        parser.add_argument("--" + kind, required=True, type=Path)
    args = parser.parse_args()
    result = [inspect_recovered_export(kind, getattr(args, kind).read_bytes()) for kind in SOURCES]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
