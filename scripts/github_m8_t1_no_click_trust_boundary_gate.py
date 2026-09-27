#!/usr/bin/env python3
"""Fail closed unless M8 T1 auto execution is on the protected public main branch."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.automation.policy import load_policy
from robo_dados_publicos.automation.trust_boundary import evaluate_m8_t1_trust_boundary


def _as_bool(value: str, *, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise RuntimeError(f"STOP_M8_T1_INVALID_BOOLEAN_{field}")


def run(*, dry_run: bool = False) -> dict:
    policy = load_policy(ROOT)
    if dry_run:
        return evaluate_m8_t1_trust_boundary(
            policy,
            repository="ferinbon-cpu/robo-dados-publicos",
            ref="refs/heads/main",
            event_name="push",
            ref_protected=True,
            repository_private=False,
        )

    return evaluate_m8_t1_trust_boundary(
        policy,
        repository=os.environ.get("GITHUB_REPOSITORY", ""),
        ref=os.environ.get("GITHUB_REF", ""),
        event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
        ref_protected=_as_bool(os.environ.get("M8_GITHUB_REF_PROTECTED", ""), field="REF_PROTECTED"),
        repository_private=_as_bool(os.environ.get("M8_GITHUB_REPOSITORY_PRIVATE", ""), field="REPOSITORY_PRIVATE"),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run(dry_run=args.dry_run), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_M8_T1_TRUST_BOUNDARY", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 47
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
