from __future__ import annotations

import ast
import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_2025_readonly_discovery_offline import (
    Siope2025OfflineFixtureError,
    validate_fixture,
)
from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from scripts.github_siope_2025_readonly_discovery_offline_fixtures_gate import (
    FIXTURES,
    validate_all,
)


class Siope2025ReadonlyDiscoveryOfflineTests(unittest.TestCase):
    def _fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def _validate(self, fixture: dict) -> dict:
        return validate_fixture(fixture, expected_schema_fields=PROVEN_DADOS_GERAIS_FIELDS)

    def test_pinned_fixture_set_covers_all_non_stop_outcomes_and_expected_stops(self) -> None:
        result = validate_all()
        self.assertEqual(result["fixture_count"], 10)
        self.assertEqual(result["pass_case_count"], 3)
        self.assertEqual(result["expected_stop_case_count"], 7)
        self.assertEqual(result["outcomes"], [
            "2025_NOT_OBSERVED",
            "2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN",
            "2025_PERIODS_OBSERVED_SCHEMA_UNKNOWN",
        ])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["drive_called"])
        self.assertFalse(result["runtime_execution_authorized"])

    def test_exact_schema_never_proves_closure_or_promotes_2025(self) -> None:
        result = self._validate(self._fixture("p6_exact_schema.json"))
        self.assertTrue(result["schema_exact"])
        self.assertEqual(result["annual_closure_status"], "UNKNOWN")
        self.assertFalse(result["promote_2025_to_proven"])

    def test_no_periods_and_periods_without_p6_are_distinct(self) -> None:
        none = self._validate(self._fixture("no_periods.json"))
        partial = self._validate(self._fixture("periods_without_p6.json"))
        self.assertEqual(none["outcome"], "2025_NOT_OBSERVED")
        self.assertEqual(partial["outcome"], "2025_PERIODS_OBSERVED_SCHEMA_UNKNOWN")
        self.assertEqual(partial["observed_periods"], [1, 2, 3])

    def test_duplicate_and_schema_drift_fixtures_stop(self) -> None:
        for name, code in (
            ("duplicate_p6_stop.json", "DUPLICATE_P6"),
            ("p6_schema_drift_stop.json", "PHASE_B_SCHEMA_DRIFT"),
            ("p6_extra_schema_stop.json", "PHASE_B_SCHEMA_DRIFT"),
            ("identity_mismatch_stop.json", "IDENTITY_P6"),
            ("nextlink_stop.json", "NEXTLINK_P6"),
            ("transport_drift_stop.json", "CONTENT_TYPE_P6"),
            ("request_budget_stop.json", "REQUEST_BUDGET"),
        ):
            with self.assertRaisesRegex(Siope2025OfflineFixtureError, code):
                self._validate(self._fixture(name))

    def test_identity_mismatch_stops(self) -> None:
        fixture = self._fixture("p6_exact_schema.json")
        fixture["phase_a_period_probes"][5]["records"][0]["COD_MUNI"] = 999999
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "IDENTITY_P6"):
            self._validate(fixture)

    def test_year_and_period_identity_drift_stop(self) -> None:
        wrong_year = self._fixture("p6_exact_schema.json")
        wrong_year["phase_a_period_probes"][5]["records"][0]["NUM_ANO"] = 2024
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "IDENTITY_P6"):
            self._validate(wrong_year)

        wrong_period = self._fixture("p6_exact_schema.json")
        wrong_period["phase_a_period_probes"][5]["records"][0]["NUM_PERI"] = 5
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "IDENTITY_PERIOD_P6"):
            self._validate(wrong_period)

    def test_missing_required_gold_input_field_stops(self) -> None:
        fixture = self._fixture("p6_exact_schema.json")
        fixture["phase_b_schema_probe"]["schema_fields"].remove("VAL_RECE_REAL")
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "PHASE_B_SCHEMA_DRIFT"):
            self._validate(fixture)

    def test_p6_requires_schema_phase_and_other_periods_cannot_trigger_it(self) -> None:
        p6 = self._fixture("p6_exact_schema.json")
        p6["phase_b_schema_probe"] = {"performed": False, "period": None, "schema_fields": []}
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "PHASE_B_REQUIRED"):
            self._validate(p6)
        partial = self._fixture("periods_without_p6.json")
        partial["phase_b_schema_probe"] = {
            "performed": True,
            "period": 3,
            "schema_fields": sorted(PROVEN_DADOS_GERAIS_FIELDS),
        }
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "PHASE_B_NOT_AUTHORIZED"):
            self._validate(partial)

    def test_fixture_cannot_claim_network_drive_or_financial_values(self) -> None:
        for key, code in (
            ("network_called", "NETWORK"),
            ("drive_called", "DRIVE"),
            ("contains_financial_values", "FINANCIAL_VALUES"),
        ):
            fixture = self._fixture("no_periods.json")
            fixture[key] = True
            with self.assertRaisesRegex(Siope2025OfflineFixtureError, code):
                self._validate(fixture)

    def test_transport_redirect_retry_status_content_type_and_size_fail_closed(self) -> None:
        mutations = (
            ("redirect_followed", True, "REDIRECT_P1"),
            ("retry_performed", True, "RETRY_P1"),
            ("nextlink_present", True, "NEXTLINK_P1"),
            ("response_status", 404, "HTTP_STATUS_P1"),
            ("content_type", "text/html", "CONTENT_TYPE_P1"),
            ("response_byte_count", 262145, "RESPONSE_LIMIT_P1"),
            ("method", "POST", "METHOD_P1"),
            ("request_count", 2, "REQUEST_COUNT_P1"),
        )
        for key, value, code in mutations:
            fixture = self._fixture("no_periods.json")
            fixture["phase_a_period_probes"][0][key] = value
            with self.assertRaisesRegex(Siope2025OfflineFixtureError, code):
                self._validate(fixture)

    def test_declared_request_count_must_match_observations(self) -> None:
        fixture = self._fixture("no_periods.json")
        fixture["declared_request_count"] = 7
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "REQUEST_COUNT_DECLARATION"):
            self._validate(fixture)

    def test_schema_only_fixture_cannot_claim_semantic_proof(self) -> None:
        fixture = self._fixture("p6_exact_schema.json")
        fixture["phase_b_schema_probe"]["field_semantics_status"] = "PROVEN"
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "PHASE_B_SEMANTICS"):
            self._validate(fixture)

    def test_schema_field_duplicates_stop_even_if_set_matches(self) -> None:
        fixture = self._fixture("p6_exact_schema.json")
        fixture["phase_b_schema_probe"]["schema_fields"].append("VAL_RECE_REAL")
        with self.assertRaisesRegex(Siope2025OfflineFixtureError, "DUPLICATE_FIELD"):
            self._validate(fixture)

    def test_validator_has_no_network_or_filesystem_import(self) -> None:
        path = Path("robo_dados_publicos/sources/siope_2025_readonly_discovery_offline.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
        self.assertLessEqual(imports, {"__future__", "collections"})


if __name__ == "__main__":
    unittest.main()
