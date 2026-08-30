#!/usr/bin/env python3
"""Manual TASK 014 corrective R3 gate; dry-run is strictly offline."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.product.publication import ProductPublicationError
from robo_dados_publicos.product.siope_historical_corrective_r3_publication import (
    ERROR, PASS_DRY_RUN, dry_run_result, execute_corrective_publication, prepare_source,
    validate_live_authorization,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider


def _failure(code: str, created_count: int = 0, *, error=None) -> tuple[dict, int]:
    result = {
        "status": code, "created_count": created_count,
        "partial_sheet_created": created_count == 1,
        "pdf_created": created_count >= 2, "completion_manifest_created": created_count >= 3,
        "retry_performed": False, "automatic_cleanup_performed": False,
        "owner_decision_required": created_count > 0,
        "remote_identifiers_exposed": False, "secret_values_exposed": False,
        "remote_stage": getattr(error, "remote_stage", None),
        "remote_operation_class": getattr(error, "remote_operation_class", None),
        "error_type": getattr(error, "error_type", None),
        "http_status_if_safe": getattr(error, "http_status_if_safe", None),
        "retryable": False,
    }
    return (result, 16)


def run_gate(source_zip: str | Path, *, owner_authorized: bool, dry_run: bool, execution_sha: str = "") -> tuple[dict, int]:
    if not dry_run and owner_authorized is not True:
        return _failure(f"{ERROR}_EXPLICIT_EXECUTION_AUTHORIZATION_REQUIRED")
    try:
        if dry_run:
            with tempfile.TemporaryDirectory(prefix="m8-corrective-dryrun-") as raw:
                _bundle, matrix, source = prepare_source(root=ROOT, source_zip=source_zip, work_dir=raw)
                result = dry_run_result(matrix, source)
                if result["status"] != PASS_DRY_RUN:
                    return _failure(f"{ERROR}_DRY_RUN_STATUS")
                return result, 0
        # Repository-pinned post-merge authorization is checked before even
        # reading OAuth environment values. The execution gate checks it again.
        validate_live_authorization(root=ROOT, execution_sha=execution_sha)
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))
        return execute_corrective_publication(
            drive, root=ROOT, source_zip=source_zip,
            published_at=datetime.now(timezone.utc).isoformat(),
            execution_sha=execution_sha,
        ), 0
    except ProductPublicationError as exc:
        return _failure(str(exc), getattr(exc, "created_count", 0), error=exc)
    except RuntimeError:
        return _failure(f"{ERROR}_RUNTIME")
    except Exception:
        return _failure(f"{ERROR}_UNEXPECTED")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execution-sha", default="")
    parser.add_argument("--validate-live-authorization", action="store_true")
    args = parser.parse_args()
    if args.validate_live_authorization:
        try:
            authorization = validate_live_authorization(root=ROOT, execution_sha=args.execution_sha)
            print(json.dumps({
                "status": "PASS_TASK_014_OWNER_AUTHORIZATION",
                "authorized_implementation_sha": authorization["repository_boundary"]["authorized_implementation_sha"],
                "execution_sha": args.execution_sha,
                "authorization_only_diff": True,
            }))
            return 0
        except ProductPublicationError as exc:
            result, code = _failure(str(exc))
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return code
    result, code = run_gate(
        args.artifact_zip, owner_authorized=args.owner_authorized, dry_run=args.dry_run,
        execution_sha=args.execution_sha,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
