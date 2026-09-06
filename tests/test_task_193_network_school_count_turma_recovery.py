import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task192_ipca_real_education_expenditure import build_task192_products
from robo_dados_publicos.analytics.task193_network_school_count_turma_recovery import (
    Task193Stop,
    build_task193_products,
    class_count_gap,
    load_contract,
    school_count_overlay_row,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_193_NETWORK_SCHOOL_COUNT_TURMA_RECOVERY_0.8.0.json"
GENERATED_AT = "2026-09-06T21:45:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products(*, task193: bool):
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
        build_task193_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        if task193
        else build_task192_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
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


class TestTask193NetworkSchoolCountTurmaRecovery(unittest.TestCase):
    def test_contract_materializes_only_proven_school_count(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["school_count"], 69)
        self.assertIsNone(got["class_count"])
        self.assertEqual(got["ei29_direct_class_count"], 294)
        self.assertEqual(got["official_turma_md5"], "438A3A3FC37F28E7E50E57D7CD8B9DAC")

    def test_school_count_row_has_exact_scope(self):
        row = school_count_overlay_row()
        self.assertEqual(row["indicator_id"], "SCHOOL_COUNT")
        self.assertEqual(row["period"], "2025")
        self.assertEqual(row["scope_level"], "NETWORK")
        self.assertEqual(row["scope_id"], "3526902:MUNICIPAL:CURRENT_69_UNITS")
        self.assertEqual(row["value"], 69)
        self.assertEqual(row["source_family"], "CENSO_ESCOLAR")
        self.assertIn("69_EQUALS_40_PLUS_29", row["caution"])

    def test_class_count_remains_explicit_gap_not_zero_or_proxy(self):
        gap = class_count_gap()
        self.assertEqual(gap["metric_id"], "CLASS_COUNT")
        self.assertEqual(gap["status"], "BLOCKED_PRIMARY_RAW_RECOVERY_REQUIRED")
        self.assertIsNone(gap["network_value"])
        self.assertEqual(gap["validated_subgroup"]["class_count"], 294)
        self.assertEqual(gap["remaining_required_subgroup"]["units"], 40)
        self.assertIsNone(gap["remaining_required_subgroup"]["class_count"])
        self.assertEqual(gap["secondary_web_mirror_status"], "DIAGNOSTIC_ONLY_NOT_CANONICAL")
        self.assertTrue(gap["proxy_forbidden"])

    def test_products_add_one_school_row_and_preserve_fiscal(self):
        before = build_task192_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        after = build_task193_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(before["SCHOOL_INDICATOR_SERIES"]["row_count"], 1018)
        self.assertEqual(after["SCHOOL_INDICATOR_SERIES"]["row_count"], 1019)
        self.assertEqual(before["FISCAL_SERIES"]["row_count"], 61)
        self.assertEqual(after["FISCAL_SERIES"]["row_count"], 61)
        self.assertEqual(
            before["FISCAL_SERIES"]["content_sha256"],
            after["FISCAL_SERIES"]["content_sha256"],
        )
        self.assertFalse(after["SCHOOL_INDICATOR_SERIES"]["overlay_scope"]["class_count_materialized"])

    def test_network_q1_reduces_to_one_precise_gap_without_status_inflation(self):
        before = question_answerability(current_products(task193=False))
        after = question_answerability(current_products(task193=True))
        expected_counts = {
            "EXPLICIT_GAP": 2,
            "MATERIALIZED_ANSWERABLE": 27,
            "MATERIALIZED_PARTIAL": 9,
        }
        self.assertEqual(before["status_counts"], expected_counts)
        self.assertEqual(after["status_counts"], expected_counts)
        before_by_id = {row["question_id"]: row for row in before["questions"]}
        after_by_id = {row["question_id"]: row for row in after["questions"]}
        self.assertEqual(before_by_id["NETWORK_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(after_by_id["NETWORK_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(
            set(before_by_id["NETWORK_Q1"]["missing_or_insufficient_metrics"]),
            {"CLASS_COUNT", "SCHOOL_COUNT"},
        )
        self.assertEqual(
            after_by_id["NETWORK_Q1"]["missing_or_insufficient_metrics"],
            ["CLASS_COUNT"],
        )
        changed_statuses = {
            qid
            for qid in before_by_id
            if before_by_id[qid]["status"] != after_by_id[qid]["status"]
        }
        self.assertEqual(changed_statuses, set())
        self.assertEqual(after_by_id["FIN_Q4"]["status"], "MATERIALIZED_ANSWERABLE")

    def test_fail_closed_if_class_count_is_fabricated_or_proxy_guard_relaxed(self):
        obj = load_contract()
        obj["class_count_recovery"]["network_class_count"] = 999
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad_count.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task193Stop, "TASK193_NETWORK_CLASS_COUNT_MUST_BE_UNKNOWN"):
                load_contract(path)

        obj = load_contract()
        obj["class_count_recovery"]["proxy_forbidden"] = False
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad_proxy.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task193Stop, "TASK193_PROXY_GUARD"):
                load_contract(path)

    def test_canonical_evidence_preserves_gap(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["school_count"]["value"], 69)
        self.assertIsNone(e["class_count"]["network_value"])
        self.assertEqual(e["class_count"]["validated_ei29_class_count"], 294)
        self.assertEqual(e["class_count"]["official_turma_md5"], "438A3A3FC37F28E7E50E57D7CD8B9DAC")
        self.assertEqual(e["answerability"]["network_q1"], "MATERIALIZED_PARTIAL")
        self.assertEqual(e["answerability"]["remaining_missing_metrics"], ["CLASS_COUNT"])
        self.assertEqual(e["expected_products"]["school_indicator_series_row_count"], 1019)
        self.assertEqual(e["expected_products"]["fiscal_series_row_count"], 61)
        self.assertEqual(e["remote_effects"]["serving"], 0)

    def test_runtime_snapshot_probe(self):
        products = build_task193_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        print(
            "TASK193_RUNTIME_SNAPSHOTS="
            + json.dumps(
                {
                    "school_snapshot_id": products["SCHOOL_INDICATOR_SERIES"]["snapshot_id"],
                    "school_content_sha256": products["SCHOOL_INDICATOR_SERIES"]["content_sha256"],
                    "school_row_count": products["SCHOOL_INDICATOR_SERIES"]["row_count"],
                    "fiscal_snapshot_id": products["FISCAL_SERIES"]["snapshot_id"],
                    "fiscal_content_sha256": products["FISCAL_SERIES"]["content_sha256"],
                    "fiscal_row_count": products["FISCAL_SERIES"]["row_count"],
                    "class_count_gap": products["CLASS_COUNT_GAP"]["status"],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
