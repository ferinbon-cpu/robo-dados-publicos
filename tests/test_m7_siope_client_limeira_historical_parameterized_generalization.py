from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_generalization import (
    HistoricalParameterizedGeneralizationError,
    build_parameterized_plan,
    load_json,
    review,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_parameterized_generalization.json"


class HistoricalParameterizedGeneralizationTests(unittest.TestCase):
    def test_review_passes_with_three_full_years_and_2021_readonly(self):
        result = review(load_json(CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION")
        self.assertEqual(result["full_pipeline_evidence_years"], [2024, 2023, 2022])
        self.assertEqual(result["read_only_evidence_years"], [2021])
        self.assertTrue(result["generic_year_parameter_verified"])
        self.assertFalse(result["individual_year_workflow_duplication_authorized"])
        self.assertFalse(result["batch_live_authorized"])
        self.assertEqual(result["max_years_per_future_batch"], 5)

    def test_config_drift_fails_closed(self):
        config = load_json(CONFIG)
        drifted = copy.deepcopy(config)
        drifted["individual_year_workflow_duplication_authorized"] = True
        with self.assertRaises(HistoricalParameterizedGeneralizationError):
            validate_config(drifted)

    def test_batch_cannot_be_live_authorized_in_this_gate(self):
        config = load_json(CONFIG)
        drifted = copy.deepcopy(config)
        drifted["batch_live_authorized"] = True
        with self.assertRaises(HistoricalParameterizedGeneralizationError):
            validate_config(drifted)

    def test_parameterized_plan_replaces_per_year_workflow_duplication(self):
        plan = build_parameterized_plan([2021, 2020, 2019])
        self.assertEqual([item["year"] for item in plan], [2021, 2020, 2019])
        self.assertTrue(all(len(item["stages"]) == 9 for item in plan))
        self.assertTrue(all(item["period"] == 6 for item in plan))

    def test_plan_is_bounded_and_ordered(self):
        with self.assertRaises(HistoricalParameterizedGeneralizationError):
            build_parameterized_plan([2020, 2021])
        with self.assertRaises(HistoricalParameterizedGeneralizationError):
            build_parameterized_plan([2021, 2020, 2019, 2018, 2017, 2016])
        with self.assertRaises(HistoricalParameterizedGeneralizationError):
            build_parameterized_plan([2021, 2021])

    def test_evidence_blob_drift_fails_closed(self):
        config = load_json(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            for meta in config["evidence"].values():
                target = tmp_root / meta["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / meta["path"]).read_bytes())
            first = next(iter(config["evidence"].values()))
            path = tmp_root / first["path"]
            data = json.loads(path.read_text(encoding="utf-8"))
            data["run_id"] += 1
            path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
            with self.assertRaises(HistoricalParameterizedGeneralizationError):
                review(config, root=tmp_root)

    def test_gate_script_runs_offline(self):
        proc = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_parameterized_generalization_gate.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["drive_called"])
        self.assertFalse(payload["batch_live_authorized"])
        self.assertEqual(
            payload["next_gate"],
            "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN_0_8_0",
        )


if __name__ == "__main__":
    unittest.main()
