#!/usr/bin/env python3
"""Deterministic T0 validator for human-prepared, sanitized FNDE intake evidence."""
import argparse
from datetime import date
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/fnde_authoritative_response_intake.v1.json"
PENDING_PATH = ROOT / "docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json"
REQUIRED_FIELDS = {"schema","task","tier","blocker_id","protocol","authority","response_received","received_date","source_class","raw_artifact_sha256","raw_artifact_bytes","raw_artifact_mime","raw_artifact_committed","sanitization_status","authority_provenance_status","provenance_basis","provenance_checks","protocol_identity_match","proposition_assessments","overall_intake_status","promotion_performed","canonical_state","fixture_disclaimer"}
ASSESSMENT_FIELDS = {"proposition_index","target_proposition","assessment","support_type","sanitized_support_excerpt","support_location","assessment_note"}
UNSAFE = [
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)"),
    re.compile(r"(?i)\b(?:bearer|authorization)\s*[:= ]\s*\S+"),
    re.compile(r"(?i)\b(?:refresh[_ -]?token|access[_ -]?token|client[_ -]?secret|session(?:id)?|cookie)\b\s*[:=]\s*\S+")]

def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)

def validate_pending(contract, pending):
    identity = (pending.get("schema"),pending.get("task"),pending.get("tier"),pending.get("request_date"),pending.get("authority"),pending.get("deadline"),pending.get("decision"))
    if identity != ("TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_V1","TASK_011","T0_OFFLINE","2026-08-30","FNDE","2026-09-21","KEEP_B1_B2_B3_PENDING_NO_PROMOTION"):
        raise ValueError("TASK 011 identity/state drift")
    expected = contract["requests"]
    if len(pending.get("requests", [])) != len(expected): raise ValueError("TASK 011 request count drift")
    for actual, wanted in zip(pending["requests"], expected):
        for key in ("blocker_id","protocol","current_blocker_state","target_propositions"):
            if actual.get(key) != wanted[key]: raise ValueError(f"TASK 011 {key} drift")
        if actual.get("response_status") != "PENDING" or actual.get("promotion_effect") != "NONE_WHILE_PENDING": raise ValueError("TASK 011 no longer pending")
    for key, value in pending["canonical_state"].items():
        if contract["canonical_no_promotion_state"].get(key) != value: raise ValueError(f"canonical state drift: {key}")

