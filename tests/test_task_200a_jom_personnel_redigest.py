import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import (
    _with_catalog,
    build_jom_product,
    build_task184_bundle,
)
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import build_task196_products
from robo_dados_publicos.analytics.task199f_same_parity_address_bracket import build_task199f_territory_profile
from robo_dados_publicos.analytics.task200a_jom_personnel_redigest import (
    build_task200a_jom_product,
    load_contract,
    load_redigest_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
ANSWERABILITY = ROOT / "config/observatory_semantic_answerability.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_200A_JOM_PERSONNEL_REDIGEST_0.8.0.json"
GENERATED_AT = "2026-09-07T18:50:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products(*, task200a: bool):
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    substantive = {
        k: v
        for k, v in bundle["products"].items()
        if k not in {
            "QUERY_PRODUCT_CATALOG",
            "PLANNING_DOCUMENT_INDEX",
            "JOM_EVENT_INDEX",
        }
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
    territory = build_task199f_territory_profile(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    if task200a:
        jom = build_task200a_jom_product(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
    else:
        jom, _ = build_jom_product(
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


class TestTask200AJomPersonnelRedigest(unittest.TestCase):
    def test_contract_is_exact_native_text_only(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["redigested_event_count"], 10)
        self.assertEqual(got["unique_editions"], 3)
        self.assertTrue(got["native_text_only"])
        self.assertFalse(got["ocr_used"])
        obj = load_contract()
        self.assertTrue(obj["drive"]["readback_verified"])
        self.assertEqual(
            obj["drive"]["full_events_sha256"],
            "edcea1e9ae251ffd05d1396f3ec117ee55292848f27825d4d3519e1579363bda",
        )

    def test_fixture_preserves_ids_pages_and_primary_clauses(self):
        rows = load_redigest_rows()
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({row["event_id"] for row in rows}), 10)
        self.assertTrue(all(row["principal_subject"] == "EDUCATION_PERSONNEL" for row in rows))
        self.assertTrue(all(row["object_text_native"] for row in rows))
        self.assertIn(
            "EFFECTIVE_APPOINTMENT_FROM_PUBLIC_COMPETITION",
            {row["principal_action"] for row in rows},
        )
        self.assertIn(
            "Secretário de Escola",
            {row["role"] for row in rows},
        )

    def test_answerability_recipes_are_subject_aware(self):
        obj = json.loads(ANSWERABILITY.read_text(encoding="utf-8"))
        personnel = obj["recipes"]["PERSONNEL_EVENTS"]["signals"][0]["row_criteria"]
        self.assertEqual(personnel["policy_domains_any"], ["EDUCATION"])
        self.assertEqual(personnel["evidence_layers_any"], ["PERSONNEL"])
        norms = obj["recipes"]["SCHOOL_NORMS"]["signals"][0]["row_criteria"]
        self.assertIn("event_type_any", norms)
        self.assertIn("education_topics_any", norms)
        self.assertNotIn("WORKFORCE", norms["education_topics_any"])

    def test_jom_product_keeps_303_identities_and_adds_personnel_semantics(self):
        product = build_task200a_jom_product(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 303)
        self.assertEqual(product["task200a_overlay"]["patched_event_count"], 10)
        self.assertFalse(product["task200a_overlay"]["event_identity_rewritten"])
        self.assertGreaterEqual(
            product["task200a_overlay"]["personnel_education_matching_rows"],
            10,
        )
        by_id = {row["event_id"]: row for row in product["rows"]}
        selected = by_id["JOEV_f378479cbe48ab0ebaa9"]
        self.assertIn("EDUCATION", selected["policy_domains"])
        self.assertIn("PERSONNEL", selected["evidence_layers"])
        self.assertIn("Monitor", selected["object_text"])

    def test_exactly_two_personnel_questions_close(self):
        before = question_answerability(current_products(task200a=False))
        after = question_answerability(current_products(task200a=True))
        self.assertEqual(
            before["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 32, "MATERIALIZED_PARTIAL": 6},
        )
        self.assertEqual(
            after["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 34, "MATERIALIZED_PARTIAL": 4},
        )
        b = {row["question_id"]: row for row in before["questions"]}
        a = {row["question_id"]: row for row in after["questions"]}
        changed = {qid for qid in b if b[qid]["status"] != a[qid]["status"]}
        self.assertEqual(changed, {"PERS_Q1", "PERS_Q2"})
        self.assertEqual(a["PERS_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(a["PERS_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(a["NORMS_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(a["NORMS_Q2"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(a["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(a["TEACH_Q2"]["status"], "MATERIALIZED_PARTIAL")

    def test_evidence_does_not_claim_norms_closed(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(
            e["answerability_expected"]["changed_questions"],
            ["PERS_Q1", "PERS_Q2"],
        )
        self.assertEqual(e["answerability_expected"]["NORMS_Q1"], "MATERIALIZED_PARTIAL")
        self.assertEqual(e["answerability_expected"]["NORMS_Q2"], "MATERIALIZED_PARTIAL")
        self.assertIn("NATIVE_TEXT_ONLY_NO_OCR", e["guards"])


if __name__ == "__main__":
    unittest.main()
