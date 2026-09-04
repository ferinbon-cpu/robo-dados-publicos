from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_089_BOUNDED_NEXT_EXECUTABLE_CONTRACT_QUERY_0.8.0.json"
HISTORICAL = ROOT / "docs/evidence/TASK_089_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE_WORKFLOW = ROOT / ".github/workflows/task-089-contract-resolver-live-once.yml"


def _load():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_task089_single_use_execution_is_consumed_and_closed():
    e = _load()
    auth = e["authorization"]
    assert auth["single_execution"] is True
    assert auth["consumed"] is True
    assert auth["retry_authorized"] is False
    assert auth["future_execution_authorized"] is False
    assert e["pre_run_chain"]["workflow_removed_after_run"] is True
    assert not LIVE_WORKFLOW.exists()


def test_task089_remote_budget_and_result_are_bounded():
    e = _load()
    assert e["live_run"]["conclusion"] == "success"
    assert e["live_run"]["resolver_status"] == "NO_MATCH"
    assert e["live_run"]["candidate_count"] == 0
    assert e["live_run"]["request_count"] == 3
    assert e["remote_budget"] == {
        "maximum_http_requests": 3,
        "actual_http_requests": 3,
        "same_origin_only": True,
        "allowed_host": "serv42.limeira.sp.gov.br",
        "fourth_request_fail_closed": True,
    }
    assert [r["method"] for r in e["observed_request_shape"]] == ["GET", "POST", "POST"]


def test_task089_historical_workflow_pins_exact_scope_and_no_recurring_trigger():
    text = HISTORICAL.read_text(encoding="utf-8")
    assert "task-089-next-executable-contract-bounded-query" in text
    assert "RECTASK_bf460d6fbffa22124902553f" in text
    assert 'ALLOWED_HOST = "serv42.limeira.sp.gov.br"' in text
    assert "MAX_REQUESTS = 3" in text
    assert "schedule:" not in text
    assert "workflow_dispatch:" not in text
    assert "repository_dispatch:" not in text
    assert "workflow_run:" not in text


def test_task089_promotes_no_identity_and_preserves_next_state():
    e = _load()
    assert e["semantic_interpretation"]["contract_identity_asserted"] is False
    assert e["semantic_interpretation"]["financial_identity_asserted"] is False
    assert e["semantic_interpretation"]["global_absence_outside_this_bounded_query_asserted"] is False
    assert e["next_state"]["raw_blocked_task_preserved"] == "RECTASK_78d06bc26f825243c23375c6"
    assert e["next_state"]["next_executable_candidate"] == "RECTASK_9060935fe5220f738bddfdb4"
    assert e["next_state"]["future_execution_authorized"] is False
