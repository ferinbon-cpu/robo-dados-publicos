#!/usr/bin/env python3
"""TASK 018 live entry point: authorization/lineage gate before adapters/effects."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json"
ONLY_AUTH_PATH = str(AUTH.relative_to(ROOT))


def preflight() -> tuple[bool, str]:
    auth = json.loads(AUTH.read_text())
    if not auth.get("authorized") or auth.get("status") != "AUTHORIZED" or not auth.get("implementation_merge_sha"):
        return False, "STOP_OWNER_AUTHORIZATION_REQUIRED"
    implementation = auth["implementation_merge_sha"]
    if subprocess.run(["git", "merge-base", "--is-ancestor", implementation, "HEAD"], cwd=ROOT).returncode:
        return False, "STOP_IMPLEMENTATION_SHA_MISMATCH"
    changed = subprocess.check_output(["git", "diff", "--name-only", implementation + "..HEAD"], cwd=ROOT, text=True).splitlines()
    if changed != [ONLY_AUTH_PATH]:
        return False, "STOP_IMPLEMENTATION_SHA_MISMATCH"
    return True, "PASS"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=("T1_DISCOVER_AND_COLLECT", "T2_CREATE_ONLY_PERSIST_AND_PROCESS", "T3_CREATE_ONLY_PRODUCT_PUBLICATION"))
    args = parser.parse_args()
    ok, status = preflight()
    # Adapters are deliberately activated only by a later owner-authorized revision.
    result = {"stage": args.stage, "status": status if not ok else "STOP_CREDENTIAL_CAPABILITY", "effects": {"source_gets": 0, "drive_reads": 0, "drive_writes": 0, "publication_writes": 0, "live_reconciliation": 0}}
    print(json.dumps(result, indent=2))
    # This implementation revision cannot turn capability into authorization: until
    # production adapters/capabilities are proven, even valid owner evidence stops.
    return 3 if ok else 2


if __name__ == "__main__": raise SystemExit(main())
