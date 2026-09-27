#!/usr/bin/env python3
"""Pure T0/offline, fail-closed validation for TASK 010N-R-E-M3."""
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/siope_2025_operational_financial_alias_bridge/official_observations.json"
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_M3_SIOPE_2025_OPERATIONAL_FINANCIAL_ALIAS_BRIDGE_0.8.0.json"
EXACT = "PROVEN_EXACT_OPERATIONAL"
PARTIAL = "PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE"
DECISION = "KEEP_S2_NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING"
IDENTITY = {"NUM_ANO": 2025, "NUM_PERI": 6, "SIG_UF": "SP", "COD_MUNI": 352690, "NOM_MUNI": "Limeira"}
ALIASES = ["VAL_RECE_PREV_ATUA", "VAL_RECE_REAL", "VAL_DESP_DOTA_ATUA", "VAL_DESP_EMPE", "VAL_DESP_LIQU", "VAL_DESP_PAGA", "VL_DESP_DOTA_ATUA_EDU", "VL_DESP_EMPE_EDU", "VL_DESP_LIQU_EDU", "VL_DESP_PAGA_EDU"]
EXPECTED_VALUES = dict(zip(ALIASES, map(Decimal, ("2241993843.27", "2127095863.19", "2405001195.43", "1988819180.58", "1869450172.86", "1776933065.63", "520399255.47", "463766660.32", "455867723.30", "420264584.22"))))
EXPECTED_EDUCATION_ROWS = {
    (1, 122): ("58194646.42", "57157497.29", "52334270.19"),
    (6, 306): ("25882994.77", "25667968.46", "25667968.46"),
    (7, 361): ("209179060.27", "206490542.31", "188169219.56"),
    (10, 364): ("359190.71", "326465.86", "326465.86"),
    (11, 365): ("104486220.93", "101168603.39", "94086355.75"),
    (12, 365): ("50395938.38", "49788037.15", "45212100.65"),
    (13, 365): ("154882159.31", "150956640.54", "139298456.40"),
    (14, 366): ("427421.75", "427421.75", "388089.29"),
    (15, 367): ("14630720.85", "14630720.85", "13869648.22"),
    (18, 782): ("210466.24", "210466.24", "210466.24"),
}


def money(value):
    if not isinstance(value, str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)\.[0-9]{2}", value):
        raise ValueError("money must be an unaltered two-cent decimal string")
    return Decimal(value)


def keyed(rows, fields, label):
    result = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        if key in result:
            raise ValueError(f"duplicate {label}: {key}")
        result[key] = row
    return result


