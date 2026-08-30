#!/usr/bin/env python3
"""Run TASK 013 with the dedicated, exact-scope read-only credential."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.product.m8_r2_forensic_readonly import (  # noqa: E402
    ForensicReadonlyAdapter, run_forensic_readonly,
)
from robo_dados_publicos.product.siope_historical_corrective_publication import prepare_source  # noqa: E402
from robo_dados_publicos.product.siope_historical_publication_gate import output_parent_id  # noqa: E402
from robo_dados_publicos.storage.drive_rest import OAuthCredentials, TokenProvider  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="task-013-canonical-") as work:
            _bundle, matrix, _source = prepare_source(root=ROOT, source_zip=args.artifact_zip, work_dir=work)
        credentials = OAuthCredentials(
            client_id=os.environ["GOOGLE_DRIVE_READONLY_CLIENT_ID"].strip(),
            client_secret=os.environ["GOOGLE_DRIVE_READONLY_CLIENT_SECRET"].strip(),
            refresh_token=os.environ["GOOGLE_DRIVE_READONLY_REFRESH_TOKEN"].strip(),
        )
        result, code = run_forensic_readonly(
            ForensicReadonlyAdapter(TokenProvider(credentials)),
            parent_id=output_parent_id(root=ROOT), canonical_matrix=matrix,
        )
    except Exception as exc:
        result, code = ({
            "schema": "TASK_013_M8_R2_FORENSIC_READONLY_RESULT_V1",
            "status": "STOP_TASK_013_LOCAL_PREFLIGHT_OR_CREDENTIAL",
            "readonly": True, "remote_mutations_performed": 0,
            "retry_performed": False, "cleanup_performed": False,
            "repair_performed": False, "owner_decision_required": True,
            "error_type": type(exc).__name__, "retryable": False,
            "remote_identifiers_exposed": False, "secret_values_exposed": False,
            "forensic_conclusion": "FORENSIC_R2_READ_FAILED",
        }, 22)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "result_path": str(output), "remote_mutations_performed": 0}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
