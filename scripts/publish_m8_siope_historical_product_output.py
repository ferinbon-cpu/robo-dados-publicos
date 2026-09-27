#!/usr/bin/env python3
"""Execute the first authorized M8 SIOPE historical product publication.

The source is the exact pinned GitHub Actions artifact from the proven T1
read-only run. No source collection, Gold processing, reconciliation, retry,
pagination or scheduling happens in this gate.
"""

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
from robo_dados_publicos.product.siope_historical_publication_gate import (
    ERROR,
    M8HistoricalPublicationGateError,
    PASS_DRY_RUN,
    dry_run_result,
    execute_publication,
    prepare_publication_source,
)
from robo_dados_publicos.product.siope_historical_publication_review import (
    SiopeHistoricalPublicationReviewError,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider


def _stop(code: str, *, created_count: int = 0) -> tuple[dict, int]:
    return {
        "status": code,
        "created_count": created_count,
        "partial_write_possible": created_count > 0,
        "remote_identifiers_exposed": False,
        "secret_values_exposed": False,
        "future_batch_execution_authorized": False,
    }, 16


def run_gate(
    source_zip: str | Path,
    *,
    owner_authorized: bool,
    dry_run: bool = False,
) -> tuple[dict, int]:
    if owner_authorized is not True:
        return _stop(f"{ERROR}_OWNER_AUTHORIZATION_REQUIRED")
    try:
        if dry_run:
            with tempfile.TemporaryDirectory(prefix="m8-siope-publication-dryrun-") as raw:
                _bundle, source = prepare_publication_source(
                    root=ROOT,
                    source_zip=source_zip,
                    work_dir=Path(raw),
                )
                result = dry_run_result(source=source)
                if result.get("status") != PASS_DRY_RUN:
                    return _stop(f"{ERROR}_DRY_RUN_STATUS")
                return result, 0

        credentials = OAuthCredentials.from_env()
        drive = DriveRESTClient(TokenProvider(credentials))
        result = execute_publication(
            drive,
            root=ROOT,
            source_zip=source_zip,
            published_at=datetime.now(timezone.utc).isoformat(),
        )
        return result, 0
    except ProductPublicationError as exc:
        return _stop(exc.code, created_count=exc.created_count)
    except M8HistoricalPublicationGateError as exc:
        return _stop(str(exc))
    except SiopeHistoricalPublicationReviewError as exc:
        return _stop(str(exc))
    except RuntimeError:
        # OAuth/bootstrap runtime errors are deliberately sanitized.
        return _stop(f"{ERROR}_RUNTIME")
    except Exception:
        return _stop(f"{ERROR}_UNEXPECTED")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--owner-authorized", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload, code = run_gate(
        args.artifact_zip,
        owner_authorized=args.owner_authorized,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
