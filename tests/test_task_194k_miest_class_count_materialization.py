import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task193_network_school_count_turma_recovery import build_task193_products
from robo_dados_publicos.analytics.task194k_miest_class_count_materialization import (
    Task194KStop,
    build_task194k_products,
    class_count_overlay_row,
    load_contract,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_194K_MIEST_CLASS_COUNT_MATERIALIZATION_0.8.0.json"
GENERATED_AT = "2026-09-07T03:30:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products(*, task194k: bool):
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
    overlay = (
        build_task194k_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        if task194k
        else build_task193_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    )
    substantive["SCHOOL_INDICATOR_SERIES"] = overlay["SCHOOL_INDICATOR_SERIES"]
    substantive["FISCAL_SERIES"] = overlay["FISCAL_SERIES"]
    return _with_catalog(
        {
            **substantive,
            "PLANNING_DOCUMENT_INDEX": planning,
            "ACCOUNTING_LEDGER": accounting,
            "REVENUE_LEDGER": revenue,
        },
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )


class TestTask194KMIeSTClassCountMaterialization(unittest.TestCase):
    def test_contract_pins_direct_class_count_and_handoff_hashes(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["class_count"], 1110)
        self.assertEqual(got["school_count"], 69)
        self.assertEqual(got["ai40_class_count"], 816)
        self.assertEqual(got["ei29_class_count"], 294)
        self.assertEqual(got["complementary_classes_excluded"], 131)

        obj = load_contract()
        self.assertEqual(
            obj["artifacts"]["miests_ciclo_2025_12"]["sha256"],
            "72577ea79fcdacd22f96daf114b25fa49f623bd3496ca0bba619e43c291f2b6b",
        )
        self.assertEqual(
            obj["artifacts"]["dictionary"]["sha256"],
            "4444763557f26e76164a331a495601b042ce161f1fa4eb0ba26a93e163392391",
        )

    def test_class_count_row_has_exact_scope_and_semantics(self):
        row = class_count_overlay_row()
        self.assertEqual(row["indicator_id"], "CLASS_COUNT")
        self.assertEqual(row["period"], "2025")
        self.assertEqual(row["scope_level"], "NETWORK")
        self.assertEqual(row["scope_id"], "3526902:MUNICIPAL:CURRENT_69_UNITS")
        self.assertEqual(row["value"], 1110)
        self.assertEqual(row["source_family"], "SEDUC_SP_MIEST")
        self.assertIn("CLASSESEC_131_COMPLEMENTARY_EXCLUDED", row["caution"])
        self.assertIn("CLASS_COUNT_NE_ATU_PROXY", row["caution"])

    def test_products_add_one_class_row_and_preserve_fiscal(self):
        before = build_task193_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        after = build_task194k_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(before["SCHOOL_INDICATOR_SERIES"]["row_count"], 1019)
        self.assertEqual(after["SCHOOL_INDICATOR_SERIES"]["row_count"], 1020)
        self.assertEqual(before["FISCAL_SERIES"]["row_count"], 61)
        self.assertEqual(after["FISCAL_SERIES"]["row_count"], 61)
        self.assertEqual(
            before["FISCAL_SERIES"]["content_sha256"],
            after["FISCAL_SERIES"]["content_sha256"],
        )
        self.assertTrue(after["SCHOOL_INDICATOR_SERIES"]["overlay_scope"]["class_count_materialized"])
        self.assertEqual(after["CLASS_COUNT"]["network_value"], 1110)

    def test_network_q1_becomes_answerable_and_only_one_status_moves(self):
        before = question_answerability(current_products(task194k=False))
        after = question_answerability(current_products(task194k=True))
        self.assertEqual(
            before["status_counts"],
            {"EXPLICIT_GAP": 2, "MATERIALIZED_ANSWERABLE": 27, "MATERIALIZED_PARTIAL": 9},
        )
        self.assertEqual(
            after["status_counts"],
            {"EXPLICIT_GAP": 2, "MATERIALIZED_ANSWERABLE": 28, "MATERIALIZED_PARTIAL": 8},
        )
        before_by_id = {row["question_id"]: row for row in before["questions"]}
        after_by_id = {row["question_id"]: row for row in after["questions"]}
        self.assertEqual(before_by_id["NETWORK_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(after_by_id["NETWORK_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(before_by_id["NETWORK_Q1"]["missing_or_insufficient_metrics"], ["CLASS_COUNT"])
        self.assertEqual(after_by_id["NETWORK_Q1"]["missing_or_insufficient_metrics"], [])
        changed = {
            qid for qid in before_by_id
            if before_by_id[qid]["status"] != after_by_id[qid]["status"]
        }
        self.assertEqual(changed, {"NETWORK_Q1"})

    def test_fail_closed_on_reconciliation_or_complementary_semantic_drift(self):
        obj = load_contract()
        obj["reconciliation"]["ei29_curricular_class_count"] = 295
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad_ei29.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task194KStop, "TASK194K_EI29_COUNT"):
                load_contract(path)

        obj = load_contract()
        obj["artifacts"]["dictionary"]["normalized_semantic"] = "CURRICULAR"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad_semantic.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task194KStop, "TASK194K_DICT_SEMANTIC"):
                load_contract(path)

        obj = load_contract()
        obj["curricular_class_count"]["proxy_used"] = True
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad_proxy.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task194KStop, "TASK194K_PROXY"):
                load_contract(path)

    def test_canonical_evidence_closes_class_count_only(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["class_count"]["network_value"], 1110)
        self.assertEqual(e["class_count"]["ai40"], 816)
        self.assertEqual(e["class_count"]["ei29"], 294)
        self.assertEqual(e["class_count"]["complementary_classes_excluded"], 131)
        self.assertEqual(e["answerability"]["network_q1_after"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(e["answerability"]["remaining_missing_metrics"], [])
        self.assertEqual(e["expected_products"]["school_indicator_series_row_count"], 1020)
        self.assertEqual(e["expected_products"]["fiscal_series_row_count"], 61)
        self.assertEqual(e["historical_transport_preserved"]["task194j_result"], "HTTP_403_FORBIDDEN_ON_OFFICIAL_SEDUC_RESOURCE")
        self.assertEqual(e["remote_effects"]["serving"], 0)

    def test_answerability_matrix_probe(self):
        report = question_answerability(current_products(task194k=True))
        print(
            "TASK194K_ANSWERABILITY_MATRIX="
            + json.dumps(
                [
                    {
                        "question_id": row["question_id"],
                        "status": row["status"],
                        "missing_or_insufficient_metrics": row["missing_or_insufficient_metrics"],
                    }
                    for row in report["questions"]
                ],
                sort_keys=True,
            )
        )

    def test_runtime_snapshot_probe(self):
        products = build_task194k_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        print(
            "TASK194K_RUNTIME_SNAPSHOTS="
            + json.dumps(
                {
                    "school_snapshot_id": products["SCHOOL_INDICATOR_SERIES"]["snapshot_id"],
                    "school_content_sha256": products["SCHOOL_INDICATOR_SERIES"]["content_sha256"],
                    "school_row_count": products["SCHOOL_INDICATOR_SERIES"]["row_count"],
                    "fiscal_snapshot_id": products["FISCAL_SERIES"]["snapshot_id"],
                    "fiscal_content_sha256": products["FISCAL_SERIES"]["content_sha256"],
                    "fiscal_row_count": products["FISCAL_SERIES"]["row_count"],
                    "class_count": products["CLASS_COUNT"]["network_value"],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
