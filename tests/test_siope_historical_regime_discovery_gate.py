from __future__ import annotations

import ast
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.github_siope_historical_regime_discovery_gate import (
    MAP,
    MATRIX,
    POLICY,
    RegimeDiscoveryError,
    validate,
)


class SiopeHistoricalRegimeDiscoveryGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.regime_map = json.loads(MAP.read_text(encoding="utf-8"))
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def _validate_map(self, changed: dict) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.json"
            path.write_text(json.dumps(changed), encoding="utf-8")
            validate(path, MATRIX, POLICY)

    @staticmethod
    def _regime(data: dict, year: int) -> dict:
        return next(item for item in data["regimes"] if year in item["years"])

    def test_canonical_contract_passes_offline(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "PASS_SIOPE_HISTORICAL_REGIME_DISCOVERY_T0")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["secrets_used"])
        self.assertFalse(result["future_batch_execution_authorized"])

    def test_period_boundary_is_2016_p1_and_2017_p6(self) -> None:
        self.assertEqual(self._regime(self.regime_map, 2016)["period"]["value"], 1)
        self.assertEqual(self._regime(self.regime_map, 2017)["period"]["value"], 6)
        for year, bad_period in ((2016, 6), (2017, 1)):
            changed = copy.deepcopy(self.regime_map)
            self._regime(changed, year)["period"]["value"] = bad_period
            with self.assertRaisesRegex(RegimeDiscoveryError, str(year)):
                self._validate_map(changed)

    def test_2008_2015_cannot_claim_current_schema(self) -> None:
        changed = copy.deepcopy(self.regime_map)
        self._regime(changed, 2008)["schema"] = {"status": "PROVEN_CURRENT_SCHEMA", "name": "DADOS_GERAIS_SIOPE_52_FIELDS"}
        with self.assertRaisesRegex(RegimeDiscoveryError, "PRE2016_SCHEMA"):
            self._validate_map(changed)

    def test_period_drift_fails_closed(self) -> None:
        changed = copy.deepcopy(self.regime_map)
        self._regime(changed, 2012)["period"]["value"] = 6
        with self.assertRaisesRegex(RegimeDiscoveryError, "PRE2016_P1"):
            self._validate_map(changed)

    def test_2025_and_2026_promotion_fails_closed(self) -> None:
        for year in (2025, 2026):
            changed = copy.deepcopy(self.regime_map)
            self._regime(changed, year)["status"] = "PROVEN"
            with self.assertRaisesRegex(RegimeDiscoveryError, str(year)):
                self._validate_map(changed)

    def test_legacy_and_external_promotions_fail_closed(self) -> None:
        for year, code in ((2005, "LEGACY_PROMOTION"), (2000, "EXTERNAL_PROMOTION")):
            changed = copy.deepcopy(self.regime_map)
            self._regime(changed, year)["status"] = "PROVEN"
            with self.assertRaisesRegex(RegimeDiscoveryError, code):
                self._validate_map(changed)

    def test_batch_expansion_authorization_fails_closed(self) -> None:
        changed = copy.deepcopy(self.regime_map)
        changed["future_batch_execution_authorized"] = True
        with self.assertRaisesRegex(RegimeDiscoveryError, "FUTURE_BATCH"):
            self._validate_map(changed)

    def test_gate_has_only_standard_library_imports_and_no_drive_or_secret_dependency(self) -> None:
        script = Path("scripts/github_siope_historical_regime_discovery_gate.py").read_text(encoding="utf-8")
        tree = ast.parse(script)
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertLessEqual(imported, {"__future__", "json", "pathlib"})
        lowered = script.lower()
        for forbidden in ("requests", "httpx", "urllib", "socket", "google_drive", "oauth", "os.environ", "getenv"):
            self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()
