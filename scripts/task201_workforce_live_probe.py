from __future__ import annotations

import argparse
import collections
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import re
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task201_workforce_live_probe.v1.json"
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


class Task201Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task201Stop(code)


def _norm(value: Any) -> str:
    raw = html.unescape(str(value or ""))
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", raw).strip().casefold()


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK201_WORKFORCE_LIVE_PROBE_V1", "TASK201_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_PRIMARY_WORKFORCE_DISCOVERY", "TASK201_MODE")
    _stop(obj.get("authorization_issue") == 639, "TASK201_ISSUE")
    inep = obj["sources"]["inep_sinopse"]
    _stop(urllib.parse.urlparse(inep["url"]).hostname == inep["allowed_host"], "TASK201_INEP_HOST")
    _stop(inep["max_http_attempts"] == 3, "TASK201_INEP_ATTEMPTS")
    for key in ("sme_home", "sme_contracted"):
        source = obj["sources"][key]
        _stop(urllib.parse.urlparse(source["url"]).hostname in set(source["allowed_hosts"]), f"TASK201_{key.upper()}_HOST")
        _stop(source["max_http_attempts"] == 2, f"TASK201_{key.upper()}_ATTEMPTS")
    privacy = obj["privacy"]
    _stop(privacy["person_level_input_ephemeral_only"] is True, "TASK201_PRIVACY_EPHEMERAL")
    _stop(privacy["aggregate_only"] is True, "TASK201_PRIVACY_AGGREGATE")
    _stop(
        all(
            privacy[key] is False
            for key in (
                "raw_sme_html_persisted",
                "raw_sme_html_artifact",
                "names_persisted",
                "cpf_persisted",
                "matricula_persisted",
                "person_hashes_persisted",
            )
        ),
        "TASK201_PRIVACY_PERSISTENCE",
    )
    output = obj["output"]
    _stop(output["staff_count_materialized"] is False, "TASK201_NO_STAFF_MATERIALIZE")
    _stop(output["employment_bond_materialized"] is False, "TASK201_NO_BOND_MATERIALIZE")
    _stop(
        all(
            output[key] is False
            for key in (
                "raw_zip_persisted",
                "raw_workbook_persisted",
                "raw_html_persisted",
                "drive_write",
                "serving",
                "publication",
                "schedule",
                "recurrence",
            )
        ),
        "TASK201_OUTPUT_EFFECT",
    )
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj = _load(contract_path)
    _stop(len(main_sha) == 40 and all(ch in "0123456789abcdef" for ch in main_sha.lower()), "TASK201_AUTH_SHA")
    return (
        "TASK201_WORKFORCE_LIVE_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} "
        "inep_attempts=3 sme_attempts=2 raw_persist=0 pii_persist=0"
    )


class _AllowedHostRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts: set[str]):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).hostname not in self.hosts:
            raise Task201Stop("TASK201_CROSS_HOST_REDIRECT")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_bytes(
    url: str,
    *,
    allowed_hosts: set[str],
    attempts: int,
    accept: str,
    user_agent: str,
    timeout: int = 180,
) -> dict[str, Any]:
    opener = urllib.request.build_opener(_AllowedHostRedirect(allowed_hosts))
    errors: list[str] = []
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": accept,
                    "Accept-Encoding": "identity",
                },
                method="GET",
            )
            with opener.open(req, timeout=timeout) as response:
                final_host = urllib.parse.urlparse(response.geturl()).hostname
                _stop(final_host in allowed_hosts, "TASK201_FINAL_HOST")
                data = response.read()
            _stop(bool(data), "TASK201_EMPTY_SOURCE")
            return {
                "data": data,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "attempts_used": attempt,
                "final_host": final_host,
            }
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError, Task201Stop) as exc:
            errors.append(type(exc).__name__)
            if isinstance(exc, Task201Stop) and str(exc) in {"TASK201_CROSS_HOST_REDIRECT", "TASK201_FINAL_HOST"}:
                raise
            if attempt < attempts:
                time.sleep(2 * attempt)
    raise Task201Stop("TASK201_FETCH_FAILED:" + ",".join(errors))


