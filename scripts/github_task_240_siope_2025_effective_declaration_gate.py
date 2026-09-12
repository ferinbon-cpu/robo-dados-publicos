#!/usr/bin/env python3
"""Deterministic T0 gate for TASK 240 B3 effective annual SIOPE declaration."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "docs/evidence/TASK_240_FNDE_B3_AUTHORITATIVE_RESPONSE_INTAKE_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_240_SIOPE_2025_EFFECTIVE_ANNUAL_DECLARATION_0.8.0.json"
PRIOR = ROOT / "docs/evidence/TASK_010N_R_E_M7_SIOPE_2025_LIMEIRA_ANNUAL_RECEIPT_EFFECTIVE_DECLARATION_0.8.0.json"
TASK016_PATH = ROOT / "scripts/github_task_016_fnde_authoritative_response_intake_gate.py"

EXPECTED_DECISION = "RESOLVE_B3_WITH_AUTHORITATIVE_DYNAMIC_SELECTION_RULE_AND_PINNED_LIMEIRA_RECEIPT"
EXPECTED_B3 = "PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT"
EXPECTED_MAIN = "ff88a34613a4b9a1e7259f1fa7f72450777f9c7e"
EXPECTED_HASH = "c34866e1f9b9383eb34996ecd69874302cfd508a89d55be25be6606fad2db554"

spec = importlib.util.spec_from_file_location("task016_gate", TASK016_PATH)
TASK016 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(TASK016)


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def validate_objects(evidence, intake, prior, intake_status):
    identity = (
        evidence.get("evidence_schema"), evidence.get("task"), evidence.get("issue"),
        evidence.get("base_main_sha"), evidence.get("tier"), evidence.get("decision"),
    )
    expected_identity = (
        "TASK_240_SIOPE_2025_EFFECTIVE_ANNUAL_DECLARATION_V1", "TASK_240", 806,
        EXPECTED_MAIN, "T0_OFFLINE_OPERATOR_PROVIDED_PRIMARY_FNDE_RESPONSE", EXPECTED_DECISION,
    )
    if identity != expected_identity:
        raise ValueError("TASK240 identity/base/decision drift")

    scope = evidence.get("scope", {})
    if scope != {"year":2025,"period":6,"period_label":"Annual","uf":"SP","municipality_code":352690,"municipality":"Limeira","system":"SIOPE","boundary":"B3_EFFECTIVE_DECLARATION_ONLY"}:
        raise ValueError("TASK240 scope drift")

    response = evidence.get("authoritative_response", {})
    if (response.get("authority") != "FNDE" or response.get("unit") != "SEOPS" or
        response.get("fala_br_nup") != "23546.111502/2026-41" or response.get("sei_document_number") != "5783017" or
        response.get("sha256") != EXPECTED_HASH or response.get("bytes") != 66632 or response.get("mime") != "application/pdf" or
        response.get("raw_pdf_committed") is not False or response.get("operator_provided") is not True):
        raise ValueError("TASK240 authoritative response provenance drift")

    if intake_status != "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW":
        raise ValueError("TASK240 TASK016 intake is not complete for decision review")
    if intake.get("blocker_id") != "B3_EFFECTIVE_DECLARATION" or intake.get("protocol") != "23546.111502/2026-41" or intake.get("raw_artifact_sha256") != EXPECTED_HASH:
        raise ValueError("TASK240 intake identity drift")
    assessments = intake.get("proposition_assessments", [])
    if len(assessments) != 4 or any(item.get("assessment") != "PROVEN_EXPLICIT" for item in assessments):
        raise ValueError("TASK240 requires 4/4 explicit proposition proof")

    task016 = evidence.get("task016_intake", {})
    if (task016.get("path") != "docs/evidence/TASK_240_FNDE_B3_AUTHORITATIVE_RESPONSE_INTAKE_0.8.0.json" or
        task016.get("status") != intake_status or task016.get("propositions_proven_explicit") != "4/4" or
        task016.get("promotion_performed_by_task016") is not False):
        raise ValueError("TASK240 intake summary drift")

    expected_rule = {
        "later_rectifying_declaration_supersedes_previous_for_same_entity_exercise_period": True,
        "new_receipt_corresponds_to_rectifying_declaration": True,
        "previous_receipt_should_not_be_used_as_proof_of_current_declaration": True,
        "effective_declaration_selection": "LATEST_DECLARATION_TRANSMITTED_AND_RECEIVED_SUCCESSFULLY",
        "public_receipts_surface": "ALWAYS_LATEST_SUCCESSFUL_TRANSMISSION_RECEIPT",
        "specific_manual_or_technical_document_exists": False,
        "implemented_siope_operating_rule_confirmed": True,
    }
    if evidence.get("authoritative_system_rule", {}) != expected_rule:
        raise ValueError("TASK240 authoritative system-rule drift")

    prior_proof = prior.get("proof_status", {})
    if prior.get("decision") != "KEEP_ANNUAL_CLOSURE_UNKNOWN_VALID_ANNUAL_SUBMISSION_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING":
        raise ValueError("TASK240 prior receipt historical state drift")
    if prior_proof.get("LIMEIRA_2025_ANNUAL_RECEIPT_NUMBER") != "428477-6" or prior_proof.get("SUCCESSFUL_ANNUAL_DELIVERY") != "PROVEN_OFFICIAL_RECEIPT" or prior_proof.get("VALID_ANNUAL_SUBMISSION") != "PROVEN" or prior_proof.get("CURRENTLY_EFFECTIVE_DECLARATION") != "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING":
        raise ValueError("TASK240 prior receipt proof drift")

    pinned = evidence.get("pinned_limeira_receipt_evidence", {})
    if (pinned.get("source_path") != "docs/evidence/TASK_010N_R_E_M7_SIOPE_2025_LIMEIRA_ANNUAL_RECEIPT_EFFECTIVE_DECLARATION_0.8.0.json" or pinned.get("observation_date") != "2026-08-30" or pinned.get("receipt_number") != "428477-6" or pinned.get("successful_delivery") != "PROVEN_OFFICIAL_RECEIPT" or pinned.get("valid_annual_submission") != "PROVEN"):
        raise ValueError("TASK240 pinned Limeira receipt drift")

    application = evidence.get("deterministic_application", {})
    if application.get("currently_effective_declaration_at_pinned_observation") != "PROVEN_RECEIPT_428477-6" or application.get("temporal_boundary") != "PINNED_OBSERVATION_2026-08-30" or application.get("immutable_finality") != "NOT_ASSERTED_AND_NOT_REQUIRED" or application.get("future_successful_rectification_effect") != "SUPERSEDES_PRIOR_DECLARATION_AND_REQUIRES_REFRESH":
        raise ValueError("TASK240 deterministic application drift")

    b3 = evidence.get("b3_decision", {})
    if (b3.get("old_state") != "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING" or b3.get("new_state") != EXPECTED_B3 or b3.get("selection_rule_proven") is not True or b3.get("pinned_limeira_effective_declaration_proven") is not True or b3.get("future_state_can_change_after_successful_rectification") is not True or b3.get("blocker_removed") is not True):
        raise ValueError("TASK240 B3 decision drift")

    expected_release = {
        "B1_NUM_POPU": "RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS",
        "B2_FINANCIAL_ALIAS_BRIDGE": "PROVEN_10_OF_10_ALIAS_TO_CONCEPT",
        "B3_EFFECTIVE_ANNUAL_DECLARATION": EXPECTED_B3,
        "semantic_comparability_2016_2025": "UNKNOWN_REQUIRES_SEPARATE_GATE",
        "annual_closure_status": "EFFECTIVE_DECLARATION_PROVEN_COMPARABILITY_PENDING",
        "closed_annual_series": "2016-2024",
        "gold_2025": "BLOCKED_NOT_CALCULATED",
        "release_0_8_0": "CANDIDATE",
        "automatic_release_promotion": False,
    }
    if evidence.get("release_gate_effect", {}) != expected_release:
        raise ValueError("TASK240 release gate effect drift")

    guards = evidence.get("guards", {})
    required_false = ("raw_fnde_pdf_committed","historical_task011_rewritten","historical_m7_receipt_evidence_rewritten","immutable_finality_inferred","future_rectification_ignored","semantic_comparability_inferred_from_b3","gold_2025_computed","release_promoted","remote_source_collection","drive_write","schedule_or_recurrence")
    if any(guards.get(key) is not False for key in required_false):
        raise ValueError("TASK240 guard drift")
    if evidence.get("next_gate") != "SEMANTIC_COMPARABILITY_2016_2025":
        raise ValueError("TASK240 next gate drift")
    return EXPECTED_DECISION


def validate():
    intake_status = TASK016.validate(INTAKE)
    return validate_objects(load(EVIDENCE), load(INTAKE), load(PRIOR), intake_status)


def main():
    print(validate())


if __name__ == "__main__":
    main()
