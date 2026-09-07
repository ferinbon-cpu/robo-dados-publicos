import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import build_task196_products
from robo_dados_publicos.analytics.task199f_same_parity_address_bracket import (
    build_task199f_territory_profile,
    held_after_task199f,
    load_contract,
    territory_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
GENERATED_AT = "2026-09-07T17:15:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products():
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive = {k:v for k,v in bundle["products"].items() if k not in {"QUERY_PRODUCT_CATALOG","PLANNING_DOCUMENT_INDEX"}}
    planning = build_planning_overlay(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    accounting = {
        "product_name":"ACCOUNTING_LEDGER","product_schema":"ACCOUNTING_LEDGER_V1",
        "snapshot_id":t188["accounting_ledger"]["snapshot_id"],"content_sha256":t188["accounting_ledger"]["content_sha256"],
        "row_count":t188["accounting_ledger"]["row_count"],"generated_at":GENERATED_AT,"software_version":SOFTWARE_VERSION,
        "rows":[],"capabilities":t188["accounting_ledger"]["capabilities"],"observed_stages":t188["accounting_ledger"]["observed_stages"],
    }
    revenue = {
        "product_name":"REVENUE_LEDGER","product_schema":t186["revenue_ledger"]["product_schema"],
        "snapshot_id":t186["revenue_ledger"]["snapshot_id"],"content_sha256":t186["revenue_ledger"]["content_sha256"],
        "row_count":t186["revenue_ledger"]["row_count"],"generated_at":GENERATED_AT,"software_version":SOFTWARE_VERSION,
        "rows":[],"capabilities":t186["revenue_ledger"]["capabilities"],
    }
    task196 = build_task196_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive["SCHOOL_INDICATOR_SERIES"] = task196["SCHOOL_INDICATOR_SERIES"]
    substantive["FISCAL_SERIES"] = task196["FISCAL_SERIES"]
    territory = build_task199f_territory_profile(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    return _with_catalog({
        **substantive,
        "PLANNING_DOCUMENT_INDEX":planning,
        "ACCOUNTING_LEDGER":accounting,
        "REVENUE_LEDGER":revenue,
        "TERRITORY_PROFILE":territory,
    }, generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)


class TestTask199FSameParityAddressBracket(unittest.TestCase):
    def test_contract_proves_two_bounded_same_parity_brackets(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["strong_school_links"], 59)
        self.assertEqual(got["held_school_links"], 10)
        self.assertAlmostEqual(got["coverage_rate"], 0.855072)
        self.assertFalse(got["full_network_school_link"])
        obj = load_contract()
        self.assertEqual(len(obj["promotions"]), 2)
        for row in obj["promotions"]:
            self.assertEqual(row["lower_sector"], row["upper_sector"])
            self.assertEqual(row["lower_cnefe_number"] % 2, row["sme_number"] % 2)
            self.assertEqual(row["upper_cnefe_number"] % 2, row["sme_number"] % 2)

    def test_only_two_formerly_held_schools_are_promoted(self):
        held = held_after_task199f()
        self.assertEqual(len(held), 10)
        held_codes = {r["codigo_inep"] for r in held}
        self.assertNotIn("35217864", held_codes)
        self.assertNotIn("35099557", held_codes)
        self.assertIn("35470600", held_codes)
        self.assertIn("35656823", held_codes)

    def test_product_expands_by_exactly_eight_rows(self):
        rows = territory_rows()
        self.assertEqual(len(rows), 247)
        codes = {r["school_code"] for r in rows if r["geo_level"] == "SCHOOL_LOCATION_CENSUS_SECTOR"}
        self.assertEqual(len(codes), 59)
        product = build_task199f_territory_profile(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        self.assertEqual(product["row_count"], 247)
        self.assertIn("SCHOOL_TO_SECTOR_LINK_COVERAGE_59_OF_69", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", product["capabilities"])

    def test_answerability_remains_fail_closed_for_equity(self):
        report = question_answerability(current_products())
        self.assertEqual(report["status_counts"], {"MATERIALIZED_ANSWERABLE":32,"MATERIALIZED_PARTIAL":6})
        by_id = {row["question_id"]:row for row in report["questions"]}
        self.assertEqual(by_id["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertIn("TERRITORY_PROFILE::CAPABILITY:SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", by_id["EQUITY_Q1"]["product_content_gaps"])


if __name__ == "__main__":
    unittest.main()
