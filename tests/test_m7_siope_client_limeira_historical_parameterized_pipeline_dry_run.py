from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_pipeline_dry_run import (
    EXPECTED_STAGES,
    HistoricalParameterizedPipelineDryRunError,
    load_json,
    review,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_parameterized_pipeline_dry_run.json"
EVIDENCE = ROOT / "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION_RUN_1_0.8.0.json"
SCRIPT = ROOT / "scripts/github_siope_client_limeira_historical_parameterized_pipeline_dry_run_gate.py"
MODULE = "robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_pipeline_dry_run"


class HistoricalParameterizedPipelineDryRunTests(unittest.TestCase):
    def test_review_passes_offline_and_proves_equivalence(self):
        result = review(load_json(CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_PIPELINE_DRY_RUN")
        self.assertEqual(result["dry_run_years"], [2024, 2023, 2022, 2021])
        self.assertEqual(result["equivalence_years"], [2024, 2023, 2022])
        self.assertEqual(result["pilot_year"], 2021)
        self.assertEqual(result["stage_count_per_year"], 9)
        self.assertTrue(result["stage_contract_equivalent"])
        self.assertTrue(result["source_url_template_equivalent"])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["drive_called"])
        self.assertEqual(result["mutation_count"], 0)
        self.assertFalse(result["source_get_authorized"])
        self.assertFalse(result["drive_write_authorized"])
        self.assertFalse(result["batch_live_authorized"])
        self.assertEqual(
            result["next_gate"],
            "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT_0_8_0",
        )

    def test_unsafe_config_drifts_fail_closed(self):
        original = load_json(CONFIG)
        for key in (
            "source_get_authorized",
            "drive_write_authorized",
            "historical_collection_authorized",
            "batch_live_authorized",
            "retry_authorized",
            "pagination_authorized",
            "processing_live_authorized",
            "recurrence_authorized",
            "schedule_enabled",
            "individual_year_workflow_duplication_authorized",
        ):
            with self.subTest(key=key):
                drifted = copy.deepcopy(original)
                drifted[key] = True
                with self.assertRaises(HistoricalParameterizedPipelineDryRunError):
                    validate_config(drifted)

    def test_gate1_evidence_blob_drift_fails_closed(self):
        config = load_json(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            target = tmp_root / config["generalization_evidence"]["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
            data["run_id"] += 1
            target.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
            with self.assertRaises(HistoricalParameterizedPipelineDryRunError):
                review(config, root=tmp_root)

    def test_gate1_evidence_semantic_drift_fails_even_if_hash_check_is_mocked_valid(self):
        config = load_json(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            target = tmp_root / config["generalization_evidence"]["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
            data["network_called"] = True
            target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            with patch(f"{MODULE}._git_blob_sha", return_value=config["generalization_evidence"]["blob_sha"]):
                with self.assertRaises(HistoricalParameterizedPipelineDryRunError):
                    review(config, root=tmp_root)

    def test_stage_contract_drift_fails_closed(self):
        config = load_json(CONFIG)

        def bad_plan(years, *, period=6):
            stages = list(EXPECTED_STAGES)
            stages[-1] = "GOLD_UNSAFE"
            return [{"year": year, "period": period, "stages": stages} for year in years]

        with patch(f"{MODULE}.build_parameterized_plan", side_effect=bad_plan):
            with self.assertRaises(HistoricalParameterizedPipelineDryRunError):
                review(config, root=ROOT)

    def test_script_runs_directly_and_stays_offline(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["drive_called"])
        self.assertEqual(result["mutation_count"], 0)
        self.assertFalse(result["source_get_authorized"])
        self.assertFalse(result["drive_write_authorized"])

    def test_config_is_bounded_to_four_dry_run_years_and_future_batch_max_five(self):
        config = load_json(CONFIG)
        self.assertEqual(len(config["dry_run_years"]), 4)
        self.assertEqual(config["max_years_per_future_batch"], 5)
        self.assertEqual(config["period"], 6)
        self.assertEqual(config["schema_key_count"], 52)


if __name__ == "__main__":
    unittest.main()
