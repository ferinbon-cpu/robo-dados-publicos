import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import build_task196_products
from robo_dados_publicos.analytics.task199d_territory_profile_product import (
    build_task199d_territory_profile,
    load_contract,
    territory_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_199D_TERRITORY_PROFILE_PRODUCT_0.8.0.json"
GENERATED_AT = "2026-09-07T16:10:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products():
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    substantive = {
        k: v for k, v in bundle["products"].items()
        if k not in {"QUERY_PRODUCT_CATALOG", "PLANNING_DOCUMENT_INDEX"}
    }
    planning = build_planning_overlay(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
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
    task196 = build_task196_products(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    substantive["SCHOOL_INDICATOR_SERIES"] = task196["SCHOOL_INDICATOR_SERIES"]
    substantive["FISCAL_SERIES"] = task196["FISCAL_SERIES"]
    territory = build_task199d_territory_profile(
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


class TestTask199DTerritoryProfileProduct(unittest.TestCase):
    def test_contract_and_dictionary_are_exact(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["territory_rows"], 67)
        self.assertEqual(got["school_links"], 14)
        self.assertFalse(got["full_network_school_link"])
        obj = load_contract()
        dictionary = obj["sources"]["income_dictionary"]
        self.assertEqual(dictionary["bytes"], 10197)
        self.assertEqual(
            dictionary["sha256"],
            "fea6e2b2439eeb167c6fa9c136ed7cb13ebcb06f4c875d634e3e2578c668a48d",
        )
        self.assertEqual(
            dictionary["semantics"]["V06004"],
            "Valor do rendimento nominal médio mensal das pessoas responsáveis com rendimentos por domicílios particulares permanentes ocupados",
        )
        self.assertEqual(
            dictionary["semantics"]["V06006"],
            "Valor do rendimento nominal mediano mensal das pessoas responsáveis com rendimentos por domicílios particulares permanentes ocupados",
        )

    def test_rows_preserve_population_reconciliation_and_school_scope(self):
        rows = territory_rows()
        population = [r for r in rows if r["metric_id"] == "POPULATION"]
        self.assertEqual(len(population), 1)
        self.assertEqual(population[0]["value"], 291869)
        school_mean = [r for r in rows if r["metric_id"] == "SECTOR_RESPONSIBLE_INCOME_MEAN"]
        self.assertEqual(len(school_mean), 14)
        self.assertTrue(all(r["geo_level"] == "SCHOOL_LOCATION_CENSUS_SECTOR" for r in school_mean))
        self.assertTrue(all("SCHOOL_LOCATION_CONTEXT_NE_STUDENT_SOCIOECONOMIC_PROFILE" in r["caution"] for r in school_mean))

    def test_territory_product_is_eighth_product_with_partial_school_link_capability(self):
        product = build_task199d_territory_profile(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["product_name"], "TERRITORY_PROFILE")
        self.assertEqual(product["row_count"], 67)
        self.assertIn("MUNICIPAL_DEMOGRAPHY", product["capabilities"])
        self.assertIn("CENSUS_SECTOR_CONTEXT", product["capabilities"])
        self.assertIn("SECTOR_INCOME_CONTEXT", product["capabilities"])
        self.assertIn("SCHOOL_TO_SECTOR_LINK_PARTIAL", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", product["capabilities"])

    def test_answerability_closes_two_territory_gaps_only(self):
        report = question_answerability(current_products())
        self.assertEqual(
            report["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 32, "MATERIALIZED_PARTIAL": 6},
        )
        by_id = {row["question_id"]: row for row in report["questions"]}
        self.assertEqual(by_id["TERR_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["TERR_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertIn(
            "TERRITORY_PROFILE::CAPABILITY:SCHOOL_TO_SECTOR_LINK_FULL_NETWORK",
            by_id["EQUITY_Q1"]["product_content_gaps"],
        )

    def test_evidence_keeps_equity_fail_closed(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["answerability"]["expected_after"], "32_ANSWERABLE_6_PARTIAL_0_EXPLICIT_GAP")
        self.assertEqual(e["answerability"]["equity_q1"], "MATERIALIZED_PARTIAL")
        self.assertFalse(e["territory_profile"]["full_network_school_link"])
        self.assertIn(
            "NO_VULNERABILITY_INDEX_WITHOUT_EXPLICIT_METHOD",
            e["guards"],
        )


if __name__ == "__main__":
    unittest.main()
