from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_task107_historical_ppa_live_once.py"


def test_task107_runner_bootstraps_repo_root_from_non_repo_cwd():
    with tempfile.TemporaryDirectory() as td:
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--preflight-only"],
            cwd=td,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS_TASK107_RUNNER_BOOTSTRAP_AND_PYPDF_PREFLIGHT"
    assert payload["marker_recovered"] is True
    assert payload["source_requests"] == 0


def test_task107_runner_places_root_on_sys_path_before_project_imports():
    source = RUNNER.read_text(encoding="utf-8")
    root_index = source.index("sys.path.insert")
    import_index = source.index("from robo_dados_publicos.research")
    assert root_index < import_index


def test_task107_preflight_only_contains_no_source_client_execution():
    source = RUNNER.read_text(encoding="utf-8")
    assert "if args.preflight_only:" in source
    assert source.index("if args.preflight_only:") < source.index("client = BoundedOfficialHttpClient")
