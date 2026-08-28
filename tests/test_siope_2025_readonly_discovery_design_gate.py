from __future__ import annotations

import ast
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.github_siope_2025_readonly_discovery_design_gate import (
    DESIGN,
    POLICY,
    REGIMES,
    Siope2025DesignError,
    validate,
)
from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS


class Siope2025ReadonlyDiscoveryDesignGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = json.loads(DESIGN.read_text(encoding="utf-8"))

    def _validate_design(self, changed: dict) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "design.json"
            path.write_text(json.dumps(changed), encoding="utf-8")
            validate(path, REGIMES, POLICY)

    def test_canonical_design_passes_with_zero_effects(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "PASS_SIOPE_2025_READONLY_DISCOVERY_DESIGN_T0")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["drive_called"])
        self.assertFalse(result["secrets_used"])
        self.assertFalse(result["runtime_execution_authorized"])

    def test_design_cannot_authorize_get_or_runtime(self) -> None:
        for key in ("source_get_authorized_by_this_design", "runtime_execution_authorized_by_this_design"):
            changed = copy.deepcopy(self.design)
            changed["proposed_runtime"][key] = True
            with self.assertRaisesRegex(Siope2025DesignError, key.upper()):
                self._validate_design(changed)

    def test_request_budget_is_exact_and_retry_pagination_are_closed(self) -> None:
        mutations = (
            ("maximum_total_request_count", 8, "TOTAL_REQUEST_BOUND"),
            ("max_attempts", 2, "ATTEMPTS"),
            ("retry_authorized", True, "RETRY"),
            ("pagination_authorized", True, "PAGINATION"),
            ("follow_odata_nextlink", True, "NEXTLINK"),
        )
        for key, value, code in mutations:
            changed = copy.deepcopy(self.design)
            changed["proposed_runtime"][key] = value
            with self.assertRaisesRegex(Siope2025DesignError, code):
                self._validate_design(changed)

    def test_all_periods_are_probes_and_p6_remains_candidate(self) -> None:
        changed = copy.deepcopy(self.design)
        changed["proposed_runtime"]["period_probe_values"] = [6]
        with self.assertRaisesRegex(Siope2025DesignError, "PERIOD_PROBES"):
            self._validate_design(changed)
        changed = copy.deepcopy(self.design)
        changed["phase_b_conditional_schema"]["period_semantics"] = "PROVEN"
        with self.assertRaisesRegex(Siope2025DesignError, "P6_NOT_PROVEN"):
            self._validate_design(changed)

    def test_schema_requires_exact_fields_without_aliases(self) -> None:
        changed = copy.deepcopy(self.design)
        changed["phase_b_conditional_schema"]["allowed_aliases"] = {"VAL_RECE_REAL": "similar_name"}
        with self.assertRaisesRegex(Siope2025DesignError, "ALIASES"):
            self._validate_design(changed)
        changed = copy.deepcopy(self.design)
        changed["phase_b_conditional_schema"]["required_gold_input_fields"].pop()
        with self.assertRaisesRegex(Siope2025DesignError, "GOLD_INPUT_FIELDS"):
            self._validate_design(changed)

    def test_persistence_drive_layers_and_publication_remain_closed(self) -> None:
        for key in ("drive_access_authorized", "persistence_authorized", "publication_authorized", "bronze_silver_gold_creation_authorized"):
            changed = copy.deepcopy(self.design)
            changed["proposed_runtime"][key] = True
            with self.assertRaisesRegex(Siope2025DesignError, key.upper()):
                self._validate_design(changed)

    def test_2025_cannot_be_promoted_or_join_closed_series(self) -> None:
        for key in ("promote_2025_to_proven", "join_closed_annual_series"):
            changed = copy.deepcopy(self.design)
            changed["promotion_contract"][key] = True
            with self.assertRaisesRegex(Siope2025DesignError, key.upper()):
                self._validate_design(changed)

    def test_gate_has_no_network_drive_or_environment_dependency(self) -> None:
        source = Path("scripts/github_siope_2025_readonly_discovery_design_gate.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertLessEqual(imports, {"__future__", "json", "pathlib"})
        lowered = source.lower()
        for forbidden in ("import urllib", "import requests", "import httpx", "import socket", "oauth", "google_drive", "os.environ", "getenv"):
            self.assertNotIn(forbidden, lowered)

    def test_offline_schema_pin_matches_the_existing_52_field_contract(self) -> None:
        offline = self.design["offline_validation"]
        self.assertEqual(offline["fixture_count"], 10)
        self.assertEqual(set(offline["expected_schema_fields"]), PROVEN_DADOS_GERAIS_FIELDS)


if __name__ == "__main__":
    unittest.main()
