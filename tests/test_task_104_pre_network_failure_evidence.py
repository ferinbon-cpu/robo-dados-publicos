from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_104_PRE_NETWORK_FAILURE_0.8.0.json"
AUTH = ROOT / "docs/evidence/TASK_104_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
HISTORICAL_WORKFLOW = (
    ROOT
    / "docs/evidence/TASK_104_HISTORICAL_LIVE_WORKFLOW_SOURCE_FAILED_PRE_NETWORK_0.8.0.txt"
)
LIVE_WORKFLOW = ROOT / ".github/workflows/task-104-historical-ppa-live-once.yml"


def test_task104_is_pinned_as_pre_network_failure_only():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["result"] == "STOP_PRE_NETWORK_CAPABILITY_MISSING"
    assert evidence["failure"]["pdftotext_present"] is False
    assert evidence["failure"]["live_runner_invoked"] is False
    assert evidence["source_effects"]["official_source_http_requests_emitted"] == 0
    assert evidence["source_effects"]["primary_source_bytes_read"] == 0
    assert evidence["source_effects"]["source_read_scope_consumed"] is False
    assert evidence["epistemic_state"]["historical_ppa_primary_gap_closed"] is False
    assert evidence["epistemic_state"]["financial_identity_created"] is False
    assert evidence["epistemic_state"]["causal_effect_created"] is False


def test_task104_owner_record_distinguishes_workflow_from_source_scope():
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    assert (
        auth["status"]
        == "WORKFLOW_ATTEMPT_CONSUMED_PRE_NETWORK_SOURCE_READ_SCOPE_UNCONSUMED"
    )
    consumed = auth["consumed_by"]
    assert consumed["run_id"] == 33911282395
    assert consumed["job_id"] == 101148033981
    assert consumed["workflow_single_use_consumed"] is True
    assert consumed["source_read_scope_consumed"] is False
    assert consumed["source_http_requests_emitted"] == 0
    assert consumed["live_runner_invoked"] is False


def test_task104_consumed_live_workflow_is_removed_but_source_preserved():
    assert not LIVE_WORKFLOW.exists()
    source = HISTORICAL_WORKFLOW.read_text(encoding="utf-8")
    assert "task-104-historical-ppa-live-once.yml" in source
    assert "Verify local PDF text extractor without installing anything" in source
    assert "schedule:" not in source
    assert "workflow_dispatch:" not in source
    assert "contents: write" not in source
    assert "secrets: inherit" not in source


def test_task104_does_not_authorize_rerun():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["workflow_state"]["rerun_authorized"] is False
    assert evidence["next_boundary"].startswith("NEW_TASK_NEW_SINGLE_USE_WORKFLOW")