def validate(fixture, evidence):
    if fixture.get("fixture_schema") != "TASK_010N_R_E_M3_MINIMAL_OFFICIAL_OBSERVATIONS_V1" or fixture.get("identity") != IDENTITY:
        raise ValueError("fixture schema or Limeira identity drifted")
    if fixture.get("provenance") != {"classification": "USER_MEDIATED_OFFICIAL_OBSERVATION", "validator_network_requests": 0, "drive_reads": 0, "drive_writes": 0, "publication": False, "gold_computation": False}:
        raise ValueError("offline user-mediated provenance widened")
    alias_rows = keyed(fixture.get("aliases", []), ["alias"], "alias")
    if set(k[0] for k in alias_rows) != set(ALIASES) or len(alias_rows) != 10:
        raise ValueError("aliases must contain exactly the ten required unique fields")
    for row in alias_rows.values():
        if set(row) != {"alias", "raw_observed_value", "canonical_money"}:
            raise ValueError("raw and canonical alias representations must remain explicit")
        raw = row["raw_observed_value"]
        if not isinstance(raw, str) or Decimal(raw) != money(row["canonical_money"]):
            raise ValueError("raw observed alias and canonical Decimal disagree")
    if alias_rows[("VL_DESP_LIQU_EDU",)]["raw_observed_value"] != "455867723.3":
        raise ValueError("raw VL_DESP_LIQU_EDU lexical observation drifted")
    observed = {name: money(alias_rows[(name,)]["canonical_money"]) for name in ALIASES}
    if observed != EXPECTED_VALUES:
        raise ValueError("an observed official alias value was altered")

    revenues = keyed(fixture.get("receita_siope", []), ["category", "stage"], "revenue row")
    expected_revenue_keys = {(category, stage) for category in ("Receitas Correntes", "Receitas de Capital") for stage in ("PA", "RR")}
    if set(revenues) != expected_revenue_keys:
        raise ValueError("missing or unexpected Receita_Siope row/stage")
    reconciled = {
        "VAL_RECE_PREV_ATUA": sum((money(revenues[(c, "PA")]["value"]) for c in ("Receitas Correntes", "Receitas de Capital")), Decimal("0.00")),
        "VAL_RECE_REAL": sum((money(revenues[(c, "RR")]["value"]) for c in ("Receitas Correntes", "Receitas de Capital")), Decimal("0.00")),
    }

    rreo1 = keyed(fixture.get("rreo_anexo_1", []), ["line", "stage"], "RREO Anexo 1 row")
    required_rreo1 = {("SUBTOTAL DAS DESPESAS", stage) for stage in ("DA", "DE", "DL", "DP")} | {("RESERVA DO RPPS", "DA")}
    if set(rreo1) != required_rreo1:
        raise ValueError("missing or unexpected RREO Anexo 1 row/stage")
    reconciled.update({
        "VAL_DESP_DOTA_ATUA": money(rreo1[("SUBTOTAL DAS DESPESAS", "DA")]["value"]) + money(rreo1[("RESERVA DO RPPS", "DA")]["value"]),
        "VAL_DESP_EMPE": money(rreo1[("SUBTOTAL DAS DESPESAS", "DE")]["value"]),
        "VAL_DESP_LIQU": money(rreo1[("SUBTOTAL DAS DESPESAS", "DL")]["value"]),
        "VAL_DESP_PAGA": money(rreo1[("SUBTOTAL DAS DESPESAS", "DP")]["value"]),
    })

    education = keyed(fixture.get("despesas_funcao_educacao_siope", []), ["NUM_ORDE", "DES_SUBF"], "education NUM_ORDE/DES_SUBF")
    if set(education) != set(EXPECTED_EDUCATION_ROWS):
        raise ValueError("the ten exact education rows are missing, duplicated, or unexpected")
    for key, expected in EXPECTED_EDUCATION_ROWS.items():
        row = education[key]
        if set(row) != {"NUM_ORDE", "DES_SUBF", "DE", "DL", "DP"} or tuple(row[stage] for stage in ("DE", "DL", "DP")) != expected:
            raise ValueError(f"official education row altered: {key}")
    rreo8 = fixture.get("rreo_anexo_8_line_33", {})
    if set(rreo8) != {"line", "DA", "DE", "DL", "DP"} or rreo8.get("line") != "TOTAL GERAL DAS DESPESAS COM EDUCAÇÃO (10 + 20 + 32)":
        raise ValueError("RREO Anexo 8 line 33 missing or altered")
    for stage, alias in (("DE", "VL_DESP_EMPE_EDU"), ("DL", "VL_DESP_LIQU_EDU"), ("DP", "VL_DESP_PAGA_EDU")):
        components = money(education[(11, 365)][stage]) + money(education[(12, 365)][stage])
        subtotal = money(education[(13, 365)][stage])
        if components != subtotal:
            raise ValueError("education rows 11 + 12 must equal subtotal row 13")
        # Include the 365 subtotal exactly once; never add its component rows too.
        reconciled[alias] = sum((money(row[stage]) for key, row in education.items() if key[1] != 365), subtotal)
        alternative = sum((money(row[stage]) for key, row in education.items() if key[1] != 365), components)
        if reconciled[alias] != alternative or money(rreo8[stage]) != reconciled[alias]:
            raise ValueError("education non-double-counted aggregate or RREO equality altered")

    accounts = keyed(fixture.get("dados_informados_consolidado_despesa", []), ["account"], "consolidated account")
    if set(accounts) != {("3.2.00.00.00",), ("3.2.91.00.00",)}:
        raise ValueError("budget-only parent/child rows missing or unexpected")
    parent, child = accounts[("3.2.00.00.00",)], accounts[("3.2.91.00.00",)]
    if parent.get("hierarchy_role") != "PARENT_INCLUDE_ONCE" or child.get("hierarchy_role") != "CHILD_DO_NOT_ADD":
        raise ValueError("parent/child non-additive rule altered")
    for stage in ("DA", "DE", "DL", "DP"):
        if money(parent[stage]) != money(child[stage]):
            raise ValueError("hierarchical child no longer duplicates parent")
    if any(money(parent[s]) != Decimal("0.00") for s in ("DE", "DL", "DP")) or money(parent["DA"]) != Decimal("1000.00"):
        raise ValueError("budget-only 1000.00 item altered")
    rreo_da = money(rreo8["DA"])
    consolidated_total = fixture.get("dados_informados_consolidado_despesa_total", {})
    if consolidated_total != {"stage": "DA", "raw_observed_value": "526804985.21", "canonical_money": "526804985.21"} or money(consolidated_total["canonical_money"]) != Decimal("526804985.21"):
        raise ValueError("raw consolidated DA total 526804985.21 altered")
    # Keep the RREO value as the reconciled value.  The 1000 item is candidate
    # explanatory evidence only: no source-defined backend inclusion rule exists.
    reconciled["VL_DESP_DOTA_ATUA_EDU"] = rreo_da
    if observed["VL_DESP_DOTA_ATUA_EDU"] - rreo_da != Decimal("1000.00"):
        raise ValueError("documented RREO variance must equal exactly 1000.00")

    for alias in set(ALIASES) - {"VL_DESP_DOTA_ATUA_EDU"}:
        if reconciled[alias] != observed[alias]:
            raise ValueError(f"exact cent reconciliation failed for {alias}")
    if (evidence.get("evidence_schema"), evidence.get("software_version"), evidence.get("task"), evidence.get("base_main_sha"), evidence.get("tier"), evidence.get("identity")) != ("TASK_010N_R_E_M3_OPERATIONAL_FINANCIAL_ALIAS_BRIDGE_V1", "0.8.0", "TASK_010N-R-E-M3", "91337f7ec06edd082887cdb50822e9fc1aad9b57", "T0_OFFLINE_B2_ONLY", IDENTITY):
        raise ValueError("evidence identity, base, version, or tier drifted")
    if evidence.get("provenance") != {"classification": "USER_MEDIATED_OFFICIAL_OBSERVATION", "sanitized_minimal_fixture": "tests/fixtures/siope_2025_operational_financial_alias_bridge/official_observations.json", "validator_network_requests": 0, "drive_reads": 0, "drive_writes": 0, "publication": False, "gold_computation": False}:
        raise ValueError("evidence offline scope widened")
    expected_matrix = evidence.get("matrix")
    if not isinstance(expected_matrix, list) or [row.get("alias") for row in expected_matrix] != ALIASES:
        raise ValueError("field matrix must have all ten aliases in canonical order")
    for row in expected_matrix:
        alias = row["alias"]
        expected_status = PARTIAL if alias == "VL_DESP_DOTA_ATUA_EDU" else EXACT
        variance = Decimal("1000.00") if alias == "VL_DESP_DOTA_ATUA_EDU" else Decimal("0.00")
        if set(row) != {"alias", "official_concept", "evidence_sources", "observed_alias_value", "reconciled_value", "variance", "status", "reason"}:
            raise ValueError("matrix schema drifted")
        if money(row["observed_alias_value"]) != observed[alias] or money(row["reconciled_value"]) != reconciled[alias] or money(row["variance"]) != variance or row["status"] != expected_status or not row["official_concept"] or not row["evidence_sources"] or not row["reason"]:
            raise ValueError(f"matrix evidence drifted for {alias}")
    if evidence.get("summary") != {EXACT: 9, "PARTIAL": 1, "AMBIGUOUS": 0, "NOT_FOUND": 0}:
        raise ValueError("summary drifted")
    expected_state = {"release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE", "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "annual_closure_status": "UNKNOWN", "semantic_comparability_status": "UNKNOWN", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED", "year_2026": "UNPROVEN_CURRENT_YEAR", "semantic_comparability_missing_gates": ["EXACT_SOURCE_DEFINED_BACKEND_INCLUSION_RULE_FOR_VL_DESP_DOTA_ATUA_EDU", "B1_NUM_POPU_SOURCE_VINTAGE_AND_GLOBAL_COMPARABILITY_GATE"]}
    if evidence.get("canonical_state") != expected_state or evidence.get("decision") != DECISION or evidence.get("education_scope_note") != "EDU != MDE as a general identity; this proof covers only the current aliases and observed official aggregates.":
        raise ValueError("bounded B2 decision or EDU/MDE guard drifted")
    return expected_matrix


def main():
    validate(json.loads(FIXTURE.read_text(encoding="utf-8")), json.loads(EVIDENCE.read_text(encoding="utf-8")))
    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
