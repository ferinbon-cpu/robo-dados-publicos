from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_regime_promotion_assessment.v1.json"
GATE_PATH = ROOT / "scripts" / "github_siope_2025_regime_promotion_gate.py"

_spec = importlib.util.spec_from_file_location("siope_2025_regime_promotion_gate", GATE_PATH)
_gate = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_gate)


class Siope2025RegimePromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))

    def _write_mutated(self, payload: dict) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "assessment.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def test_gate_passes_offline_narrow_promotion(self) -> None:
        result = _gate.validate()
        self.assertEqual(result["status"], "PASS_SIOPE_2025_REGIME_PROMOTION_T0")
        self.assertEqual(result["source_get_count"], 0)
        self.assertEqual(result["drive_read_count"], 0)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["publication"])
        self.assertEqual(result["year_2025_status"], "PROVEN_STRUCTURAL_RECENT")
        self.assertEqual(result["p6_status"], "PROVEN_AVAILABLE_CLOSURE_UNKNOWN")
        self.assertEqual(result["annual_closure_status"], "UNKNOWN")
        self.assertEqual(result["semantic_comparability_status"], "UNKNOWN")
        self.assertEqual(result["gold_metrics_status"], "UNKNOWN")
        self.assertEqual(result["year_2026_status"], "UNPROVEN_CURRENT_YEAR")

    def test_closure_cannot_be_promoted_from_structural_evidence(self) -> None:
        payload = copy.deepcopy(self.assessment)
        payload["classification_matrix"]["annual_closure"]["status"] = "PROVEN"
        with self.assertRaisesRegex(_gate.Siope2025RegimePromotionError, "ANNUAL_CLOSURE"):
            _gate.validate(assessment_path=self._write_mutated(payload))

    def test_gold_metrics_cannot_be_computed_or_promoted(self) -> None:
        payload = copy.deepcopy(self.assessment)
        payload["classification_matrix"]["gold_metrics"]["status"] = "PROVEN"
        payload["classification_matrix"]["gold_metrics"]["computed"] = True
        with self.assertRaisesRegex(_gate.Siope2025RegimePromotionError, "GOLD_STATUS"):
            _gate.validate(assessment_path=self._write_mutated(payload))

    def test_2026_cannot_be_promoted_by_task005(self) -> None:
        payload = copy.deepcopy(self.assessment)
        payload["classification_matrix"]["year_2026"]["status"] = "PROVEN_STRUCTURAL_RECENT"
        payload["classification_matrix"]["year_2026"]["in_scope"] = True
        with self.assertRaisesRegex(_gate.Siope2025RegimePromotionError, "2026_STATUS"):
            _gate.validate(assessment_path=self._write_mutated(payload))

    def test_task005_cannot_authorize_future_batch_or_live(self) -> None:
        payload = copy.deepcopy(self.assessment)
        payload["guards"]["future_batch_execution_authorized"] = True
        with self.assertRaisesRegex(_gate.Siope2025RegimePromotionError, "GUARD_FUTURE_BATCH_EXECUTION_AUTHORIZED"):
            _gate.validate(assessment_path=self._write_mutated(payload))

    def test_p6_role_remains_candidate_for_annual_closure(self) -> None:
        payload = copy.deepcopy(self.assessment)
        payload["classification_matrix"]["p6_annual_role"]["status"] = "PROVEN_ANNUAL_CLOSED"
        with self.assertRaisesRegex(_gate.Siope2025RegimePromotionError, "P6_ANNUAL_ROLE"):
            _gate.validate(assessment_path=self._write_mutated(payload))


if __name__ == "__main__":
    unittest.main()
