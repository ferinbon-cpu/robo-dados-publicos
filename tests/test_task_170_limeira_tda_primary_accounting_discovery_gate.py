import json
import unittest
from pathlib import Path

from robo_dados_publicos.research.task170_limeira_tda_primary_accounting_discovery_gate import (
    Task170Stop,
    load_gate,
    validate_gate,
)


GATE = Path("config/task170_limeira_tda_primary_accounting_discovery_gate.v1.json")


class TestTask170LimeiraTdaPrimaryAccountingDiscoveryGate(unittest.TestCase):
    def test_gate_passes_and_selects_tda(self):
        result = validate_gate(GATE)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["selected_source"], "LIMEIRA_TDA_PORTAL")
        self.assertFalse(result["live_authorized"])
        self.assertEqual(result["request_budget"], 1)
        self.assertEqual(result["redirects_followed_max"], 0)

    def test_exact_known_route_is_pinned(self):
        obj = load_gate(GATE)
        req = obj["future_live_gate"]["exact_first_request"]
        self.assertEqual(req["method"], "GET")
        self.assertEqual(
            req["url"],
            "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418",
        )

    def test_fresh_authorization_is_required(self):
        obj = load_gate(GATE)
        live = obj["future_live_gate"]
        self.assertFalse(live["authorized_now"])
        self.assertTrue(live["fresh_explicit_owner_authorization_required"])
        self.assertEqual(
            live["authorization_scope_if_granted"]["host"],
            "transparencia.limeira.sp.gov.br",
        )

    def test_no_reverse_engineering_or_access_bypass(self):
        obj = load_gate(GATE)
        forbidden = set(obj["forbidden_actions"])
        for item in (
            "FOLLOW_REDIRECT",
            "AUTHENTICATE",
            "SUBMIT_FORM",
            "EXECUTE_JAVASCRIPT",
            "BYPASS_CAPTCHA",
            "GUESS_ENDPOINT",
            "BRUTE_FORCE_PATHS",
        ):
            self.assertIn(item, forbidden)

    def test_tce_is_corroboration_only(self):
        obj = load_gate(GATE)
        tce = obj["fallback_after_blocked_tda"]["TCE_SP_DESPESAS"]
        self.assertEqual(tce["role"], "CONTROL_PRIMARY_CORROBORATION_ONLY")
        self.assertIn("ficha_or_dotacao", tce["missing_for_policy_discovery"])

    def test_tampered_live_authorization_fails_closed(self):
        obj = json.loads(GATE.read_text(encoding="utf-8"))
        obj["future_live_gate"]["authorized_now"] = True
        temp = Path("tests/.task170_tampered_gate.json")
        try:
            temp.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaises(Task170Stop):
                validate_gate(temp)
        finally:
            if temp.exists():
                temp.unlink()


if __name__ == "__main__":
    unittest.main()
