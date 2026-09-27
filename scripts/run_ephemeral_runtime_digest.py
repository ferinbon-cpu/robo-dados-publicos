from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from robo_dados_publicos.manual_ingest.ephemeral_runtime_digest import (
    EphemeralDigestStop,
    run_ephemeral_digest,
)
from robo_dados_publicos.manual_ingest.source_family_maturity import (
    load_maturity_registry,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config" / "ephemeral_runtime_digest.v1.json"
DEFAULT_MATURITY = ROOT / "config" / "source_family_maturity_registry.v1.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_input_path(workspace: Path, value: str, *, code: str) -> Path:
    root = workspace.resolve(strict=True)
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(code)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(code) from exc
    return resolved


def _safe_result_path(workspace: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or rel == Path("."):
        raise ValueError("STOP_EPHEMERAL_DIGEST_RESULT_PATH")
    root = workspace.resolve(strict=True)
    candidate = (workspace / rel).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("STOP_EPHEMERAL_DIGEST_RESULT_PATH") from exc
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one bounded local-only ephemeral digest batch over bytes already staged in the workspace."
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--maturity", default=str(DEFAULT_MATURITY))
    parser.add_argument("--result", default="ephemeral_digest_result.json")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    result_path = _safe_result_path(workspace, args.result)
    try:
        manifest_path = _safe_input_path(
            workspace, args.manifest, code="STOP_EPHEMERAL_DIGEST_MANIFEST_PATH"
        )
        contract = _load_json(Path(args.contract))
        manifest = _load_json(manifest_path)
        maturity = load_maturity_registry(Path(args.maturity))
        payload = run_ephemeral_digest(
            contract,
            manifest,
            maturity,
            workspace_root=workspace,
        )
        exit_code = 0
    except (EphemeralDigestStop, ValueError, json.JSONDecodeError, OSError) as exc:
        payload = {
            "schema": "EPHEMERAL_DIGEST_RESULT_V1",
            "status": "STOP_EPHEMERAL_RUNTIME_DIGEST",
            "reason": str(exc),
            "remote_effects": 0,
            "persistence_authorized": False,
        }
        exit_code = 2

    result_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
