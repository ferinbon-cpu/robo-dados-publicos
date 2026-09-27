from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/evidence/TASK_107_LIVE_RESULT_0.8.0.json"
ARTIFACT = ROOT / "docs/evidence/TASK_107_LIVE_ARTIFACT_READBACK_0.8.0.json"
AUTH = ROOT / "docs/evidence/TASK_107_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
LIVE_WORKFLOW = ROOT / ".github/workflows/task-107-historical-ppa-live-once.yml"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_task107_exact_live_result_is_partial_with_one_primary_match():
    data = load(RESULT)
    assert data["overall_status"] == "PARTIAL_TASK107_ONE_PRIMARY_PPA_MATCH"
    assert data["primary_match_count"] == 1
    assert data["request_count"] == 3
    assert data["result_canonical_sha256"] == "f69259e73b6ce79618ecdea9ef10617fcc3ab123b7fcd7153ae5d379f037252a"
    assert data["retry_performed"] is False
    assert data["recurrence"] is False
    assert data["schedule"] is False
    assert data["future_execution_authorized"] is False
    assert all(value == 0 for value in data["hard_boundaries"].values())


def test_task107_2022_2025_is_primary_planning_evidence_only():
    data = load(RESULT)
    p2022 = next(item for item in data["period_results"] if item["period"] == "2022-2025")
    assert p2022["status"] == "PRIMARY_MATCH"
    assert p2022["source_sha256"] == "8e10123b07d83e9a9928fd2444318f595a7560eac2bc06c920761ca7893778f7"
    assert p2022["source_bytes"] == 3273513
    assert p2022["locator"]["page"] == 23
    assert p2022["locator"]["coordinate_system"] == "SOURCE_PDF_PAGE_1_BASED"
    assert p2022["locator"]["page_text_sha256"] == "6c8294fb4a511fc7fbc86d69dda780085cdc5bbbea363b8482d06c22eba57883"
    assert p2022["financial_identity_created"] is False
    assert p2022["implementation_proven"] is False
    assert p2022["causal_effect_created"] is False


def test_task107_2018_2021_remains_unresolved_after_official_pdf_read():
    data = load(RESULT)
    p2018 = next(item for item in data["period_results"] if item["period"] == "2018-2021")
    assert p2018["status"] == "STOP_REMOTE_ACQUISITION"
    assert p2018["error"] == "TASK106_PDF_TEXT_EMPTY"
    assert p2018["financial_identity_created"] is False
    assert p2018["implementation_proven"] is False
    assert p2018["causal_effect_created"] is False
    requests = [item for item in data["requests"] if item["period"] == "2018-2021"]
    assert len(requests) == 2
    assert requests[1]["path"] == "/sitenovo/downloads/0fa1a5cc5c9a1823fbf5436def00f01f.pdf"


def test_task107_artifact_and_authorization_are_pinned():
    artifact = load(ARTIFACT)
    auth = load(AUTH)
    assert artifact["artifact"]["id"] == 9952715143
    assert artifact["artifact"]["zip_sha256"] == "d8080de70b05453722b1c32f6f9c374c3da9a49408bbc959ed459ebcb5815bb7"
    assert auth["status"] == "WORKFLOW_AND_BOUNDED_SOURCE_READ_CONSUMED_PARTIAL_PRIMARY_EVIDENCE"
    assert auth["consumed_by"]["request_count"] == 3
    assert auth["consumed_by"]["source_read_scope_consumed"] is True
    assert auth["consumed_by"]["workflow_single_use_consumed"] is True
    assert auth["next_execution_authorized"] is False


def test_task107_live_workflow_is_removed_before_merge():
    assert not LIVE_WORKFLOW.exists()
