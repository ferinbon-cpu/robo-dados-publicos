#!/usr/bin/env python3
"""Pure T0/offline, fail-closed validation for TASK 010N-R-E-M4."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_M4_SIOPE_2025_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_0.8.0.json"
DECISION = "KEEP_S2_NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING"
PARTIAL = "PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE"
EXPECTED_TERMS = [
    "VL_DESP_DOTA_ATUA_EDU", "DOTA_ATUA_EDU", "DOTACAO_ATUALIZADA EDUCACAO",
    "dotação educação", "TOTAL GERAL DAS DESPESAS COM EDUCAÇÃO",
    "3.2.00.00.00", "3.2.91.00.00", "520399255.47", "520398255.47",
]
EXPECTED_INVENTORY = {
    "docs/evidence/TASK_010N_R_E_M3_SIOPE_2025_OPERATIONAL_FINANCIAL_ALIAS_BRIDGE_0.8.0.json": "df84296b8fa4a04d09431329395e4fa6d44d669799dc4041c7f35695e955774e",
    "tests/fixtures/siope_2025_operational_financial_alias_bridge/official_observations.json": "a190bf8ac3f11e5d0e84f2dba56d286e128f577c0d9b426f82a852ca3a4f2a30",
    "docs/evidence/TASK_010N_R_E_M2_SIOPE_EDMX_HANDOFF_AUDIT_0.8.0.json": "72d2dbdddb74b7a24c648ccdf10583080ffae9c6b4a0c5c53ba9cd950fcbd91f",
    "docs/evidence/TASK_010L_SIOPE_2025_ODATA_ALIAS_STATIC_BRIDGE_0.8.0.json": "09aa8edef521a47090c219c649d8cbeaeb5673b0dafc6f5f72557505e36e1f7d",
    "docs/evidence/TASK_010K_SIOPE_2025_OFFLINE_SEMANTIC_REVIEW_0.8.0.json": "6861167287d0c7a7415fd4b214977590730b95b757ef2200aa1c81017463c6a1",
    "docs/evidence/TASK_010N_R_E_D_SIOPE_OFFICIAL_DOC_ALIAS_CONCEPT_SEARCH_0.8.0.json": "b8e6d0d91ede314551ee257579886d179ebcecbc9855e8d35df911f1e79c3446",
}
EXPECTED_STATE = {
    "release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE",
    "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN",
    "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
    "financial_aliases_proven_exact_operational": "9/10",
    "annual_closure_status": "UNKNOWN", "semantic_comparability_status": "UNKNOWN",
    "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED",
    "year_2026": "UNPROVEN_CURRENT_YEAR",
}


def validate(evidence, *, verify_files=True):
    identity = (evidence.get("evidence_schema"), evidence.get("software_version"),
                evidence.get("task"), evidence.get("base_main_sha"), evidence.get("tier"))
    if identity != ("TASK_010N_R_E_M4_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_V1", "0.8.0",
                    "TASK_010N-R-E-M4", "158dcae15fab2f4809434d16556ace03c55dc08f",
                    "T0_OFFLINE_INVENTORY_ONLY"):
        raise ValueError("evidence identity, base, version, or T0 tier drifted")
    if evidence.get("search_terms") != EXPECTED_TERMS:
        raise ValueError("required exact search inventory drifted")

    rows = evidence.get("inventory")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_INVENTORY):
        raise ValueError("inventory must contain exactly the pinned local artifacts")
    indexed = {}
    for row in rows:
        if set(row) != {"path", "sha256", "finding"} or not row["finding"]:
            raise ValueError("inventory row schema or finding drifted")
        if row["path"] in indexed:
            raise ValueError("duplicate inventory path")
        indexed[row["path"]] = row["sha256"]
    if indexed != EXPECTED_INVENTORY:
        raise ValueError("inventory path or pinned hash drifted")
    if verify_files:
        for path, expected_hash in EXPECTED_INVENTORY.items():
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            if actual != expected_hash:
                raise ValueError(f"pinned inventory artifact changed: {path}")

    candidates = evidence.get("candidate_assessment")
    expected_classes = ["CANDIDATE_ONLY", "STRUCTURAL_ONLY", "CONCEPT_ONLY", "NOT_FOUND", "INAPPLICABLE_FOR_PROMOTION"]
    if not isinstance(candidates, list) or [row.get("classification") for row in candidates] != expected_classes:
        raise ValueError("candidate classifications drifted")
    if len({row.get("candidate") for row in candidates}) != 5 or any(not row.get("insufficiency") for row in candidates):
        raise ValueError("every unique candidate needs an insufficiency reason")
    observed = candidates[0].get("observations", {})
    required_values = {"alias": "520399255.47", "rreo_line_33_DA": "520398255.47", "variance": "1000.00", "account_parent_DA": "1000.00", "account_child_DA": "1000.00"}
    if observed != required_values:
        raise ValueError("current candidate observations drifted")
    if Decimal(observed["alias"]) - Decimal(observed["rreo_line_33_DA"]) != Decimal("1000.00"):
        raise ValueError("exact Decimal variance drifted")

    result = evidence.get("field_result")
    if result != {"alias": "VL_DESP_DOTA_ATUA_EDU", "status": PARTIAL,
                  "source_defined_current_rule": "NOT_FOUND", "promotion_performed": False}:
        raise ValueError("field result was promoted or drifted")
    next_evidence = evidence.get("smallest_next_evidence_acquisition", {})
    if set(next_evidence) != {"required_artifact", "acceptance_condition", "acquisition_boundary"} or any(not value for value in next_evidence.values()):
        raise ValueError("smallest next evidence acquisition is incomplete")
    if evidence.get("canonical_state") != EXPECTED_STATE:
        raise ValueError("bounded canonical state drifted")
    guards = {"EDU_equals_MDE": False, "network_requests": 0, "drive_reads": 0,
              "drive_writes": 0, "publication": False, "gold_computation": False}
    if evidence.get("guards") != guards or evidence.get("decision") != DECISION:
        raise ValueError("fail-closed guards or decision drifted")
    return DECISION


def main():
    validate(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
