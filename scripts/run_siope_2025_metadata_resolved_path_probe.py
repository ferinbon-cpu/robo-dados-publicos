#!/usr/bin/env python3
"""Run TASK 009C only after exact separately merged one-shot authorization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_2025_metadata_resolved_path_probe import (
    AUTH_PATH,
    MetadataResolvedPathProbe,
    MetadataResolvedPathProbeError,
    validate_authorization_document,
)

PREPARATION = ROOT / "config" / "siope_2025_metadata_resolved_path_probe_preparation.v1.json"
ACTUAL_AUTH = ROOT / AUTH_PATH


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"OBJECT_REQUIRED:{path.name}")
    return value


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _git_state(base_sha: str) -> tuple[str, str, list[str]]:
    head = _git("rev-parse", "HEAD")
    parent = _git("rev-parse", "HEAD^")
    paths = [line for line in _git("diff", "--name-only", f"{base_sha}..HEAD").splitlines() if line]
    return head, parent, sorted(paths)


def _emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "live"], required=True)
    parser.add_argument("--authorization-id")
    parser.add_argument("--workflow-run-number", type=int)
    parser.add_argument("--workflow-run-attempt", type=int)
    parser.add_argument("--workflow-ref")
    args = parser.parse_args()

    if args.mode == "dry-run":
        _emit({
            "status": "PASS_TASK009C_RESOLVED_PATH_PROBE_DRY_RUN_NO_NETWORK",
            "source_get_count": 0,
            "live_execution_authorized": False,
            "follow_redirects": False,
            "maximum_future_probe_get_count": 1,
            "annual_closure_status": "UNKNOWN",
            "semantic_comparability_status": "UNKNOWN",
            "gold_metrics_status": "UNKNOWN",
        })
        return 0

    if not ACTUAL_AUTH.exists():
        _emit({"status": "STOP_METADATA_RESOLVED_PATH_PROBE_NOT_AUTHORIZED", "source_get_count": 0})
        return 13
    if not args.authorization_id or not args.workflow_run_number or not args.workflow_run_attempt or not args.workflow_ref:
        _emit({"status": "STOP_METADATA_RESOLVED_PATH_PROBE_RUN_IDENTITY_REQUIRED", "source_get_count": 0})
        return 13

    authorization = _load(ACTUAL_AUTH)
    try:
        base_sha = str(authorization.get("authorized_base_sha", ""))
        head, parent, changed = _git_state(base_sha)
        validate_authorization_document(
            authorization,
            requested_authorization_id=args.authorization_id,
            current_head_sha=head,
            current_parent_sha=parent,
            changed_paths_since_base=changed,
            current_workflow_run_number=args.workflow_run_number,
            current_workflow_run_attempt=args.workflow_run_attempt,
            current_workflow_ref=args.workflow_ref,
        )
        observation = MetadataResolvedPathProbe().run()
    except MetadataResolvedPathProbeError as exc:
        _emit({
            "status": "STOP_METADATA_RESOLVED_PATH_PROBE",
            "reason": str(exc),
            "source_get_count": exc.request_count,
            "drive_read_count": 0,
            "drive_write_count": 0,
            "response_persisted": False,
            "archive_persisted": False,
            "publication": False,
        })
        return 13
    except Exception as exc:
        _emit({"status": "STOP_METADATA_RESOLVED_PATH_PROBE_INTERNAL_FAIL_CLOSED", "reason": type(exc).__name__, "source_get_count": 0})
        return 13

    payload = observation.sanitized()
    payload.update({
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "gold_metrics_status": "UNKNOWN",
    })
    if observation.result_kind == "REDIRECT_STOP_REQUIRES_NEW_AUTHORIZATION":
        payload["status"] = "STOP_METADATA_RESOLVED_PATH_REDIRECT_REQUIRES_NEW_AUTHORIZATION"
        _emit(payload)
        return 13
    if not observation.zip_magic_present:
        payload["status"] = "STOP_METADATA_RESOLVED_PATH_ZIP_MAGIC_NOT_OBSERVED"
        _emit(payload)
        return 13
    payload["status"] = "PASS_METADATA_RESOLVED_PATH_PROBE_DIRECT_BOUNDED"
    _emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
