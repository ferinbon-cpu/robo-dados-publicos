from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_106_PRE_NETWORK_FAILURE_0.8.0.json"
AUTH = ROOT / "docs/evidence/TASK_106_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
LIVE_WORKFLOW = ROOT / ".github/workflows/task-106-historical-ppa-live-once.yml"


def test_task106_failure_is_pinned_as_pre_network_and_non_promoting():
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert data["result"] == "STOP_PRE_NETWORK_RUNNER_IMPORT_BOOTSTRAP"
    assert data["source_effects"]["official_source_http_requests_emitted"] == 0
    assert data["source_effects"]["primary_source_bytes_read"] == 0
    assert data["source_effects"]["source_read_scope_consumed"] is False
    assert data["workflow_state"]["single_use_trigger_consumed"] is True
    assert data["workflow_state"]["rerun_authorized"] is False
    assert all(value is False for value in data["epistemic_state"].values())


def test_task106_authorization_distinguishes_workflow_consumption_from_source_scope():
    data = json.loads(AUTH.read_text(encoding="utf-8"))
    assert data["status"] == "WORKFLOW_ATTEMPT_CONSUMED_PRE_NETWORK_SOURCE_READ_SCOPE_UNCONSUMED"
    assert data["consumed_by"]["parser_preflight_passed"] is True
    assert data["consumed_by"]["live_runner_import_completed"] is False
    assert data["consumed_by"]["source_http_requests_emitted"] == 0
    assert data["consumed_by"]["source_read_scope_consumed"] is False
    assert data["consumed_by"]["workflow_single_use_consumed"] is True


def test_task106_live_workflow_is_removed_before_merge():
    assert not LIVE_WORKFLOW.exists()