def status_for(data, contract):
    if set(data) != REQUIRED_FIELDS: return "STOP_PROPOSITION_MAPPING_DRIFT"
    if data["schema"] != contract["intake_schema"] or data["task"] != "TASK_016" or data["tier"] != "T0_OFFLINE" or data["authority"] != "FNDE": return "STOP_BLOCKER_MISMATCH"
    requests = {item["blocker_id"]: item for item in contract["requests"]}
    if data["blocker_id"] not in requests: return "STOP_BLOCKER_MISMATCH"
    request = requests[data["blocker_id"]]
    if data["protocol"] != request["protocol"] or data["protocol_identity_match"] is not True: return "STOP_PROTOCOL_MISMATCH"
    if data["promotion_performed"] is not False or data["canonical_state"] != contract["canonical_no_promotion_state"]: return "STOP_FORBIDDEN_PROMOTION"
    if type(data["response_received"]) is not bool: return "STOP_INVALID_INTAKE_METADATA"
    if data["response_received"] is False: return "STOP_NO_RESPONSE"
    received_date = data["received_date"]
    if type(received_date) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", received_date): return "STOP_INVALID_INTAKE_METADATA"
    try:
        if date.fromisoformat(received_date).isoformat() != received_date: return "STOP_INVALID_INTAKE_METADATA"
    except ValueError:
        return "STOP_INVALID_INTAKE_METADATA"
    if data["raw_artifact_committed"] is not False: return "STOP_UNSAFE_PUBLIC_EVIDENCE"
    public_text = "\n".join(
        str(value)
        for value in [data.get("provenance_basis", "")]
        + [item.get(key, "") for item in data.get("proposition_assessments", []) for key in ("sanitized_support_excerpt", "support_location", "assessment_note")]
    )
    if any(pattern.search(public_text) for pattern in UNSAFE): return "STOP_UNSAFE_PUBLIC_EVIDENCE"
    if (not re.fullmatch(r"[0-9a-f]{64}", str(data["raw_artifact_sha256"])) or type(data["raw_artifact_bytes"]) is not int or data["raw_artifact_bytes"] <= 0 or not re.fullmatch(r"[\w.+-]+/[\w.+-]+", str(data["raw_artifact_mime"]))): return "STOP_INVALID_ARTIFACT_METADATA"
    if data["authority_provenance_status"] not in contract["allowed_provenance_states"]: return "STOP_PROVENANCE_INCOMPLETE"
    synthetic = data["source_class"] == "SYNTHETIC_FIXTURE"
    checks = data["provenance_checks"]
    if type(checks) is not dict or set(checks) != set(contract["provenance_check_fields"]): return "STOP_PROVENANCE_INCOMPLETE"
    if synthetic:
        synthetic_checks = {"handoff_mode":"SYNTHETIC_TEST_CONSTRUCTION","authority_label_observed":False,"protocol_observed":data["protocol"],"raw_artifact_hash_verified":False,"human_offline_review_completed":True}
        if data["authority_provenance_status"] != "SYNTHETIC_NOT_AUTHORITATIVE" or data["fixture_disclaimer"] != ["SYNTHETIC","NOT FROM FNDE","NO REAL PERSONAL DATA","NO PROMOTION EFFECT"] or checks != synthetic_checks: return "STOP_PROVENANCE_INCOMPLETE"
    else:
        if data["fixture_disclaimer"] != []: return "STOP_UNSAFE_PUBLIC_EVIDENCE"
        proven_checks = {"handoff_mode":"USER_MEDIATED_OFFICIAL_RESPONSE","authority_label_observed":True,"protocol_observed":data["protocol"],"raw_artifact_hash_verified":True,"human_offline_review_completed":True}
        if data["authority_provenance_status"] != "AUTHORITATIVE_PROVEN" or type(data["provenance_basis"]) is not str or not data["provenance_basis"].strip() or checks != proven_checks: return "STOP_PROVENANCE_INCOMPLETE"
    if data["source_class"] not in contract["allowed_source_classes"] or data["sanitization_status"] != "SANITIZED_FOR_PUBLIC_REPOSITORY": return "STOP_PROVENANCE_INCOMPLETE"
    assessments = data["proposition_assessments"]
    if len(assessments) != len(request["target_propositions"]): return "STOP_PROPOSITION_MAPPING_DRIFT"
    for index, (assessment, target) in enumerate(zip(assessments, request["target_propositions"]), 1):
        if set(assessment) != ASSESSMENT_FIELDS or assessment["proposition_index"] != index or assessment["target_proposition"] != target: return "STOP_PROPOSITION_MAPPING_DRIFT"
        if assessment["assessment"] not in contract["allowed_proposition_assessments"] or assessment["support_type"] not in contract["allowed_support_types"]: return "STOP_PROPOSITION_MAPPING_DRIFT"
        excerpt = assessment["sanitized_support_excerpt"]
        if len(excerpt) > contract["max_support_excerpt_characters"]: return "STOP_UNSAFE_PUBLIC_EVIDENCE"
    states = [item["assessment"] for item in assessments]
    if "CONTRADICTORY" in states: return "INTAKE_RECEIVED_CONTRADICTORY"
    if "AMBIGUOUS" in states: return "INTAKE_RECEIVED_AMBIGUOUS"
    if all(state == "PROVEN_EXPLICIT" for state in states): return "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW"
    return "INTAKE_RECEIVED_INCOMPLETE"

def validate(path):
    contract, pending, data = load(CONTRACT_PATH), load(PENDING_PATH), load(path)
    validate_pending(contract, pending)
    result = status_for(data, contract)
    if data.get("overall_intake_status") != result: raise ValueError(f"declared status mismatch: expected {result}")
    return result

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("intake", type=Path); args = parser.parse_args()
    print(validate(args.intake))

if __name__ == "__main__": main()
