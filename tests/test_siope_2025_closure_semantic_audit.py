from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts" / "github_siope_2025_closure_semantic_audit_gate.py"
AUDIT_PATH = ROOT / "config" / "siope_2025_closure_semantic_audit.v1.json"

spec = importlib.util.spec_from_file_location("siope_2025_closure_semantic_audit_gate", GATE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


class Siope2025ClosureSemanticAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

    def _validate_mutated(self, mutate) -> None:
        payload = copy.deepcopy(self.audit)
        mutate(payload)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            gate.validate(audit_path=path)

    def test_gate_passes_with_repository_evidence_only(self) -> None:
        result = gate.validate()
        self.assertEqual(result["status"], gate.PASS)
        self.assertEqual(result["source_get_count"], 0)
        self.assertEqual(result["gate_a_annual_closure"], "NOT_PROVEN")
        self.assertEqual(result["gate_b_semantic_comparability"], "NOT_PROVEN")
        self.assertEqual(result["closed_annual_series_last_year"], 2024)
        self.assertEqual(result["gold_metrics_status"], "UNKNOWN")

    def test_closure_cannot_be_promoted_without_missing_proof(self) -> None:
        with self.assertRaisesRegex(gate.ClosureSemanticAuditError, "GATE_A_STATUS|GATE_A_CANONICAL|GATE_A_PROMOTION"):
            self._validate_mutated(lambda p: p["gate_a_annual_closure"].update({
                "status": "PROVEN",
                "canonical_state_remains": "PROVEN",
                "promotion_authorized": True,
            }))

    def test_semantic_comparability_cannot_be_promoted_from_matching_field_names(self) -> None:
        with self.assertRaisesRegex(gate.ClosureSemanticAuditError, "GATE_B_STATUS|GATE_B_CANONICAL|GATE_B_PROMOTION"):
            self._validate_mutated(lambda p: p["gate_b_semantic_comparability"].update({
                "status": "PROVEN",
                "canonical_state_remains": "PROVEN",
                "promotion_authorized": True,
            }))

    def test_closed_series_cannot_expand_to_2025(self) -> None:
        with self.assertRaisesRegex(gate.ClosureSemanticAuditError, "RESULT_CLOSED_SERIES|RESULT_SERIES_BOUNDARY"):
            self._validate_mutated(lambda p: p["resulting_state"].update({
                "closed_series_eligible": True,
                "closed_annual_series_last_year": 2025,
            }))

    def test_gold_cannot_be_promoted_or_computed(self) -> None:
        def mutate(payload: dict) -> None:
            payload["gold_computation_performed"] = True
            payload["resulting_state"]["gold_metrics_status"] = "PROVEN"
        with self.assertRaisesRegex(gate.ClosureSemanticAuditError, "GOLD_COMPUTATION|RESULT_GOLD"):
            self._validate_mutated(mutate)

    def test_live_future_batch_and_2026_remain_blocked(self) -> None:
        for guard in (
            "live_discovery_authorized",
            "future_batch_execution_authorized",
            "year_2026_promotion_authorized",
        ):
            with self.subTest(guard=guard):
                with self.assertRaisesRegex(gate.ClosureSemanticAuditError, "GUARD_"):
                    self._validate_mutated(lambda p, g=guard: p["guards"].__setitem__(g, True))

    def test_task006_has_zero_source_and_drive_effects(self) -> None:
        self.assertEqual(self.audit["source_get_count"], 0)
        self.assertEqual(self.audit["drive_read_count"], 0)
        self.assertEqual(self.audit["drive_write_count"], 0)
        self.assertFalse(self.audit["persistence"])
        self.assertFalse(self.audit["publication"])
        self.assertFalse(self.audit["new_authorization_created"])


if __name__ == "__main__":
    unittest.main()
