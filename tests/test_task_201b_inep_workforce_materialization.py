import copy
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
from robo_dados_publicos.analytics.task201b_inep_workforce_materialization import (
    build_task201b_school_indicator,
    load_contract,
    validate_contract,
    workforce_overlay_rows,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
ANSWERABILITY_V2 = ROOT / "config/observatory_semantic_answerability.v2.json"
ANSWERABILITY_V3 = ROOT / "config/observatory_semantic_answerability.v3.json"
EVIDENCE = ROOT / "docs/evidence/TASK_201B_INEP_2025_WORKFORCE_MANUAL_HANDOFF_0.8.0.json"
GENERATED_AT = "2026-09-07T22:10:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def full_products(*, with_task201b: bool):
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
    task196 = build_task196_products(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    if with_task201b:
        school = build_task201b_school_indicator(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )["SCHOOL_INDICATOR_SERIES"]
    else:
        school = task196["SCHOOL_INDICATOR_SERIES"]
    substantive["SCHOOL_INDICATOR_SERIES"] = school
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


class TestTask201BInepWorkforceMaterialization(unittest.TestCase):
    def test_manual_handoff_identity_and_values_are_pinned(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["staff_count"], 1280)
        self.assertEqual(got["bond_category_count"], 4)
        self.assertEqual(got["bond_category_sum_non_additive"], 1372)
        self.assertEqual(got["sme_current_contracted_teachers"], 842)
        obj = load_contract()
        self.assertEqual(
            obj["source"]["xlsx_sha256"],
            "af3a0f13731214730c4baa362bfc542c526c8c81d31c48e699919623c491462c",
        )
        self.assertTrue(obj["source"]["official_manifest_md5_verified"])

    def test_overlay_materializes_count_bonds_and_current_sme_context(self):
        rows = workforce_overlay_rows()
        by_id = {row["indicator_id"]: row for row in rows}
        self.assertEqual(len(rows), 7)
        self.assertEqual(by_id["STAFF_COUNT"]["value"], 1280)
        self.assertEqual(by_id["EMPLOYMENT_BOND"]["value"], 4)
        self.assertEqual(
            by_id["EMPLOYMENT_BOND"]["bond_counts"],
            {
                "CONCURSADO_EFETIVO_ESTAVEL": 681,
                "CONTRATO_TEMPORARIO": 291,
                "CONTRATO_TERCEIRIZADO": 0,
                "CONTRATO_CLT": 400,
            },
        )
        self.assertEqual(by_id["CONTRACTED_TEACHER_CURRENT_COUNT"]["value"], 842)
        self.assertIn("NON_ADDITIVE", by_id["EMPLOYMENT_BOND"]["caution"])

    def test_school_product_grows_from_1035_to_1042_rows(self):
        product = build_task201b_school_indicator(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )["SCHOOL_INDICATOR_SERIES"]
        self.assertEqual(product["row_count"], 1042)
        ids = {row["indicator_id"] for row in product["rows"]}
        self.assertIn("STAFF_COUNT", ids)
        self.assertIn("EMPLOYMENT_BOND", ids)
        self.assertIn("CONTRACTED_TEACHER_CURRENT_COUNT", ids)

    def test_answerability_moves_only_teach_q2_to_37_of_38(self):
        before_products = full_products(with_task201b=False)
        after_products = full_products(with_task201b=True)
        before = question_answerability(
            before_products,
            answerability_path=ANSWERABILITY_V2,
        )
        after = current_question_answerability(after_products)
        self.assertEqual(
            before["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 36, "MATERIALIZED_PARTIAL": 2},
        )
        self.assertEqual(
            after["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 37, "MATERIALIZED_PARTIAL": 1},
        )
        b = {row["question_id"]: row for row in before["questions"]}
        a = {row["question_id"]: row for row in after["questions"]}
        changed = {qid for qid in b if b[qid]["status"] != a[qid]["status"]}
        self.assertEqual(changed, {"TEACH_Q2"})
        self.assertEqual(a["TEACH_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(a["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")

    def test_v3_requires_both_staff_count_and_employment_bond(self):
        obj = json.loads(ANSWERABILITY_V3.read_text(encoding="utf-8"))
        signal = next(
            s for s in obj["recipes"]["STAFFING_BONDS"]["signals"]
            if s["kind"] == "METRIC"
        )
        self.assertEqual(signal["match"], "ALL")
        self.assertEqual(set(signal["ids"]), {"STAFF_COUNT", "EMPLOYMENT_BOND"})
        self.assertEqual(signal["scope_levels_required"], ["NETWORK"])

        products = full_products(with_task201b=True)
        for missing_id in ("STAFF_COUNT", "EMPLOYMENT_BOND"):
            weakened = copy.deepcopy(products)
            rows = weakened["SCHOOL_INDICATOR_SERIES"]["rows"]
            weakened["SCHOOL_INDICATOR_SERIES"]["rows"] = [
                row for row in rows if row["indicator_id"] != missing_id
            ]
            result = question_answerability(
                weakened,
                answerability_path=ANSWERABILITY_V3,
            )
            q = {row["question_id"]: row for row in result["questions"]}
            self.assertEqual(q["TEACH_Q2"]["status"], "MATERIALIZED_PARTIAL")

    def test_evidence_preserves_non_additivity_and_no_person_data(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["employment_bonds"]["additivity"], "NON_ADDITIVE")
        self.assertEqual(e["sme_current_context"]["unique_contracted_teachers"], 842)
        self.assertFalse(e["sme_current_context"]["person_level_output"])
        encoded = json.dumps(e, ensure_ascii=False).casefold()
        self.assertNotIn('"cpf"', encoded)
        self.assertNotIn('"matricula"', encoded)


if __name__ == "__main__":
    unittest.main()
