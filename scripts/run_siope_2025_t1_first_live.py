#!/usr/bin/env python3
"""Entrypoint for TASK 004A preparation and future TASK 004B first live run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_2025_request_plan import (  # noqa: E402
    materialize_request_plan,
    sanitized_plan_evidence,
)
from robo_dados_publicos.sources.siope_2025_t1_authorization import (  # noqa: E402
    AUTH_PATH,
    STOP,
    Siope2025T1AuthorizationError,
    validate_authorization_document,
    validate_preparation_contract,
)

PREP_PATH = ROOT / "config/siope_2025_t1_first_live_preparation.v1.json"
DESIGN_PATH = ROOT / "config/siope_2025_readonly_discovery_design.v1.json"
POLICY_PATH = ROOT / "config/automation_policy.v1.json"
AUTH_FILE = ROOT / AUTH_PATH
EXIT_STOP = 13


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"OBJECT_REQUIRED:{path}")
    return value


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _stop_payload(reason: str, *, source_get_count: int = 0) -> dict:
    return {
        "status": STOP,
        "reason": reason,
        "source_get_count": source_get_count,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "response_persisted": False,
    }


def prepare() -> dict:
    preparation = _load(PREP_PATH)
    design = _load(DESIGN_PATH)
    policy = _load(POLICY_PATH)
    validate_preparation_contract(preparation, design, policy)
    if AUTH_FILE.exists():
        raise Siope2025T1AuthorizationError("STOP_SIOPE_2025_T1_AUTHORIZATION_AUTH_FILE_MUST_BE_ABSENT_IN_004A")
    plan = materialize_request_plan(design)
    return {
        "status": "PASS_SIOPE_2025_T1_PREPARATION_T0",
        "task_phase": "TASK_004A",
        "live_execution_authorized": False,
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "request_plan_evidence": sanitized_plan_evidence(plan, executed_ordinals=[]),
        "next_gate": "TASK_004B_OWNER_AUTHORIZATION_AND_SINGLE_LIVE_RUN",
    }


def live(authorization_id_input: str | None) -> dict:
    preparation = _load(PREP_PATH)
    design = _load(DESIGN_PATH)
    policy = _load(POLICY_PATH)
    validate_preparation_contract(preparation, design, policy)

    if not AUTH_FILE.exists():
        raise Siope2025T1AuthorizationError(STOP)
    authorization = _load(AUTH_FILE)
    current_head = _git("rev-parse", "HEAD")
    current_parent = _git("rev-parse", "HEAD^")
    base = authorization.get("authorized_base_sha")
    if not isinstance(base, str):
        raise Siope2025T1AuthorizationError(STOP)
    changed_paths = sorted(line for line in _git("diff", "--name-only", f"{base}..HEAD").splitlines() if line)
    grant = validate_authorization_document(
        authorization,
        preparation,
        current_head_sha=current_head,
        current_parent_sha=current_parent,
        changed_paths_since_base=changed_paths,
    )
    if not authorization_id_input or authorization_id_input != grant.authorization_id:
        raise Siope2025T1AuthorizationError(STOP)

    # Live-capable imports intentionally happen only after the authorization gate.
    from robo_dados_publicos.sources.siope_2025_t1_discovery import execute_authorized_discovery
    from robo_dados_publicos.sources.siope_2025_t1_transport import Siope2025T1HttpTransport

    transport = Siope2025T1HttpTransport.build_live(grant=grant)
    return execute_authorized_discovery(grant=grant, design=design, transport=transport)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("prepare", "live"), default="prepare")
    parser.add_argument("--authorization-id", default=None)
    args = parser.parse_args()
    try:
        result = prepare() if args.mode == "prepare" else live(args.authorization_id)
    except Exception as exc:
        source_get_count = int(getattr(exc, "source_get_count", 0) or 0)
        print(json.dumps(_stop_payload(str(exc), source_get_count=source_get_count), sort_keys=True))
        return EXIT_STOP
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
