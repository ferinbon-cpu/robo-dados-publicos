#!/usr/bin/env python3
"""Fail-closed offline gate for TASK249 bounded JOM PDF acquisition."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.task249_jom_bounded_pdf_acquisition import (
    load_config,
    load_queue,
    validate_config,
    validate_live_authorization,
)


def main() -> int:
    config = load_config(ROOT / "config/task249_jom_bounded_pdf_acquisition.v1.json")
    queue = load_queue(ROOT / "config/task248_jom_bounded_ingestion_queue.v1.json")
    evidence = json.loads(
        (ROOT / "docs/evidence/TASK_249_JOM_BOUNDED_PDF_ACQUISITION_CARRIER_0.8.0.json").read_text(encoding="utf-8")
    )
    workflow = (ROOT / ".github/workflows/task249_jom_bounded_pdf_acquisition.yml").read_text(encoding="utf-8")
    validation = validate_config(config, queue)
    missing_auth = validate_live_authorization(None, expected_sha="0" * 40)
    checks = {
        "config_pass": validation["status"] == "PASS_TASK249_CONFIG",
        "exact_scope": config["scope"]["editions"] == [7321, 7322, 7323, 7324],
        "source_get_budget": config["limits"]["max_source_gets"] == 4,
        "no_retry_redirect_fallback": (
            config["limits"]["automatic_retry"] is False
            and config["limits"]["redirects"] is False
            and config["limits"]["alternate_url_discovery"] is False
        ),
        "sanitized_only": (
            config["persistence"]["sanitized_result_artifact"] is True
            and config["persistence"]["raw_pdf_artifact"] is False
            and config["persistence"]["raw_pdf_repository"] is False
            and config["persistence"]["drive_write"] is False
        ),
        "live_auth_absent_stops": missing_auth["status"] == "STOP_TASK249_LIVE_NOT_AUTHORIZED",
        "carrier_is_pre_live": (
            evidence["live_execution_performed"] is False
            and evidence["source_hashes_known"] is False
            and evidence["source_page_counts_known"] is False
        ),
        "runtime_branch_pinned": "task-249-jom-bounded-pdf-acquisition-runtime" in workflow,
        "trigger_path_pinned": "runtime_triggers/task249_jom_bounded_pdf_acquisition.run" in workflow,
        "workflow_no_schedule": "schedule:" not in workflow,
        "workflow_no_dispatch": "workflow_dispatch" not in workflow,
        "workflow_no_pr_trigger": "pull_request" not in workflow,
        "workflow_no_secrets": "secrets." not in workflow,
        "artifact_one_day": "retention-days: 1" in workflow,
        "artifact_json_only": (
            "runtime_out/task249_sanitized_pdf_acquisition_result.json" in workflow
            and "path: runtime_out/task249_sanitized_pdf_acquisition_result.json" in workflow
        ),
    }
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({
        "status": "PASS_TASK249_BOUNDED_PDF_ACQUISITION_IMPLEMENTATION_OFFLINE" if not failed else "STOP",
        "checks": checks,
        "failed_checks": failed,
    }, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
