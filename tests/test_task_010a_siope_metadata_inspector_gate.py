from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.github_task_010a_siope_metadata_inspector_gate import CONTRACT, GateError, validate


class Task010AGateTest(unittest.TestCase):
    def test_canonical_contract_passes(self) -> None:
        self.assertEqual(validate()["status"], "PASS_TASK_010A_SIOPE_METADATA_INSPECTOR_T0")

    def test_every_forbidden_promotion_fails_closed(self) -> None:
        mutations = {
            "network_enabled": True, "official_acquisition_performed": True,
            "phase_010b_authorized": True, "schedule_or_recurrence_enabled": True,
            "promotions_authorized": True,
        }
        for key, value in mutations.items():
            with self.subTest(key=key): self._reject({key: value})

    def test_semantic_and_year_promotions_fail_closed(self) -> None:
        mutations = {
            "S1_NUM_POPU": "PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "PROVEN",
            "annual_closure_status": "PROVEN", "gold_metrics_status": "PROVEN",
            "closed_annual_series": "2016-2025", "year_2026": "AUTHORIZED",
        }
        for key, value in mutations.items():
            with self.subTest(key=key): self._reject({}, {key: value})

    def _reject(self, top: dict, state: dict | None = None) -> None:
        value = json.loads(CONTRACT.read_text(encoding="utf-8")); value.update(top)
        value["canonical_state"].update(state or {})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"; path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(GateError): validate(path)


if __name__ == "__main__":
    unittest.main()
