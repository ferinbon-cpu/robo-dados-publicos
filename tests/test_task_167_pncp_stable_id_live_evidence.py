import json
import unittest
from pathlib import Path


EVIDENCE = Path("docs/evidence/TASK_167_PNCP_STABLE_ID_DIRECT_JSON_TRAVERSAL_0.8.0.json")


def load():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


class TestTask167PncpStableIdLiveEvidence(unittest.TestCase):
    def test_task167_live_evidence_is_fail_closed(self):
        evidence = load()
        self.assertEqual(
            evidence["task"],
            "TASK_167_PNCP_STABLE_ID_DIRECT_JSON_TRAVERSAL",
        )
        self.assertEqual(evidence["execution"]["workflow_conclusion"], "success")
        self.assertFalse(evidence["execution"]["raw_payload_persisted"])
        self.assertEqual(evidence["adjudication"]["requests_attempted"], 10)
        self.assertEqual(evidence["adjudication"]["successful_json_bodies"], 0)
        self.assertEqual(evidence["adjudication"]["candidate_accounting_signals"], 0)
        self.assertFalse(
            evidence["adjudication"]["transport_or_http_failure_is_no_data"]
        )
        self.assertFalse(evidence["adjudication"]["pncp_no_data_created"])
        self.assertFalse(evidence["adjudication"]["eiti_financial_identity_proven"])
        self.assertFalse(evidence["adjudication"]["eiti_transaction_identity_proven"])
        self.assertEqual(
            evidence["adjudication"]["scientific_state"],
            "UNCHANGED_UNKNOWN_FINANCIAL_IDENTITY",
        )

    def test_all_task167_routes_are_recorded_as_unavailable_not_absent(self):
        evidence = load()
        expected = {
            "DETAIL",
            "ITEMS",
            "HISTORY",
            "BUDGET_SOURCES",
            "LINKED_CONTRACTS",
        }
        for target in evidence["targets"]:
            self.assertEqual(set(target["routes"]), expected)
            self.assertFalse(target["detail_identity_validated_this_run"])
            for route in target["routes"].values():
                self.assertEqual(route["bytes_received"], 0)
                self.assertIn(route["http_status"], {502, 503})
                self.assertEqual(
                    route["status"],
                    "SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE",
                )


if __name__ == "__main__":
    unittest.main()
