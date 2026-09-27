from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_ws_public_discovery_design.json"


class TestM7SiopeWsPublicDiscoveryDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_design_is_public_read_only_and_does_not_guess(self):
        self.assertEqual(self.cfg["mode"], "PUBLIC_READ_ONLY_DISCOVERY")
        rules = self.cfg["discovery_rules"]
        self.assertEqual(rules["methods"], ["GET"])
        self.assertTrue(rules["follow_only_explicit_declared_links"])
        self.assertFalse(rules["guess_endpoint_paths"])
        self.assertFalse(rules["submit_forms"])

    def test_authentication_and_captcha_remain_prohibited(self):
        rules = self.cfg["discovery_rules"]
        for key in ("bypass_captcha", "authenticate", "capture_credentials", "capture_cookies"):
            self.assertFalse(rules[key])

    def test_hosts_are_exact_and_artifact_download_is_closed(self):
        self.assertEqual(self.cfg["allowed_hosts"], ["www.fnde.gov.br", "webservice.fnde.gov.br"])
        self.assertFalse(self.cfg["discovery_rules"]["download_artifacts"])
        self.assertFalse(self.cfg["collection_authorized"])
        self.assertFalse(self.cfg["processing_authorized"])
        self.assertFalse(self.cfg["recurrence_authorized"])
        self.assertFalse(self.cfg["schedule_enabled"])

    def test_classification_rejects_generic_castor_file_delivery(self):
        rules = self.cfg["classification_rules"]
        self.assertEqual(rules["excluded_route_prefixes"], ["/webservices/castor/"])
        self.assertEqual(rules["endpoint_specific_hosts"], ["webservice.fnde.gov.br"])
        self.assertEqual(rules["endpoint_specific_markers"], ["ws-siope", "wsdl", "soap"])
        self.assertTrue(rules["generic_webservices_path_is_not_endpoint"])
        self.assertTrue(rules["installer_anchor_is_not_endpoint"])

    def test_ws_siope_clue_does_not_claim_endpoint_contract(self):
        self.assertIn("WS-SIOPE", self.cfg["official_clues"][0]["observed_text"])
        self.assertEqual(
            self.cfg["success_condition"],
            "EXPLICIT_PUBLIC_WS_SIOPE_ENDPOINT_OR_OFFICIAL_DOCUMENTATION_OBSERVED",
        )


if __name__ == "__main__":
    unittest.main()
