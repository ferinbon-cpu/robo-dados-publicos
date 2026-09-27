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
SCRIPT = ROOT / "scripts" / "github_siope_2025_alias_finality_audit_gate.py"
ASSESSMENT = ROOT / "config" / "siope_2025_alias_finality_audit.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_008_SIOPE_2025_ALIAS_FINALITY_EVIDENCE_0.8.0.json"

spec = importlib.util.spec_from_file_location("task008_gate", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Task008AliasFinalityAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def _json_path(self, value: dict) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False)
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_baseline_keep_unknown_passes(self) -> None:
        result = mod.validate()
        self.assertEqual(result["status"], mod.PASS)
        self.assertEqual(result["decision"], "KEEP_UNKNOWN")
        self.assertEqual(result["source_data_get_count"], 0)
        self.assertEqual(result["operational_receipt_status_query_count"], 0)
        self.assertEqual(result["alias_identity_proven_count"], 0)
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
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(assessment_path=self._json_path(value))

    def test_package_existence_cannot_become_content_inspection(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_a_alias_metadata"]["package_content_inspection_status"] = "INSPECTED"
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(assessment_path=self._json_path(value))

    def test_alias_bridge_cannot_be_inferred(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_a_alias_metadata"]["current_2025_alias_bridge_status"] = "PROVEN"
        value["gate_a_alias_metadata"]["field_level_identity_proven_count"] = 11
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(assessment_path=self._json_path(value))

    def test_num_popu_definition_cannot_be_invented(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["alias_metadata_summary"]["num_popu_definition_proven"] = True
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(evidence_path=self._json_path(value))

    def test_processing_publication_cannot_be_upgraded_to_finality(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_b_finality_state"]["processed_or_published_equivalent_to_non_rectifiable_final"] = True
        value["gate_b_finality_state"]["observed_2025_p6_finality_state"] = "PROVEN_FINAL"
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(assessment_path=self._json_path(value))

    def test_limeira_operational_status_cannot_be_claimed_queried(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["operational_receipt_status_query_count"] = 1
        value["finality_summary"]["observed_2025_limeira_finality_state"] = "PROCESSED"
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(evidence_path=self._json_path(value))

    def test_gold_promotion_remains_blocked(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["gate_a_alias_metadata"]["gold_promotion_authorized"] = True
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(assessment_path=self._json_path(value))

    def test_closed_series_cannot_expand_to_2025(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["resulting_state"]["closed_annual_series_last_year"] = 2025
        value["resulting_state"]["closed_series_eligible"] = True
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(assessment_path=self._json_path(value))

    def test_2026_cannot_be_promoted(self) -> None:
        value = copy.deepcopy(self.assessment)
        value["resulting_state"]["year_2026_status"] = "PROVEN"
        with self.assertRaises(mod.AliasFinalityAuditError):
            mod.validate(assessment_path=self._json_path(value))

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
