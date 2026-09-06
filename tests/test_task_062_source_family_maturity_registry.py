from __future__ import annotations

import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.source_family_maturity import (
    assert_controller_family_coverage,
    auto_execution_allowed_by_maturity,
    execution_maturity,
    load_maturity_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "source_family_maturity_registry.v1.json"
CONTROLLER = ROOT / "config" / "drive_ingestion_controller.v2.json"


class Task062Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_maturity_registry(REGISTRY)
        cls.controller = json.loads(CONTROLLER.read_text(encoding="utf-8"))

    def test_all_controller_families_are_covered(self):
        assert_controller_family_coverage(self.controller, self.registry)
        self.assertEqual(len(self.registry["families"]), 21)

    def test_journal_is_bounded_execution_ready(self):
        self.assertTrue(auto_execution_allowed_by_maturity("JORNAL_OFICIAL", self.registry))

    def test_siope_is_contract_scoped_execution_ready(self):
        self.assertTrue(auto_execution_allowed_by_maturity("SIOPE", self.registry))

    def test_task172_promotes_proven_machine_readable_fiscal_families(self):
        for family in ("FUNDEB", "RREO", "RGF", "TCE_SP_EXPENSES"):
            self.assertTrue(auto_execution_allowed_by_maturity(family, self.registry))
            self.assertEqual(execution_maturity(family, self.registry), "EXECUTION_READY_BOUNDED")

    def test_mde_remains_supervised_after_exact_empty_query(self):
        self.assertFalse(auto_execution_allowed_by_maturity("MDE", self.registry))
        self.assertEqual(execution_maturity("MDE", self.registry), "ROUTING_ONLY_SUPERVISED_EXECUTION")

    def test_tda_remains_blocked(self):
        self.assertEqual(execution_maturity("TDA_LIMEIRA", self.registry), "BLOCKED_PENDING_CONTRACT")

    def test_unknown_family_is_fail_closed(self):
        self.assertFalse(auto_execution_allowed_by_maturity("NEW_UNKNOWN", self.registry))


if __name__ == "__main__":
    unittest.main()
