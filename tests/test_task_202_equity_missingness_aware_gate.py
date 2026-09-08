import copy
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task199g_official_spatial_triangulation import build_task199g_territory_profile
from robo_dados_publicos.analytics.task202_equity_missingness_aware_gate import (
    Task202Stop,
    build_task202_territory_profile,
    current_answerability_config_v4,
    current_question_answerability_v4,
    load_contract,
    validate_contract,
    validated_coverage,
)
from tests.test_task_201b_inep_workforce_materialization import (
    ANSWERABILITY_V3,
    GENERATED_AT,
    SOFTWARE_VERSION,
    full_products,
)

ROOT = Path(__file__).resolve().parents[1]


def latest_products(*, task202: bool):
    products = full_products(with_task201b=True)
    if task202:
        territory = build_task202_territory_profile(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
    else:
        territory = build_task199g_territory_profile(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
    products["TERRITORY_PROFILE"] = territory
    return products


class TestTask202EquityMissingnessAwareGate(unittest.TestCase):
    def test_contract_pins_64_linked_5_held_and_no_full_network(self):
        report = validate_contract()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["strong_links"], 64)
        self.assertEqual(report["held"], 5)
        self.assertAlmostEqual(report["coverage_rate"], 64 / 69)
        self.assertEqual(report["unresolved_promoted"], 0)
        self.assertFalse(report["full_network"])
        coverage = validated_coverage()
        self.assertEqual(len(coverage["linked_codes"]), 64)
        self.assertEqual(len(coverage["held_codes"]), 5)
        self.assertFalse(set(coverage["linked_codes"]) & set(coverage["held_codes"]))
        self.assertEqual(len(set(coverage["linked_codes"]) | set(coverage["held_codes"])), 69)

    def test_territory_product_adds_only_narrow_missingness_capability(self):
        product = build_task202_territory_profile(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 267)
        self.assertIn(
            "SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS",
            product["capabilities"],
        )
        self.assertIn("SCHOOL_TO_SECTOR_LINK_COVERAGE_64_OF_69", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", product["capabilities"])
        school_codes = {
            row["school_code"]
            for row in product["rows"]
            if row.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"
        }
        self.assertEqual(len(school_codes), 64)

    def test_v4_changes_only_equity_q1_and_reaches_38_of_38(self):
        before = question_answerability(latest_products(task202=False), answerability_path=ANSWERABILITY_V3)
        after = current_question_answerability_v4(latest_products(task202=True))
        self.assertEqual(
            before["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 37, "MATERIALIZED_PARTIAL": 1},
        )
        self.assertEqual(after["status_counts"], {"MATERIALIZED_ANSWERABLE": 38})
        b = {row["question_id"]: row for row in before["questions"]}
        a = {row["question_id"]: row for row in after["questions"]}
        changed = {qid for qid in b if b[qid]["status"] != a[qid]["status"]}
        self.assertEqual(changed, {"EQUITY_Q1"})
        self.assertEqual(a["EQUITY_Q1"]["status"], "MATERIALIZED_ANSWERABLE")

    def test_v4_preserves_equity_metrics_and_removes_only_full_network_gate(self):
        cfg = current_answerability_config_v4()
        recipe = cfg["recipes"]["EQUITY_CONTEXT"]
        metric, territory = recipe["signals"]
        self.assertEqual(metric["match"], "ALL")
        self.assertEqual(
            set(metric["ids"]),
            {"PPI_SHARE", "INSE", "SPECIAL_EDUCATION_ENROLLMENT"},
        )
        self.assertEqual(
            set(territory["required_capabilities"]),
            {
                "CENSUS_SECTOR_CONTEXT",
                "SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS",
            },
        )
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", territory["required_capabilities"])

    def test_missing_any_equity_metric_returns_equity_to_partial(self):
        for missing in ("PPI_SHARE", "INSE", "SPECIAL_EDUCATION_ENROLLMENT"):
            products = latest_products(task202=True)
            school = products["SCHOOL_INDICATOR_SERIES"]
            school["rows"] = [row for row in school["rows"] if row.get("indicator_id") != missing]
            report = current_question_answerability_v4(products)
            equity = {row["question_id"]: row for row in report["questions"]}["EQUITY_Q1"]
            self.assertEqual(equity["status"], "MATERIALIZED_PARTIAL", missing)

    def test_missing_territory_capability_or_sector_context_returns_partial(self):
        for missing_capability in (
            "SCHOOL_TO_SECTOR_LINK_SUBSTANTIAL_COVERAGE_WITH_EXPLICIT_MISSINGNESS",
            "CENSUS_SECTOR_CONTEXT",
        ):
            products = latest_products(task202=True)
            territory = products["TERRITORY_PROFILE"]
            territory["capabilities"] = [
                cap for cap in territory["capabilities"] if cap != missing_capability
            ]
            report = current_question_answerability_v4(products)
            equity = {row["question_id"]: row for row in report["questions"]}["EQUITY_Q1"]
            self.assertEqual(equity["status"], "MATERIALIZED_PARTIAL", missing_capability)

    def test_contract_fails_closed_on_coverage_or_held_roster_drift(self):
        original = json.loads((ROOT / "config/task202_equity_missingness_aware_gate.v1.json").read_text(encoding="utf-8"))
        mutations = []
        low_links = copy.deepcopy(original)
        low_links["coverage"]["strong_links"] = 63
        mutations.append(low_links)
        low_rate = copy.deepcopy(original)
        low_rate["coverage"]["rate"] = 0.91
        mutations.append(low_rate)
        full = copy.deepcopy(original)
        full["coverage"]["full_network"] = True
        mutations.append(full)
        held = copy.deepcopy(original)
        held["held_roster"]["codes"][0] = "99999999"
        mutations.append(held)

        for mutated in mutations:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as handle:
                json.dump(mutated, handle)
                handle.flush()
                with self.assertRaises(Task202Stop):
                    load_contract(handle.name)

    def test_v3_remains_37_of_38_with_64_of_69_territory(self):
        report = question_answerability(latest_products(task202=True), answerability_path=ANSWERABILITY_V3)
        self.assertEqual(
            report["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 37, "MATERIALIZED_PARTIAL": 1},
        )
        equity = {row["question_id"]: row for row in report["questions"]}["EQUITY_Q1"]
        self.assertEqual(equity["status"], "MATERIALIZED_PARTIAL")


if __name__ == "__main__":
    unittest.main()
