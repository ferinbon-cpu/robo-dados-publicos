from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_siope_2025_official_documentary_proof_gate.py"
ASSESSMENT = ROOT / "config" / "siope_2025_official_documentary_proof.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_EVIDENCE_0.8.0.json"

spec = importlib.util.spec_from_file_location("task007_gate", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Task007OfficialDocumentaryProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def _assessment_path(self, value: dict) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False)
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def _evidence_path(self, value: dict) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False)
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_baseline_passes_without_remote_effects(self) -> None:
        result = mod.validate()
        self.assertEqual(result["status"], mod.PASS)
        self.assertEqual(result["source_data_get_count"], 0)
        self.assertEqual(result["annual_closure_status"], "UNKNOWN")
        self.assertEqual(result["semantic_comparability_status"], "UNKNOWN")
        self.assertEqual(result["closed_annual_series_last_year"], 2024)
        self.assertEqual(result["gold_metrics_status"], "UNKNOWN")

    def test_cli_gate_passes(self) -> None:
        proc = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(mod.PASS, proc.stdout)

    def test_source_data_get_fails_closed(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["source_data_get_count"] = 1
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_non_official_proof_source_fails_closed(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["official_sources"][0]["url"] = "https://example.com/not-official.pdf"
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_annual_consolidation_cannot_be_upgraded_to_finality(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_a_p6_closure"]["finality_status"] = "PROVEN"
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_annual_closure_cannot_be_promoted(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_a_p6_closure"]["annual_closure_status"] = "PROVEN"
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_alias_identity_cannot_be_inferred_from_similar_names(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_b_field_semantics"]["field_assessment"][0]["2025_alias_identity_proven"] = True
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_population_definition_cannot_be_invented(self) -> None:
        value = copy.deepcopy(self.assessment)
        row = next(row for row in value["gate_b_field_semantics"]["field_assessment"] if row["odata_field"] == "NUM_POPU")
        row["historical_definition_found"] = True
        row["historical_meaning"] = "population"
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_gold_promotion_remains_blocked(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_b_field_semantics"]["gold_promotion_authorized"] = True
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_closed_series_cannot_expand_to_2025(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["resulting_state"]["closed_annual_series_last_year"] = 2025
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(assessment_path=self._assessment_path(value))

    def test_documentary_evidence_cannot_claim_2025_alias_bridge(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["field_definition_summary"]["2025_odata_alias_identity_proven_count"] = 10
        with self.assertRaises(mod.DocumentaryProofError):
            mod.validate(evidence_path=self._evidence_path(value))

    def test_all_execution_guards_remain_false(self) -> None:
        self.assertTrue(self.assessment["guards"])
        self.assertTrue(all(value is False for value in self.assessment["guards"].values()))
        effects = self.evidence["effects"]
        self.assertEqual(effects["drive_read_count"], 0)
        self.assertEqual(effects["drive_write_count"], 0)
        self.assertFalse(effects["gold_computation"])
        self.assertFalse(effects["publication"])


if __name__ == "__main__":
    unittest.main()
