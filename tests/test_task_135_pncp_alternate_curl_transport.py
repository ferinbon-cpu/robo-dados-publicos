from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task135_pncp_alternate_curl_transport import (
    Task135Stop,
    build_curl_argv,
    load,
    validate_task135_contract,
)

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "config/task135_pncp_alternate_curl_transport.v1.json"


class TestTask135(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load(P)

    def test_design_is_offline(self):
        self.assertEqual("T0_OFFLINE_ALTERNATE_TRANSPORT_DESIGN_ONLY", self.c["mode"])
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task135_design"].values()))

    def test_curl_is_exact_one_get_no_redirect_no_retry(self):
        argv = build_curl_argv(self.c, "/tmp/task135.json")
        self.assertIn("--request", argv)
        self.assertEqual("GET", argv[argv.index("--request") + 1])
        self.assertEqual("0", argv[argv.index("--max-redirs") + 1])
        self.assertEqual("0", argv[argv.index("--retry") + 1])
        self.assertEqual(self.c["source"]["exact_url"], argv[-1])
        self.assertNotIn("-L", argv)

    def test_scope_widening_fails_closed(self):
        x = deepcopy(self.c)
        x["curl"]["max_requests"] = 2
        with self.assertRaisesRegex(Task135Stop, "TASK135_REQUESTS"):
            validate_task135_contract(x)

    def test_followup_and_identity_promotion_stay_blocked(self):
        self.assertFalse(self.c["followup_endpoints_authorized"])
        i = self.c["interpretation"]
        self.assertFalse(i["automatic_financial_identity"])
        self.assertFalse(i["automatic_transaction_identity"])
        self.assertFalse(i["automatic_supplier_linkage"])

    def test_raw_persistence_is_forbidden(self):
        h = self.c["local_handling"]
        self.assertFalse(h["raw_git_persistence"])
        self.assertFalse(h["raw_drive_persistence"])
        self.assertTrue(h["delete_raw_after_hash_and_parse"])


if __name__ == "__main__":
    unittest.main()
