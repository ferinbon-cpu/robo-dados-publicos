import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import build_task196_products
from robo_dados_publicos.analytics.task199e_school_sector_expansion import (
    build_task199e_territory_profile,
    load_held_fixture,
    load_school_fixture,
    territory_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_199E_SCHOOL_TO_SECTOR_EXPANSION_0.8.0.json"
GENERATED_AT = "2026-09-07T16:45:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products():
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive = {
        k: v for k, v in bundle["products"].items()
        if k not in {"QUERY_PRODUCT_CATALOG", "PLANNING_DOCUMENT_INDEX"}
    }
    planning = build_planning_overlay(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    accounting = {
        "product_name": "ACCOUNTING_LEDGER",
        "product_schema": "ACCOUNTING_LEDGER_V1",
        "snapshot_id": t188["accounting_ledger"]["snapshot_id"],
        "content_sha256": t188["accounting_ledger"]["content_sha256"],
        "row_count": t188["accounting_ledger"]["row_count"],
        "generated_at": GENERATED_AT,
        "software_version": SOFTWARE_VERSION,
        "rows": [],
        "capabilities": t188["accounting_ledger"]["capabilities"],
        "observed_stages": t188["accounting_ledger"]["observed_stages"],
    }
    revenue = {
        "product_name": "REVENUE_LEDGER",
        "product_schema": t186["revenue_ledger"]["product_schema"],
        "snapshot_id": t186["revenue_ledger"]["snapshot_id"],
        "content_sha256": t186["revenue_ledger"]["content_sha256"],
        "row_count": t186["revenue_ledger"]["row_count"],
        "generated_at": GENERATED_AT,
        "software_version": SOFTWARE_VERSION,
        "rows": [],
        "capabilities": t186["revenue_ledger"]["capabilities"],
    }
    task196 = build_task196_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive["SCHOOL_INDICATOR_SERIES"] = task196["SCHOOL_INDICATOR_SERIES"]
    substantive["FISCAL_SERIES"] = task196["FISCAL_SERIES"]
    territory = build_task199e_territory_profile(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    return _with_catalog(
        {
            **substantive,
            "PLANNING_DOCUMENT_INDEX": planning,
            "ACCOUNTING_LEDGER": accounting,
            "REVENUE_LEDGER": revenue,
            "TERRITORY_PROFILE": territory,
        },
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )


class TestTask199ESchoolSectorExpansion(unittest.TestCase):
    def test_contract_exact_counts_and_no_full_network_claim(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["territory_rows"], 239)
        self.assertEqual(got["strong_school_links"], 57)
        self.assertEqual(got["held_school_links"], 12)
        self.assertAlmostEqual(got["coverage_rate"], 0.826087)
        self.assertFalse(got["full_network_school_link"])

    def test_fixture_tiers_are_exact_and_held_rows_have_reasons(self):
        rows = load_school_fixture()
        self.assertEqual(len(rows), 57)
        tiers = {tier: sum(1 for r in rows if r["match_tier"] == tier) for tier in {"A","B","C"}}
        self.assertEqual(tiers, {"A":41,"B":15,"C":1})
        held = load_held_fixture()
        self.assertEqual(len(held), 12)
        self.assertTrue(all(r["hold_reason"] for r in held))

    def test_product_expands_from_67_to_239_without_full_network_capability(self):
        product = build_task199e_territory_profile(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 239)
        self.assertIn("SCHOOL_TO_SECTOR_LINK_PARTIAL", product["capabilities"])
        self.assertIn("SCHOOL_TO_SECTOR_LINK_COVERAGE_57_OF_69", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", product["capabilities"])
        school_rows = [r for r in product["rows"] if r["geo_level"] == "SCHOOL_LOCATION_CENSUS_SECTOR"]
        self.assertEqual(len(school_rows), 228)
        self.assertEqual(len({r["school_code"] for r in school_rows}), 57)

    def test_all_school_rows_preserve_location_not_student_guard(self):
        school_rows = [r for r in territory_rows() if r["geo_level"] == "SCHOOL_LOCATION_CENSUS_SECTOR"]
        self.assertTrue(all("SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE" in r["caution"] for r in school_rows))
        self.assertTrue(all("PARTIAL_57_OF_69_NETWORK" in r["caution"] for r in school_rows))

    def test_answerability_does_not_inflate(self):
        report = question_answerability(current_products())
        self.assertEqual(
            report["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 32, "MATERIALIZED_PARTIAL": 6},
        )
        by_id = {r["question_id"]: r for r in report["questions"]}
        self.assertEqual(by_id["TERR_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["TERR_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertIn(
            "TERRITORY_PROFILE::CAPABILITY:SCHOOL_TO_SECTOR_LINK_FULL_NETWORK",
            by_id["EQUITY_Q1"]["product_content_gaps"],
        )

    def test_evidence_reports_zero_answerability_status_changes(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["crosswalk"]["after_strong_links"], 57)
        self.assertEqual(e["crosswalk"]["held"], 12)
        self.assertEqual(e["answerability"]["before"], e["answerability"]["after"])
        self.assertEqual(e["answerability"]["status_change_count"], 0)


if __name__ == "__main__":
    unittest.main()
