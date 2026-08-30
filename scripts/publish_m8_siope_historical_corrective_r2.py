#!/usr/bin/env python3
"""Manual TASK 012 corrective R2 gate; dry-run is strictly offline."""
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
from robo_dados_publicos.product.siope_historical_corrective_publication import (
    ERROR, PASS_DRY_RUN, dry_run_result, execute_corrective_publication, prepare_source,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider


def _failure(code: str, created_count: int = 0) -> tuple[dict, int]:
    return ({
        "status": code, "created_count": created_count,
        "partial_sheet_created": created_count == 1,
        "pdf_created": created_count >= 2, "completion_manifest_created": created_count >= 3,
        "retry_performed": False, "automatic_cleanup_performed": False,
        "owner_decision_required": created_count > 0,
        "remote_identifiers_exposed": False, "secret_values_exposed": False,
    }, 16)


def run_gate(source_zip: str | Path, *, owner_authorized: bool, dry_run: bool) -> tuple[dict, int]:
    if owner_authorized is not True:
        return _failure(f"{ERROR}_EXPLICIT_EXECUTION_AUTHORIZATION_REQUIRED")
    try:
        if dry_run:
            with tempfile.TemporaryDirectory(prefix="m8-corrective-dryrun-") as raw:
                _bundle, matrix, source = prepare_source(root=ROOT, source_zip=source_zip, work_dir=raw)
                result = dry_run_result(matrix, source)
                if result["status"] != PASS_DRY_RUN:
                    return _failure(f"{ERROR}_DRY_RUN_STATUS")
                return result, 0
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))
        return execute_corrective_publication(
            drive, root=ROOT, source_zip=source_zip,
            published_at=datetime.now(timezone.utc).isoformat(),
        ), 0
    except ProductPublicationError as exc:
        return _failure(str(exc), getattr(exc, "created_count", 0))
    except RuntimeError:
        return _failure(f"{ERROR}_RUNTIME")
    except Exception:
        return _failure(f"{ERROR}_UNEXPECTED")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result, code = run_gate(args.artifact_zip, owner_authorized=args.owner_authorized, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
