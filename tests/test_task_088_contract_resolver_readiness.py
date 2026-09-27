from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_088_CONTRACT_RESOLVER_READINESS_0.8.0.json"


def _task(candidate: dict) -> dict:
    keys = {"year": candidate["year"]}
    for key in ("cnpj", "contract_number", "contractor"):
        if candidate.get(key):
            keys[key] = candidate[key]
    return {
        "task_id": candidate["task_id"],
        "target_source": "LIMEIRA_CONTRATOS",
        "match_keys": keys,
    }


def test_task088_readiness_matches_current_resolver_contract():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    candidates = evidence["candidates_in_plan_order"]

    observed = [
        LimeiraContractsResolver.has_minimum_search_key(_task(candidate))
        for candidate in candidates
    ]
    assert observed == [False, True, True]
    assert candidates[0]["routing"] == "BLOCKED_CONNECTOR_DISCOVERY_NOT_CONSUMED"
    assert candidates[1]["routing"] == "NEXT_EXECUTABLE"
    assert candidates[2]["routing"] == "EXECUTABLE_AFTER_CURRENT_NEXT"
    assert evidence["next_executable_task_id"] == candidates[1]["task_id"]


def test_task088_does_not_promote_cnpj_object_process_or_edital_into_primary_query_key():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    policy = evidence["readiness_policy"]
    assert policy["permitted_primary_query_keys"] == ["contract_number", "contractor"]
    assert set(policy["corroborating_only"]) == {"cnpj", "object_text", "process_number", "edital_number"}
    assert policy["broad_object_or_cnpj_only_query_forbidden"] is True

    ineligible = evidence["candidates_in_plan_order"][0]
    task = _task(ineligible)
    assert task["match_keys"] == {"year": 2025, "cnpj": "29494115000161"}
    assert LimeiraContractsResolver.has_minimum_search_key(task) is False


def test_task088_is_offline_and_preserves_unresolved_task():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["source_plan"]["new_drive_reads"] == 0
    assert all(value == 0 for value in evidence["hard_boundaries"].values())
    assert evidence["authorization"]["live_municipal_query_authorized_by_this_task"] is False
    assert evidence["next_gate_candidate"]["authorized_by_task088"] is False
