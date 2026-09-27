from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "docs/evidence/TASK_134_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
BLOCK = ROOT / "docs/evidence/TASK_134_PRE_NETWORK_CONNECTOR_WORKFLOW_WRITE_BLOCK_0.8.0.json"
LIVE = ROOT / ".github/workflows/task-134-pncp-procurement-live-once.yml"


class TestTask134PreNetworkBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = json.loads(AUTH.read_text(encoding="utf-8"))
        cls.b = json.loads(BLOCK.read_text(encoding="utf-8"))

    def test_authorization_remains_unconsumed(self):
        self.assertIn(
            self.a["status"],
            {
                "AUTHORIZED_UNCONSUMED_PRE_NETWORK_CONNECTOR_WORKFLOW_WRITE_BLOCK",
                "ALT_TRANSPORT_ATTEMPT_CONSUMED_PRE_HTTP_SOURCE_READ_SCOPE_UNCONSUMED",
            },
        )
        self.assertFalse(self.a["authorization_consumed"])
        self.assertFalse(self.a["source_read_scope_consumed"])
        self.assertEqual(0, self.a["source_http_requests_emitted"])
        self.assertIsNone(self.a["consumed_by"])

    def test_owner_ten_tokens_do_not_expand_task133_bound(self):
        self.assertEqual(10, self.a["authorization_tokens_stated_by_owner"])
        self.assertEqual(1, self.a["authorization_tokens_effectively_consumable_in_this_task"])
        self.assertTrue(self.a["surplus_authorization_does_not_broaden_scope"])
        self.assertEqual(1, self.a["get_requests_max"])
        self.assertEqual(1, self.a["max_live_runs"])

    def test_block_is_pre_network_not_data_result(self):
        self.assertEqual("STOP_PRE_NETWORK_CONNECTOR_WORKFLOW_WRITE_BLOCK", self.b["result"])
        self.assertEqual(0, self.b["source_effects"]["pncp_http_requests_emitted"])
        self.assertFalse(self.b["epistemic_state"]["administrative_identifier_found"])
        self.assertFalse(self.b["epistemic_state"]["no_match_conclusion_created"])
        self.assertFalse(self.b["authorization_state"]["authorization_consumed"])

    def test_executable_workflow_was_not_created(self):
        self.assertFalse(LIVE.exists())


if __name__ == "__main__":
    unittest.main()