def _decode_html(data: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def _plain_html_text(data: bytes) -> str:
    parser = _TextParser()
    parser.feed(_decode_html(data))
    return " ".join(parser.parts)


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.casefold()
        if tag == "tr":
            self.in_row = True
            self.current_row = []
        elif tag in {"td", "th"} and self.in_row:
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.in_cell and data.strip():
            self.current_cell.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in {"td", "th"} and self.in_cell:
            self.current_row.append(re.sub(r"\s+", " ", " ".join(self.current_cell)).strip())
            self.current_cell = []
            self.in_cell = False
        elif tag == "tr" and self.in_row:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_row = False


def parse_sme_bonds(home_bytes: bytes) -> dict[str, Any]:
    text = _norm(_plain_html_text(home_bytes))
    effective = "professores efetivos" in text or "professor efetivo" in text
    clt = "( clt )" in text or "(clt)" in text or "professores clt" in text
    _stop(effective, "TASK201_SME_EFFECTIVE_LABEL_NOT_FOUND")
    _stop(clt, "TASK201_SME_CLT_LABEL_NOT_FOUND")
    return {
        "bond_categories": ["EFETIVO", "CLT_PROCESSO_SELETIVO"],
        "category_count": 2,
        "evidence_semantic": "CURRENT_SME_OPERATIONAL_ATTRIBUTION_LABELS",
    }


def parse_contracted_aggregate(contracted_bytes: bytes, expected_title: str) -> dict[str, Any]:
    raw_text = _plain_html_text(contracted_bytes)
    _stop(_norm(expected_title) in _norm(raw_text), "TASK201_CONTRACTED_TITLE")
    date_match = re.search(r"IMPRESS[AÃ]O\s+EM\s*:\s*(\d{2}-\d{2}-\d{4})", raw_text, re.I)
    _stop(date_match is not None, "TASK201_CONTRACTED_PRINT_DATE")

    parser = _TableParser()
    parser.feed(_decode_html(contracted_bytes))
    persons: collections.Counter[str] = collections.Counter()
    cargos: collections.Counter[str] = collections.Counter()
    schools: set[str] = set()
    assignment_rows = 0

    for row in parser.rows:
        if len(row) < 5:
            continue
        normalized = [_norm(cell) for cell in row]
        if normalized[0] in {"matricula", "matrícula"} or "cpf" in normalized[2].replace(".", ""):
            continue
        first = row[0].strip()
        cpf = re.sub(r"\D", "", row[2])
        if not first or len(cpf) != 11:
            continue
        assignment_rows += 1
        persons[first] += 1
        cargos[row[3].strip().upper()] += 1
        schools.add(row[4].strip().upper())

    _stop(assignment_rows > 0, "TASK201_CONTRACTED_NO_ROWS")
    _stop(len(persons) > 0, "TASK201_CONTRACTED_NO_PEOPLE")
    _stop(assignment_rows >= len(persons), "TASK201_CONTRACTED_ROW_PERSON_RELATION")
    duplicates = sum(1 for count in persons.values() if count > 1)
    return {
        "print_date": date_match.group(1),
        "assignment_row_count": assignment_rows,
        "unique_contracted_teacher_count": len(persons),
        "people_with_multiple_assignment_rows": duplicates,
        "distinct_school_label_count": len(schools),
        "assignment_rows_by_cargo": dict(sorted(cargos.items())),
        "dedupe_key_semantic": "EPHEMERAL_PRIVATE_IDENTIFIER_NOT_PERSISTED",
        "person_level_output": False,
    }


def _shared_strings(xlsx: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in xlsx.namelist():
        return []
    root = ET.fromstring(xlsx.read(name))
    result: list[str] = []
    for si in root.findall("main:si", NS):
        result.append("".join((t.text or "") for t in si.findall(".//main:t", NS)))
    return result


def _sheet_map(xlsx: zipfile.ZipFile) -> list[tuple[str, str]]:
    wb = ET.fromstring(xlsx.read("xl/workbook.xml"))
    rels = ET.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
    target_by_id = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("pkgrel:Relationship", NS)}
    result: list[tuple[str, str]] = []
    for sheet in wb.findall("main:sheets/main:sheet", NS):
        rid = sheet.attrib.get("{%s}id" % NS["rel"])
        target = target_by_id.get(rid, "")
        target = ("xl/" + target.lstrip("./")) if not target.startswith("/") else target.lstrip("/")
        result.append((sheet.attrib.get("name", ""), target))
    return result


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    ctype = cell.attrib.get("t")
    if ctype == "inlineStr":
        return "".join((t.text or "") for t in cell.findall(".//main:t", NS))
    node = cell.find("main:v", NS)
    if node is None:
        return ""
    raw = node.text or ""
    if ctype == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return ""
    return raw


def _row_cells(row: ET.Element, shared: list[str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for cell in row.findall("main:c", NS):
        value = _cell_value(cell, shared)
        if value != "":
            result.append({"ref": cell.attrib.get("r", ""), "value": value})
    return result


def scan_inep_docente_candidates(package_bytes: bytes, target: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    workbooks: list[dict[str, Any]] = []
    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        tmp.write(package_bytes)
        tmp.flush()
        with zipfile.ZipFile(tmp.name, "r") as outer:
            names = [name for name in outer.namelist() if name.casefold().endswith(".xlsx")]
            _stop(bool(names), "TASK201_INEP_NO_XLSX")
            for name in names:
                data = outer.read(name)
                workbooks.append({
                    "basename": Path(name).name,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                })
                with tempfile.NamedTemporaryFile(suffix=".xlsx") as xfile:
                    xfile.write(data)
                    xfile.flush()
                    with zipfile.ZipFile(xfile.name, "r") as xlsx:
                        shared = _shared_strings(xlsx)
                        for sheet_name, sheet_path in _sheet_map(xlsx):
                            if sheet_path not in xlsx.namelist():
                                continue
                            root = ET.fromstring(xlsx.read(sheet_path))
                            rows: list[tuple[int, list[dict[str, str]], str]] = []
                            has_docente = "docent" in _norm(sheet_name)
                            limeira_positions: list[int] = []
                            keyword_hits: set[str] = set()
                            for row in root.findall(".//main:sheetData/main:row", NS):
                                cells = _row_cells(row, shared)
                                if not cells:
                                    continue
                                row_num = int(row.attrib.get("r", "0") or 0)
                                text = " | ".join(cell["value"] for cell in cells)
                                norm = _norm(text)
                                rows.append((row_num, cells, norm))
                                if "docent" in norm:
                                    has_docente = True
                                for key in target["inep_keywords"]:
                                    if _norm(key) in norm:
                                        keyword_hits.add(_norm(key))
                                if _norm(target["municipality_name"]) in norm:
                                    limeira_positions.append(len(rows) - 1)
                            if not has_docente or not limeira_positions:
                                continue
                            limeira_rows = []
                            header_rows = []
                            seen_header_rows: set[int] = set()
                            for pos in limeira_positions[:5]:
                                row_num, cells, _ = rows[pos]
                                limeira_rows.append({"row": row_num, "cells": cells[:100]})
                                for hpos in range(max(0, pos - 12), pos):
                                    hnum, hcells, _ = rows[hpos]
                                    if hnum not in seen_header_rows:
                                        header_rows.append({"row": hnum, "cells": hcells[:100]})
                                        seen_header_rows.add(hnum)
                            candidates.append({
                                "workbook": Path(name).name,
                                "sheet": sheet_name,
                                "keyword_hits": sorted(keyword_hits),
                                "header_rows": header_rows[-25:],
                                "limeira_rows": limeira_rows,
                            })
                            if len(candidates) >= 12:
                                break
                        if len(candidates) >= 12:
                            break
                if len(candidates) >= 12:
                    break
    return {
        "workbook_count": len(workbooks),
        "workbooks": workbooks,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "staff_count_materialized": False,
    }


def _assert_no_person_level_payload(result: dict[str, Any]) -> None:
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    lowered = _norm(encoded)
    forbidden_keys = ["cpf", "nome", "matricula", "registration_value"]
    _stop(not any(token in lowered for token in forbidden_keys), "TASK201_PERSON_LEVEL_OUTPUT_LEAK")
    _stop(not re.search(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", encoded), "TASK201_CPF_PATTERN_LEAK")


def derive_sanitized_result(
    *,
    inep_bytes: bytes,
    sme_home_bytes: bytes,
    sme_contracted_bytes: bytes,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = _load(contract_path)
    inep = scan_inep_docente_candidates(inep_bytes, obj["target"])
    bonds = parse_sme_bonds(sme_home_bytes)
    contracted = parse_contracted_aggregate(
        sme_contracted_bytes,
        obj["sources"]["sme_contracted"]["expected_title"],
    )
    result = {
        "schema": "TASK201_WORKFORCE_SANITIZED_DISCOVERY_V1",
        "status": "PASS" if inep["candidate_count"] > 0 else "PARTIAL_NO_INEP_DOCENTE_CANDIDATE",
        "target": {
            "municipality_name": obj["target"]["municipality_name"],
            "municipality_code": obj["target"]["municipality_code"],
            "inep_period": str(obj["target"]["year"]),
            "sme_period": "CURRENT_OPERATIONAL_PAGE",
        },
        "inep_docente_probe": inep,
        "sme_bond_taxonomy": bonds,
        "sme_contracted_aggregate": contracted,
        "guards": {
            "assignment_rows_are_not_unique_people": True,
            "school_level_docente_sum_is_not_network_unique_headcount": True,
            "inep_2025_is_not_sme_2026_period": True,
            "clt_is_not_all_non_effective_bonds": True,
            "person_level_output": False,
            "raw_bytes_persisted": False,
            "staff_count_materialized": False,
            "employment_bond_materialized": False,
            "drive_write": False,
            "serving": False,
            "publication": False,
            "schedule": False,
            "recurrence": False,
        },
    }
    _assert_no_person_level_payload(result)
    return result


def run_live(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(contract_path)
    main_sha = str(os.environ.get("GITHUB_SHA") or "")
    checked = str(os.environ.get("TASK201_CHECKED_OUT_SHA") or "")
    comment = str(os.environ.get("TASK201_AUTH_COMMENT") or "")
    issue = str(os.environ.get("TASK201_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK201_CHECKOUT_SHA")
    _stop(issue == str(obj["authorization_issue"]), "TASK201_RUNTIME_ISSUE")
    _stop(comment == exact_auth_comment(main_sha, contract_path), "TASK201_AUTH_COMMENT")

    inep_src = obj["sources"]["inep_sinopse"]
    home_src = obj["sources"]["sme_home"]
    contracted_src = obj["sources"]["sme_contracted"]

    inep_fetch = _fetch_bytes(
        inep_src["url"],
        allowed_hosts={inep_src["allowed_host"]},
        attempts=inep_src["max_http_attempts"],
        accept="application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
        user_agent="robo-dados-publicos-task201/0.8.0",
    )
    home_fetch = _fetch_bytes(
        home_src["url"],
        allowed_hosts=set(home_src["allowed_hosts"]),
        attempts=home_src["max_http_attempts"],
        accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        user_agent="robo-dados-publicos-task201/0.8.0",
        timeout=60,
    )
    contracted_fetch = _fetch_bytes(
        contracted_src["url"],
        allowed_hosts=set(contracted_src["allowed_hosts"]),
        attempts=contracted_src["max_http_attempts"],
        accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        user_agent="robo-dados-publicos-task201/0.8.0",
        timeout=60,
    )

    result = derive_sanitized_result(
        inep_bytes=inep_fetch.pop("data"),
        sme_home_bytes=home_fetch.pop("data"),
        sme_contracted_bytes=contracted_fetch.pop("data"),
        contract_path=contract_path,
    )
    result["source"] = {
        "inep_sinopse": {
            "url": inep_src["url"],
            "package_sha256": inep_fetch["sha256"],
            "package_bytes": inep_fetch["bytes"],
            "attempts_used": inep_fetch["attempts_used"],
        },
        "sme_home": {
            "url": home_src["url"],
            "html_sha256": home_fetch["sha256"],
            "html_bytes": home_fetch["bytes"],
            "attempts_used": home_fetch["attempts_used"],
        },
        "sme_contracted": {
            "url": contracted_src["url"],
            "html_sha256": contracted_fetch["sha256"],
            "html_bytes": contracted_fetch["bytes"],
            "attempts_used": contracted_fetch["attempts_used"],
        },
    }
    result["authorization"] = {
        "issue": obj["authorization_issue"],
        "main_sha": main_sha,
        "exact_comment_verified": True,
    }
    _assert_no_person_level_payload(result)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    result = run_live(args.output, args.contract)
    print(json.dumps({
        "status": result["status"],
        "inep_candidate_count": result["inep_docente_probe"]["candidate_count"],
        "bond_categories": result["sme_bond_taxonomy"]["bond_categories"],
        "contracted_assignment_rows": result["sme_contracted_aggregate"]["assignment_row_count"],
        "unique_contracted_teachers": result["sme_contracted_aggregate"]["unique_contracted_teacher_count"],
        "person_level_output": result["guards"]["person_level_output"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
