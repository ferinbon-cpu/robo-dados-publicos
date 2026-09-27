import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.research.task170_limeira_tda_accounting_discovery_gate import (
    DEFAULT_CONTRACT,
    Task170Stop,
    validate_contract,
)


def _base():
    return json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))


class TestTask170LimeiraTdaAccountingDiscoveryGate(unittest.TestCase):
    def _write(self, obj):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "task170.json"
        path.write_text(json.dumps(obj), encoding="utf-8")
        return path

    def test_task170_contract_passes(self):
        result = validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["selected_source"], "LIMEIRA_TDA_PORTAL")
        self.assertIs(result["live_authorized"], False)
        self.assertEqual(result["network_requests"], 0)

    def test_task170_cannot_authorize_live(self):
        obj = _base()
        obj["authorization_boundary"]["live_discovery_authorized_now"] = True
        with self.assertRaisesRegex(Task170Stop, "TASK170_LIVE_BOUNDARY"):
            validate_contract(self._write(obj))

    def test_task170_rejects_wrong_source(self):
        obj = _base()
        obj["selected_source"]["source_id"] = "TCE_SP_2026_BULK"
        with self.assertRaisesRegex(Task170Stop, "TASK170_SOURCE"):
            validate_contract(self._write(obj))

    def test_task170_rejects_endpoint_guessing_permission(self):
        obj = _base()
        obj["future_live_discovery_gate"]["forbidden_discovery"].remove("endpoint_guessing")
        with self.assertRaisesRegex(Task170Stop, "TASK170_FORBIDDEN_DISCOVERY_MISSING"):
            validate_contract(self._write(obj))

    def test_task170_requires_blocked_access_not_no_data(self):
        obj = _base()
        obj["future_live_discovery_gate"]["access_barrier_semantics"][
            "redirect_to_login_logout_root_or_session_barrier"
        ] = "NO_DATA"
        with self.assertRaisesRegex(Task170Stop, "TASK170_ACCESS_SEMANTICS"):
            validate_contract(self._write(obj))

    def test_task170_rejects_retry(self):
        obj = _base()
        obj["future_live_discovery_gate"]["request_budget"]["retry"] = 1
        with self.assertRaisesRegex(Task170Stop, "TASK170_RETRY_REDIRECT"):
            validate_contract(self._write(obj))

    def test_task170_preserves_unknown_financial_identity(self):
        obj = _base()
        obj["scientific_guards"]["current_financial_identity"] = "PROVEN"
        with self.assertRaisesRegex(Task170Stop, "TASK170_FINANCIAL_STATE"):
            validate_contract(self._write(obj))

    def test_task170_preserves_weak_join_guards(self):
        obj = _base()
        obj["promotion_preconditions_after_future_route_discovery"]["weak_joins_forbidden"].remove(
            "semantic_similarity"
        )
        with self.assertRaisesRegex(Task170Stop, "TASK170_WEAK_JOIN_GUARD"):
            validate_contract(self._write(obj))


if __name__ == "__main__":
    unittest.main()
