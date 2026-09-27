import copy
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import current_question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import build_task196_products
from robo_dados_publicos.analytics.task199g_official_spatial_triangulation import (
    Task199GStop,
    build_task199g_territory_profile,
    held_after_task199g,
    load_contract,
    territory_rows,
    validate_contract,
)
from robo_dados_publicos.analytics.task200a_jom_personnel_redigest import build_task200a_jom_product
from robo_dados_publicos.analytics.task201b_inep_workforce_materialization import build_task201b_school_indicator

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_199G_OFFICIAL_SPATIAL_TRIANGULATION_0.8.0.json"
GENERATED_AT = "2026-09-08T00:45:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products():
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive = {
        k: v for k, v in bundle["products"].items()
        if k not in {"QUERY_PRODUCT_CATALOG", "PLANNING_DOCUMENT_INDEX", "JOM_EVENT_INDEX"}
    }
    planning = build_planning_overlay(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    task196 = build_task196_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive["SCHOOL_INDICATOR_SERIES"] = build_task201b_school_indicator(
        generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION
    )["SCHOOL_INDICATOR_SERIES"]
    substantive["FISCAL_SERIES"] = task196["FISCAL_SERIES"]
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
    territory = build_task199g_territory_profile(
        generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION
    )
    jom = build_task200a_jom_product(
        generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION
    )
    return _with_catalog(
        {
            **substantive,
            "JOM_EVENT_INDEX": jom,
            "PLANNING_DOCUMENT_INDEX": planning,
            "ACCOUNTING_LEDGER": accounting,
            "REVENUE_LEDGER": revenue,
            "TERRITORY_PROFILE": territory,
        },
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )


class TestTask199GOfficialSpatialTriangulation(unittest.TestCase):
    def test_contract_proves_exactly_five_bounded_promotions(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["strong_school_links"], 64)
        self.assertEqual(got["held_school_links"], 5)
        self.assertAlmostEqual(got["coverage_rate"], 0.927536)
        self.assertFalse(got["full_network_school_link"])
        self.assertEqual(
            set(got["promotion_codes"]),
            {"35470600", "35656823", "35217924", "35217992", "35223359"},
        )

    def test_held_set_remains_exactly_the_five_ambiguous_cases(self):
        held = held_after_task199g()
        self.assertEqual(len(held), 5)
        self.assertEqual(
            {row["codigo_inep"] for row in held},
            {"35208437", "35286229", "35004773", "35099569", "35241885"},
        )

    def test_product_expands_by_twenty_rows_to_64_school_links(self):
        rows = territory_rows()
        self.assertEqual(len(rows), 267)
        codes = {
            row["school_code"] for row in rows
            if row["geo_level"] == "SCHOOL_LOCATION_CENSUS_SECTOR"
        }
        self.assertEqual(len(codes), 64)
        product = build_task199g_territory_profile(
            generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION
        )
        self.assertEqual(product["row_count"], 267)
        self.assertIn("SCHOOL_TO_SECTOR_LINK_COVERAGE_64_OF_69", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", product["capabilities"])

    def test_promoted_sector_metrics_are_exactly_pinned(self):
        obj = load_contract()
        by_code = {row["codigo_inep"]: row for row in obj["promotions"]}
        self.assertEqual(by_code["35217924"]["sector_id"], "352690205000094")
        self.assertEqual(by_code["35656823"]["sector_id"], "352690205000652")
        self.assertEqual(by_code["35217992"]["sector_id"], "352690205000375")
        self.assertEqual(by_code["35223359"]["sector_id"], "352690205000554")
        self.assertEqual(by_code["35470600"]["sector_id"], "352690205000136")
        self.assertEqual(by_code["35217924"]["sector_population_2022"], 539)
        self.assertEqual(by_code["35470600"]["V06004_sector_percentile_unweighted"], 45.4)

    def test_answerability_remains_37_of_38_fail_closed(self):
        report = current_question_answerability(current_products())
        self.assertEqual(
            report["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 37, "MATERIALIZED_PARTIAL": 1},
        )
        by_id = {row["question_id"]: row for row in report["questions"]}
        self.assertEqual(by_id["TEACH_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertIn(
            "TERRITORY_PROFILE::CAPABILITY:SCHOOL_TO_SECTOR_LINK_FULL_NETWORK",
            by_id["EQUITY_Q1"]["product_content_gaps"],
        )

    def test_rafael_requires_all_landmark_rows_same_named_school_sector(self):
        obj = load_contract()
        row = next(x for x in obj["promotions"] if x["codigo_inep"] == "35470600")
        row["cnefe_landmark"]["unique_sector"] = "352690205000142P"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as tmp:
            json.dump(obj, tmp)
            tmp.flush()
            with self.assertRaises(Task199GStop):
                load_contract(tmp.name)

    def test_alfredo_requires_exact_km_and_named_school_same_sector(self):
        obj = load_contract()
        row = next(x for x in obj["promotions"] if x["codigo_inep"] == "35656823")
        row["cnefe_exact_km"]["sector"] = "352690205000524P"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as tmp:
            json.dump(obj, tmp)
            tmp.flush()
            with self.assertRaises(Task199GStop):
                load_contract(tmp.name)

    def test_jose_newer_exact_address_cannot_be_weakened_back_to_three(self):
        obj = load_contract()
        row = next(x for x in obj["promotions"] if x["codigo_inep"] == "35217924")
        row["cnefe_named"]["number"] = 3
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as tmp:
            json.dump(obj, tmp)
            tmp.flush()
            with self.assertRaises(Task199GStop):
                load_contract(tmp.name)

    def test_evidence_explicitly_preserves_all_five_held_cases(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["after"]["strong_school_links"], 64)
        self.assertEqual(evidence["after"]["held"], 5)
        self.assertFalse(evidence["after"]["full_network"])
        self.assertEqual(len(evidence["held_after"]), 5)
        self.assertEqual(evidence["answerability"]["equity_q1"], "MATERIALIZED_PARTIAL")


if __name__ == "__main__":
    unittest.main()
