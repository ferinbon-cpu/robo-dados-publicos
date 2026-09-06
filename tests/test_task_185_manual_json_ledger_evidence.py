import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import (
    _transition_report,
    _with_catalog,
    build_task184_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_185_MANUAL_JSON_LEDGER_MATERIALIZATION_0.8.0.json"
CONFIG = ROOT / "config/task185_tcesp_json_api_2026.v1.json"
GENERATED_AT = "2026-09-06T13:34:30.586057+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask185ManualJsonLedgerEvidence(unittest.TestCase):
    def evidence(self):
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_real_custody_and_ledger_counts_are_self_consistent(self):
        e = self.evidence()
        self.assertEqual(e["status"], "PASS_REAL_JAN_JUL_LEDGER_MATERIALIZED")
        self.assertEqual(e["source"]["months_validated"], [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(
            sum(x["rows"] for x in e["source"]["month_files"].values()),
            39779,
        )
        self.assertEqual(e["source"]["validated_total_rows"], 39779)
        self.assertEqual(
            sum(e["accounting_ledger"]["stage_counts"].values()),
            39779,
        )
        self.assertEqual(e["accounting_ledger"]["row_count"], 39779)
        self.assertEqual(e["accounting_ledger"]["snapshot_id"], "8c898422c61137c6a51755ec")
        self.assertEqual(
            e["accounting_ledger"]["content_sha256"],
            "8c898422c61137c6a51755ec5fe14a0861eb335ceb26797bcf4bef49123652c8",
        )
        self.assertFalse(e["source"]["august"]["cryptographically_proven_empty"])
        self.assertEqual(e["remote_effects"]["source_network_gets_for_manual_intake"], 0)
        self.assertEqual(e["remote_effects"]["drive_overwrites"], 0)
        self.assertEqual(e["remote_effects"]["serving"], 0)

    def test_config_matches_observed_time_semantics(self):
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        provided = set(cfg["source_capabilities"]["provided"])
        missing = set(cfg["source_capabilities"]["not_provided"])
        self.assertIn("EXPENSE_ISSUE_DATE", provided)
        self.assertIn("EVENT_MONTH", provided)
        self.assertNotIn("EVENT_DATE", provided)
        self.assertIn("EVENT_DATE", missing)
        self.assertTrue(
            cfg["source"]["current_2026_route_status"].startswith(
                "PROVEN_VALID_BY_OWNER_SUPPLIED_JAN_JUL_BODIES"
            )
        )

    def test_current_answerability_contract_reproduces_eight_changes(self):
        e = self.evidence()
        bundle = build_task184_bundle(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        before = bundle["answerability"]["final"]

        ledger_summary = {
            "product_name": "ACCOUNTING_LEDGER",
            "product_schema": "ACCOUNTING_LEDGER_V1",
            "snapshot_id": e["accounting_ledger"]["snapshot_id"],
            "content_sha256": e["accounting_ledger"]["content_sha256"],
            "row_count": e["accounting_ledger"]["row_count"],
            "generated_at": GENERATED_AT,
            "software_version": SOFTWARE_VERSION,
            # Raw source rows are intentionally not committed to Git. The
            # answerability recipes involved here are capability-gated.
            "rows": [],
            "capabilities": e["accounting_ledger"]["capabilities"],
            "observed_stages": sorted(e["accounting_ledger"]["stage_counts"]),
        }
        substantive = {
            k: v
            for k, v in bundle["products"].items()
            if k != "QUERY_PRODUCT_CATALOG"
        }
        products = _with_catalog(
            {**substantive, "ACCOUNTING_LEDGER": ledger_summary},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        after = question_answerability(products)
        gain = _transition_report(before, after)

        self.assertEqual(before["status_counts"], e["answerability"]["before_status_counts"])
        self.assertEqual(after["status_counts"], e["answerability"]["after_status_counts"])
        self.assertEqual(gain["changed_question_count"], 8)
        self.assertEqual(gain["changes"], e["answerability"]["changes"])

        by_id = {row["question_id"]: row for row in after["questions"]}
        self.assertEqual(by_id["ACC_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["ACC_Q2"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["ACC_Q3"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["PROC_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["CTRL_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["INFRA_Q2"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["PLAN_Q3"]["status"], "MATERIALIZED_PARTIAL")


if __name__ == "__main__":
    unittest.main()
