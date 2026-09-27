#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.task247_jom_rolling_discovery import load_config, validate_offline_carrier

CONFIG = ROOT / "config/task247_jom_rolling_discovery.v1.json"
WORKFLOW = ROOT / ".github/workflows/task247_jom_rolling_discovery.yml"
TASK_DOC = ROOT / "docs/tasks/TASK_247_JOM_ROLLING_DISCOVERY.md"
EVIDENCE = ROOT / "docs/evidence/TASK_247_JOM_ROLLING_DISCOVERY_CARRIER_0.8.0.json"


def req(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def run() -> dict:
    cfg = load_config(CONFIG)
    result = validate_offline_carrier(CONFIG)
    req(result["status"] == "PASS", "STOP_TASK247_OFFLINE_CARRIER")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    task_doc = TASK_DOC.read_text(encoding="utf-8")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    req("task-247-jom-rolling-discovery-runtime" in workflow, "STOP_TASK247_RUNTIME_BRANCH")
    req("runtime_triggers/task247_jom_rolling_discovery.run" in workflow, "STOP_TASK247_TRIGGER_PATH")
    req("permissions:\n  contents: read" in workflow, "STOP_TASK247_PERMISSIONS")
    req("persist-credentials: false" in workflow, "STOP_TASK247_PERSIST_CREDENTIALS")
    req("schedule:" not in workflow, "STOP_TASK247_SCHEDULE_TRIGGER")
    req("workflow_dispatch:" not in workflow, "STOP_TASK247_UNPINNED_MANUAL_DISPATCH")
    req("pull_request:" not in workflow, "STOP_TASK247_PR_LIVE_TRIGGER")
    req("branches:\n      - task-247-jom-rolling-discovery-runtime" in workflow, "STOP_TASK247_BRANCH_SCOPE")
    req("runtime/task247_owner_authorization.json" in workflow, "STOP_TASK247_AUTH_FILE")
    req("TASK247_IMPLEMENTATION_SHA" in workflow, "STOP_TASK247_SHA_BINDING")
    req("task247_sanitized_discovery_result.json" in workflow, "STOP_TASK247_SANITIZED_OUTPUT")
    req("retention-days: 1" in workflow, "STOP_TASK247_RETENTION")
    req("secrets." not in workflow, "STOP_TASK247_SECRET_BINDING")

    auth = cfg["authorization"]
    req(auth["recurrence_authorized"] is False, "STOP_TASK247_RECURRENCE_AUTH")
    req(auth["schedule_authorized"] is False, "STOP_TASK247_SCHEDULE_AUTH")
    req(auth["drive_write_authorized"] is False, "STOP_TASK247_DRIVE_AUTH")
    req(auth["serving_authorized"] is False, "STOP_TASK247_SERVING_AUTH")
    req(auth["publication_authorized"] is False, "STOP_TASK247_PUBLICATION_AUTH")
    req(cfg["discovery"]["document_downloads"] == 0, "STOP_TASK247_PDF_BOUND")
    req(cfg["baseline"]["total_document_count"] == 99, "STOP_TASK247_BASELINE_TOTAL")
    req(cfg["baseline"]["through_date"] == "2026-09-08", "STOP_TASK247_BASELINE_DATE")
    req(cfg["scope"]["start_date"] == "2026-09-09" and cfg["scope"]["end_date"] == "2026-09-16", "STOP_TASK247_DELTA_WINDOW")

    req(evidence.get("status") == "OFFLINE_CARRIER_READY_LIVE_BLOCKED", "STOP_TASK247_EVIDENCE_STATUS")
    req(evidence.get("baseline", {}).get("canonical_document_count") == 99, "STOP_TASK247_EVIDENCE_BASELINE")
    req(evidence.get("remote_effects", {}).get("source_network") is False, "STOP_TASK247_EVIDENCE_NETWORK")
    req(evidence.get("remote_effects", {}).get("drive_write") is False, "STOP_TASK247_EVIDENCE_DRIVE")
    req(evidence.get("remote_effects", {}).get("schedule") is False, "STOP_TASK247_EVIDENCE_SCHEDULE")
    req(evidence.get("remote_effects", {}).get("recurrence") is False, "STOP_TASK247_EVIDENCE_RECURRENCE")
    req("TASK217C" in task_doc and "99" in task_doc and "09/09/2026" in task_doc, "STOP_TASK247_TASK_DOC")

    return {
        "status": "PASS_TASK247_ROLLING_DISCOVERY_CARRIER_OFFLINE",
        "issue": 821,
        "baseline_total": 99,
        "baseline_through": "2026-09-08",
        "delta_window": ["2026-09-09", "2026-09-16"],
        "max_remote_get_count": 10,
        "live_source_network": False,
        "document_downloads": 0,
        "drive_write": False,
        "serving_write": False,
        "publication": False,
        "promotion": False,
        "schedule": False,
        "recurrence": False,
        "live_authorization_required": True,
    }


def main() -> int:
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_TASK247_ROLLING_DISCOVERY_CARRIER_OFFLINE", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 47
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
