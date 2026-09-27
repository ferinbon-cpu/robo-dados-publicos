import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import (
    current_question_answerability,
    question_answerability,
)
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import build_task196_products
from robo_dados_publicos.analytics.task199f_same_parity_address_bracket import build_task199f_territory_profile
from robo_dados_publicos.analytics.task200a_jom_personnel_redigest import build_task200a_jom_product
from robo_dados_publicos.analytics.task200b_school_norms_primary_evidence import (
    load_contract,
    primary_normative_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
ANSWERABILITY_V1 = ROOT / "config/observatory_semantic_answerability.v1.json"
ANSWERABILITY_V2 = ROOT / "config/observatory_semantic_answerability.v2.json"
EVIDENCE = ROOT / "docs/evidence/TASK_200B_SCHOOL_NORMS_PRIMARY_EVIDENCE_0.8.0.json"
GENERATED_AT = "2026-09-07T19:30:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products():
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive = {
        k: v
        for k, v in bundle["products"].items()
        if k not in {"QUERY_PRODUCT_CATALOG", "PLANNING_DOCUMENT_INDEX", "JOM_EVENT_INDEX"}
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
    territory = build_task199f_territory_profile(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    jom = build_task200a_jom_product(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
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


class TestTask200BSchoolNormsPrimaryEvidence(unittest.TestCase):
    def test_contract_and_two_authoritative_sources_are_exact(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["primary_normative_rows"], 2)
        self.assertEqual(got["source_families"], ["CME", "MUNICIPAL_LEGISLATION"])
        self.assertFalse(got["recent_jom_is_required_gate"])
        rows = primary_normative_rows()
        self.assertEqual(
            {row["source_sha256"] for row in rows},
            {
                "5d01a883bd5ec721b9a9a8b0a0f2c985eea8958da23de8d475d7c73d3109c07c",
                "a534b99711652d437e1672dbaf39b9f56fe8f35c042f3648ae8483187c909b60",
            },
        )

    def test_v1_is_immutable_and_v2_changes_only_norms_questions(self):
        products = current_products()
        historical = question_answerability(products, answerability_path=ANSWERABILITY_V1)
        current = current_question_answerability(products)
        self.assertEqual(
            historical["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 34, "MATERIALIZED_PARTIAL": 4},
        )
        self.assertEqual(
            current["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 36, "MATERIALIZED_PARTIAL": 2},
        )
        h = {row["question_id"]: row for row in historical["questions"]}
        c = {row["question_id"]: row for row in current["questions"]}
        changed = {qid for qid in h if h[qid]["status"] != c[qid]["status"]}
        self.assertEqual(changed, {"NORMS_Q1", "NORMS_Q2"})
        self.assertEqual(c["NORMS_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(c["NORMS_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(c["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(c["TEACH_Q2"]["status"], "MATERIALIZED_PARTIAL")

    def test_v2_gate_requires_authority_quality_and_substantive_topic(self):
        obj = json.loads(ANSWERABILITY_V2.read_text(encoding="utf-8"))
        signal = obj["recipes"]["SCHOOL_NORMS"]["signals"][0]
        self.assertEqual(signal["product"], "PLANNING_DOCUMENT_INDEX")
        self.assertEqual(signal["min_matching_rows"], 2)
        self.assertEqual(
            set(signal["required_source_family_role_pairs"]),
            {"CME", "MUNICIPAL_LEGISLATION"},
        )
        criteria = signal["row_criteria"]
        self.assertEqual(criteria["policy_domains_any"], ["EDUCATION"])
        self.assertEqual(criteria["evidence_role_any"], ["PRIMARY_NORMATIVE"])
        self.assertEqual(criteria["quality_status_any"], ["VALIDATED"])
        self.assertIn("FULL_TIME_EDUCATION", criteria["topics_any"])

    def test_evidence_keeps_false_positive_guards(self):
        contract = load_contract()
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(
            e["expected_answerability"]["changed_questions"],
            ["NORMS_Q1", "NORMS_Q2"],
        )
        self.assertIn("CONTRACT_NE_SCHOOL_NORM", contract["guards"])
        self.assertIn("PERSONNEL_ACT_NE_SCHOOL_NORM", contract["guards"])
        self.assertIn("BUDGET_DECREE_NE_SCHOOL_OPERATION_NORM", contract["guards"])
        self.assertIn("NORMATIVE_ACT_NE_IMPLEMENTATION_RESULT", contract["guards"])


if __name__ == "__main__":
    unittest.main()
