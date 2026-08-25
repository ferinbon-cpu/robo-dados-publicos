from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_artifact_access_boundary.json"


class TestM7SiopeArtifactAccessBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_public_metadata_does_not_imply_public_artifact(self):
        self.assertEqual(self.cfg["product_page_status"], "PUBLIC_VERIFIED")
        self.assertEqual(self.cfg["artifact_metadata_status"], "PUBLIC_VERIFIED")
        self.assertEqual(self.cfg["anonymous_export_status"], "AUTHENTICATION_BOUNDARY_OBSERVED")
        self.assertEqual(self.cfg["artifact_access_status"], "NOT_PROVEN_PUBLIC_ANONYMOUS")
        self.assertEqual(self.cfg["acquisition_route_status"], "UNPROVEN_BEYOND_AUTHENTICATION_BOUNDARY")

    def test_authentication_is_not_automated_or_captured(self):
        auth = self.cfg["authentication_boundary"]
        self.assertEqual(auth["provider_label"], "gov.br")
        self.assertEqual(auth["observed_login_host"], "www.fnde.gov.br")
        self.assertEqual(auth["observed_login_path"], "/plataforma-antonieta-de-barros/login")
        self.assertEqual(auth["observed_query_keys"], ["returnUrl"])
        for key in (
            "credential_capture",
            "session_cookie_capture",
            "authenticated_browser_automation",
            "login_click",
            "captcha_bypass",
        ):
            self.assertEqual(auth[key], "PROHIBITED")

    def test_operational_authorizations_remain_closed(self):
        self.assertFalse(self.cfg["collection_authorized"])
        self.assertFalse(self.cfg["processing_authorized"])
        self.assertFalse(self.cfg["recurrence_authorized"])
        self.assertFalse(self.cfg["schedule_enabled"])
        prohibited = set(self.cfg["prohibited_next_actions"])
        self.assertIn("GUESS_DOWNLOAD_URL_FROM_STORAGE_PATH", prohibited)
        self.assertIn("AUTOMATE_GOV_BR_LOGIN", prohibited)
        self.assertIn("REUSE_PERSONAL_SESSION", prohibited)

    def test_next_actions_are_design_or_public_discovery_only(self):
        self.assertEqual(
            self.cfg["allowed_next_actions"],
            [
                "SEARCH_OFFICIAL_PUBLIC_DOCUMENTED_EXPORT_OR_API",
                "DESIGN_HUMAN_AUTHORIZED_AUTHENTICATED_FLOW_WITHOUT_CREDENTIAL_CAPTURE",
            ],
        )


if __name__ == "__main__":
    unittest.main()
