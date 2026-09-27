#!/usr/bin/env python3
"""TASK246: offline, evidence-bound population inventory; no ratio or live GET.

The document review is pinned separately from the numerical parsers. Hashes
authenticate this reviewed snapshot, not the truth of future unseen documents.
"""
import argparse
from datetime import date
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "docs/evidence/TASK_246_IBGE_MUNICIPAL_POPULATION_2016_2025_0.8.0"
PATHS = {
    "evidence": PREFIX + ".json", "support": PREFIX + ".support.json",
    "inventory": PREFIX + ".series.json",
    "contract": "config/ibge_municipal_population_2016_2025.v1.json",
    "acquisition": "config/ibge_municipal_population_acquisition.v1.json",
    "overlay": "config/ibge_population_denominator_rebase.v2.json",
}
BASE = "5b5bf747ece811e4c95fd57d9dfc1cc7d745aeaa"
YEARS = list(range(2016, 2026))
ESTIMATE_YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2024, 2025]
CODE = "3526902"
REVIEWED_SUPPORT_SHA256 = "bc4778a469088ef0e475ab5f115738e9b60a188497cd83feece694b4818788ca"
REVIEWED_CONTRACT_SHA256 = "919bc82bc84b16889eee49c8e3f68359a7d4056f8d0817d6492a3636be62b0f1"
REVIEWED_ACQUISITION_SHA256 = "d51bf845c78173e292e925baae38528140a62e0d7fbfcce663db88a4fa65ed2d"
PASS = "PASS_TASK246_NOT_COMPARABLE_9_OBSERVED_REFERENCE_YEARS_2023_MISSING"
PRESERVED = {
    "release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE",
    "closed_annual_series": "2016-2024", "gold_2025": "BLOCKED_NOT_CALCULATED",
    "financial_metrics_1_to_6": "PARTIAL", "per_capita_metrics_7_to_8": "NON_COMPARABLE",
    "gold_authorized": False, "series_inclusion_authorized": False,
    "release_promotion_authorized": False, "historical_rewrite_authorized": False,
    "per_capita_calculation_authorized": False, "num_popu_reuse_authorized": False,
    "automatic_future_acquisition_authorized": False,
}
NS = {"table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
      "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
      "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_digest(obj):
    return digest((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode())


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def extract_ods_row(payload):
    """Read only the municipal sheet and first five columns; never follow links."""
    with zipfile.ZipFile(io.BytesIO(payload)) as book:
        require(book.getinfo("content.xml").file_size < 40_000_000, "ODS XML exceeds bound")
        xml = book.read("content.xml")
    require(b"<!DOCTYPE" not in xml and b"<!ENTITY" not in xml, "unexpected XML entity")
    root = ET.fromstring(xml)
    sheets = [t for t in root.findall(".//table:table", NS)
              if t.get("{%s}name" % NS["table"], "").casefold() == "municípios"]
    require(len(sheets) == 1, "missing/duplicate municipal sheet")
    found, headers, logical_row = [], [], 0
    for row in sheets[0].findall("table:table-row", NS):
        repeat = int(row.get("{%s}number-rows-repeated" % NS["table"], "1"))
        require(1 <= repeat <= 1_048_576, "row repeat outside ODS bound")
        cells = []
        for cell in row:
            if cell.tag not in {"{%s}table-cell" % NS["table"], "{%s}covered-table-cell" % NS["table"]}:
                continue
            text = " ".join("".join(p.itertext()) for p in cell.findall("text:p", NS))
            value = cell.get("{%s}value" % NS["office"], text)
            count = int(cell.get("{%s}number-columns-repeated" % NS["table"], "1"))
            require(1 <= count <= 16_384, "column repeat outside ODS bound")
            cells.extend([value] * min(count, 5 - len(cells)))
            if len(cells) == 5:
                break
        if logical_row < 4:
            headers.append(cells)
        if len(cells) == 5 and cells[1:3] == ["35", "26902"]:
            require(repeat == 1 and cells[:4] == ["SP", "35", "26902", "Limeira"], "ODS identity drift")
            require(re.fullmatch(r"[0-9]+", cells[4]) is not None, "non-integer ODS population")
            found.append({"sheet": sheets[0].get("{%s}name" % NS["table"]),
                          "row_1_based": logical_row + 1, "columns": "A:E",
                          "identity_cells": cells[:4], "population": int(cells[4])})
        logical_row += repeat
    require(len(found) == 1, "missing/duplicate Limeira ODS row")
    return dict(found[0], header_rows=headers)


def parse_population(data, variable, label, years):
    require(isinstance(data, list) and len(data) == 1, "one variable required")
    var = data[0]
    require(var["id"] == variable and var["variavel"] == label and var["unidade"] == "Pessoas", "variable/unit drift")
    require(len(var["resultados"]) == 1, "unexpected result count")
    result = var["resultados"][0]
    require(result["classificacoes"] == [] and len(result["series"]) == 1, "classification/municipality count drift")
    series = result["series"][0]
    require(series["localidade"] == {"id": CODE, "nivel": {"id": "N6", "nome": "Município"}, "nome": "Limeira (SP)"}, "municipality identity drift")
    values = series["serie"]
    require(set(values) == {str(y) for y in years}, "reference-year coverage drift")
    require(all(isinstance(v, str) and re.fullmatch(r"[0-9]+", v) and int(v) > 0 for v in values.values()), "missing/non-integer population")
    return {int(y): int(v) for y, v in values.items()}


def build_inventory(contract, support, snapshots):
    """Build values from official structured snapshots, never transcribed numbers."""
    products = contract["products"]
    for table in ("6579", "4714"):
        meta, product = snapshots["metadata" + table], products[table]
        require(meta["id"] == int(table) and meta["classificacoes"] == [], "metadata table/classification drift")
        require("N6" in meta["nivelTerritorial"]["Administrativo"], "municipal coverage absent")
        variables = [v for v in meta["variaveis"] if v["id"] == int(product["variable"])]
        require(len(variables) == 1 and variables[0]["nome"] == product["variable_name"]
                and variables[0]["unidade"] == "Pessoas" and meta["pesquisa"] == product["name"], "official product identity drift")
    identity = snapshots["limeira_identity"]
    require(identity["id"] == int(CODE) and identity["nome"] == "Limeira"
            and identity["microrregiao"]["mesorregiao"]["UF"]["sigla"] == "SP", "official municipality identity drift")
    values = parse_population(snapshots["estimates_limeira"], "9324", "População residente estimada", ESTIMATE_YEARS)
    values.update(parse_population(snapshots["census_limeira"], "93", "População residente", [2022]))
    periods = {}
    for table in ("6579", "4714"):
        rows = snapshots["periods" + table]
        require(len({r["id"] for r in rows}) == len(rows), "duplicate official period")
        periods[table] = {int(r["id"]): r["modificacao"] for r in rows}
    require(sorted(set(periods["6579"]) & set(YEARS)) == ESTIMATE_YEARS
            and sorted(periods["4714"]) == [2022], "official availability drift")
    sources = {s["id"]: s for s in support["sources"]}
    observations = []
    for year in YEARS:
        common = {"year": year, "municipality_name": "Limeira", "uf": "SP", "municipality_ibge_code": CODE,
                  "unit": "Pessoas", "publication_date": None,
                  "publication_date_status": "NOT_ESTABLISHED_BY_ACQUIRED_ARTIFACTS",
                  "eligible_as_homogeneous_denominator": False}
        if year == 2023:
            common.update(population=None, status="MISSING_REFERENCE_YEAR", reference_date=None,
                          product=None, table=None, variable=None, classification=None,
                          projection_revision=None, source_id=None, source_url=None, retrieved_at=None,
                          vintage_or_revision=None, territorial_comparability="NOT_PROVEN",
                          notes="TCU 2023 publica referência censitária 2022; não é observação de população referida a 2023.")
        else:
            census = year == 2022
            table = "4714" if census else "6579"
            product = products[table]
            source = sources["CENSUS_LIMEIRA" if census else "ESTIMATES_LIMEIRA"]
            regime = next(r for r in contract["regimes"] if year in r["years"])
            crosscheck = support["ods_extracts"]["TCU2023_MUNICIPAL" if census else "REVISED" + str(year)]
            require(crosscheck["population"] == values[year], "API/official ODS mismatch")
            common.update(population=values[year], status="OBSERVED_OFFICIAL_NOT_APPROVED_FOR_MIXED_SERIES",
                          reference_date=f"{year}-08-01" if census else f"{year}-07-01",
                          product=product["name"], table=table, variable=product["variable"],
                          classification="CENSUS" if census else "ESTIMATE",
                          projection_revision=regime["projection_revision"],
                          source_id=source["id"], source_url=source["official_url"], retrieved_at=source["retrieved_at"],
                          vintage_or_revision={"sidra_period_modified": periods[table][year],
                                              "archive_edition": contract["archive_editions"][str(year)],
                                              "original_publication_equivalence": "NOT_ASSUMED"},
                          territorial_comparability="UPDATE_RECORDED_IMPACT_UNRESOLVED" if year == 2025 else "NOT_PROVEN",
                          notes=regime["notes"])
        observations.append(common)
    return {"schema": "TASK246_OFFICIAL_OBSERVATION_INVENTORY_V1", "purpose": "AUDIT_INVENTORY_NOT_HOMOGENEOUS_DENOMINATOR_SERIES",
            "observations": observations,
            "supplemental_publication": {"publication_year": 2023, "reference_year": 2022,
                                         "reference_date": "2022-08-01", "territorial_vintage": 2023,
                                         "municipality_ibge_code": CODE,
                                         "population": support["ods_extracts"]["TCU2023_MUNICIPAL"]["population"],
                                         "source_id": "TCU2023_MUNICIPAL", "fills_reference_year_2023": False}}


def assess(observations, rules, years):
    """Evaluate already reviewed semantics; same labels/values are not proof."""
    require([r["year"] for r in observations] == years and len(set(years)) == len(years), "inventory year order/coverage drift")
    observed = [r for r in observations if r["population"] is not None]
    for row in observed:
        require(type(row["population"]) is int and row["population"] > 0, "invalid population")
        require(date.fromisoformat(row["reference_date"]).year == row["year"], "publication year substituted for reference")
        require(row["unit"] == "Pessoas" and row["municipality_ibge_code"] == CODE, "unit/territory identity drift")
    revisions = sorted({r["projection_revision"] for r in observed if r["projection_revision"] is not None})
    kinds = {r["classification"] for r in observed}
    breaks = []
    if len(revisions) > 1 and rules["same_projection_revision_required"]:
        breaks.append("OFFICIAL_SAME_REVISION_RULE_VIOLATED")
    if kinds == {"CENSUS", "ESTIMATE"} and rules["unadjusted_census_estimate_direct_growth_rejected"]:
        breaks.append("CENSUS_AND_ADJUSTED_ESTIMATES_WITHOUT_OFFICIAL_ADAPTER")
    missing = [r["year"] for r in observations if r["population"] is None]
    unproven = any(r["territorial_comparability"] != "PROVEN_COMMON_TERRITORY" for r in observed)
    homogeneous = (len(revisions) == 1 and kinds == {"ESTIMATE"}
                   and all(type(r["projection_revision"]) is int for r in observed)
                   and len({r["reference_date"][4:] for r in observed}) == 1)
    status = "NOT_COMPARABLE" if breaks else "PARTIAL" if missing or unproven or not homogeneous else "PROVEN"
    return {"status": status, "observed_reference_years": [r["year"] for r in observed],
            "missing_reference_years": missing, "projection_revisions": revisions,
            "positive_incompatibilities": breaks, "homogeneous_denominator_eligible": status == "PROVEN"}


def validate_objects(evidence, contract, support, inventory, acquisition, overlay, snapshots):
    for name, obj, expected in (("support", support, REVIEWED_SUPPORT_SHA256),
                                ("contract", contract, REVIEWED_CONTRACT_SHA256),
                                ("acquisition", acquisition, REVIEWED_ACQUISITION_SHA256)):
        require(object_digest(obj) == expected, "unreviewed " + name + " integrity drift")
        require(evidence["artifact_sha256"][PATHS[name]] == expected, "evidence fingerprint drift")
    require(evidence["schema"] == "TASK246_IBGE_POPULATION_EVIDENCE_V1" and evidence["base_main_sha"] == BASE, "evidence identity drift")
    require(len(support["sources"]) == 34 and len({s["id"] for s in support["sources"]}) == 34, "source inventory drift")
    for source in support["sources"]:
        url = urlparse(source["official_url"])
        require(url.scheme == "https" and url.hostname in acquisition["official_hosts"], "non-official source")
        require(re.fullmatch(r"[a-f0-9]{64}", source["raw_sha256"]) and source["bytes"] > 0, "source fingerprint missing")
    for source in support["sources"]:
        if source.get("decoded_snapshot_path"):
            raw = (ROOT / source["decoded_snapshot_path"]).read_bytes()
            require(digest(raw) == source["decoded_sha256"], "decoded API snapshot drift")
            require(snapshots[source["id"].lower()] == json.loads(raw), "in-memory API snapshot drift")
    expected_inventory = build_inventory(contract, support, snapshots)
    require(inventory == expected_inventory, "materialized inventory disagrees with official snapshots or reference contract")
    decision = assess(inventory["observations"], contract["reviewed_comparison_rules"], YEARS)
    require(evidence["decision"] == decision, "decision disagrees with reviewed evidence")
    require(evidence["minimum_closing_evidence"] == contract["minimum_closing_evidence"], "closing artifact specification drift")
    require(evidence["preserved_state"] == overlay["preserved_state"] == PRESERVED, "protected state promoted")
    require(overlay == {
        "schema": "IBGE_POPULATION_DENOMINATOR_REBASE_V2", "task": "TASK_246", "issue": 819,
        "base_main_sha": BASE, "source_contract": PATHS["contract"], "evidence": PATHS["evidence"],
        "source_contract_status": decision["status"], "observation_inventory_materialized": True,
        "annual_comparable_denominator_series_materialized": False,
        "historical_num_popu_compatible": "NOT_PROVEN", "num_popu_2025_allowed": False,
        "rebased_series_identity_reserved": "SIOPE_PER_CAPITA_IBGE_REBASED_2016_2025",
        "decision": "STOP_IBGE_REBASE_DOCUMENTED_PRODUCT_REGIME_INCOMPATIBILITY",
        "next_gate": "OFFICIAL_HARMONIZED_MUNICIPAL_SERIES_OR_ADAPTER_WITH_TRUE_2023_AND_TERRITORY_PROOF",
        "preserved_state": PRESERVED}, "overlay expands scope")
    require(evidence["effects"] == {"official_artifacts_acquired": 34, "acquisition_attempts": 38,
            "observed_reference_years": 9, "per_capita_calculations": 0, "gold_calculations": 0,
            "drive_writes": 0, "external_publication": 0, "recurrence_created": 0}, "effects drift")
    require(evidence["raw_custody"] == support["raw_custody"], "custody fingerprint drift")
    require(evidence["historical_snapshots"] == support["historical_snapshots"], "historical manifest drift")
    for source in evidence["historical_snapshots"]:
        require(digest((ROOT / source["path"]).read_bytes()) == source["sha256"], "historical snapshot rewritten")
    return decision


def validate_custody(path, support):
    payload = Path(path).read_bytes()
    require(digest(payload) == support["raw_custody"]["archive_sha256"], "custody archive hash drift")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        require(archive.testzip() is None, "custody CRC failure")
        for source in support["sources"]:
            raw = archive.read(source["filename"])
            require(len(raw) == source["bytes"] and digest(raw) == source["raw_sha256"], "custody source drift")
            if source.get("decoded_snapshot_path"):
                decoded = gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw
                require(digest(decoded) == source["decoded_sha256"], "wire/decoded snapshot mismatch")
            if source["filename"].endswith(".ods"):
                require(extract_ods_row(raw) == support["ods_extracts"][source["id"]], "custody ODS extraction mismatch")


def validate(raw_custody=None):
    objects = {name: load(ROOT / path) for name, path in PATHS.items()}
    snapshots = {s["id"].lower(): load(ROOT / s["decoded_snapshot_path"])
                 for s in objects["support"]["sources"] if s.get("decoded_snapshot_path")}
    validate_objects(**objects, snapshots=snapshots)
    if raw_custody:
        validate_custody(raw_custody, objects["support"])
    return PASS


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-custody", type=Path, help="optional local official-source ZIP; never downloads")
    print(validate(parser.parse_args().raw_custody))
