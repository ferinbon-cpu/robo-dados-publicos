from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_2025_bounded_runner import Siope2025BoundedRunnerError, run_bounded
from robo_dados_publicos.sources.siope_2025_fake_transport import FakeSiope2025Transport

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "siope_2025_bounded_runner.v1.json"
DESIGN = ROOT / "config" / "siope_2025_readonly_discovery_design.v1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "siope_2025_readonly_discovery"
REGIMES = ROOT / "config" / "siope_historical_regimes.v1.json"


class Siope2025BoundedRunnerRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.design = json.loads(DESIGN.read_text(encoding="utf-8"))

    def test_cardinality_above_one_stops_before_phase_b(self) -> None:
        fixture = json.loads((FIXTURES / "duplicate_p6_stop.json").read_text(encoding="utf-8"))
        transport = FakeSiope2025Transport(fixture)
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "DUPLICATE_P6"):
            run_bounded(runner_config=self.config, design=self.design, transport=transport)
        self.assertEqual(len(transport.requests), 6)

    def test_schema_extra_field_stops_in_runner(self) -> None:
        fixture = json.loads((FIXTURES / "p6_exact_schema.json").read_text(encoding="utf-8"))
        fixture = copy.deepcopy(fixture)
        fixture["phase_b_schema_probe"]["schema_fields"].append("TASK003_EXTRA_FIELD")
        transport = FakeSiope2025Transport(fixture)
        with self.assertRaisesRegex(Siope2025BoundedRunnerError, "PHASE_B_SCHEMA_DRIFT"):
            run_bounded(runner_config=self.config, design=self.design, transport=transport)
        self.assertEqual(len(transport.requests), 7)

    def test_historical_boundary_regressions_remain_unchanged(self) -> None:
        payload = json.loads(REGIMES.read_text(encoding="utf-8"))
        regimes = {item["id"]: item for item in payload["regimes"]}
        self.assertEqual(regimes["PROVEN_ANNUAL_2016"]["period"], {"value": 1, "status": "PROVEN"})
        self.assertEqual(regimes["PROVEN_BIMONTHLY_2017_2024"]["period"], {"value": 6, "status": "PROVEN"})
        self.assertEqual(regimes["PROVEN_BIMONTHLY_2017_2024"]["years"], list(range(2017, 2025)))
        self.assertEqual(regimes["RECENT_2025"]["status"], "UNPROVEN_RECENT")
        self.assertEqual(regimes["RECENT_2025"]["period"], {"value": None, "status": "UNKNOWN"})
        self.assertEqual(regimes["CURRENT_2026"]["status"], "UNPROVEN_CURRENT_YEAR")
        self.assertEqual(regimes["CURRENT_2026"]["period"], {"value": None, "status": "UNKNOWN"})
        self.assertFalse(payload["future_batch_execution_authorized"])
        self.assertFalse(payload["live_discovery_authorized"])


if __name__ == "__main__":
    unittest.main()
