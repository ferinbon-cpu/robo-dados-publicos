from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_public_readiness_audit.py"
spec = importlib.util.spec_from_file_location("public_readiness", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _codes(text: str) -> set[str]:
    return {code for code, _line in mod.scan_text(text)}


class PublicReadinessAuditTests(unittest.TestCase):
    def test_known_secret_signatures_are_detected_without_literal_fixture_in_source(self) -> None:
        github_token = "gh" + "p_" + ("Ab9" * 12)
        google_secret = "GOC" + "SPX-" + ("aB9_" * 7)
        google_key = "AI" + "za" + ("A1_b" * 9)
        aws_key = "AK" + "IA" + ("A1B2" * 4)
        private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
        codes = _codes("\n".join([github_token, google_secret, google_key, aws_key, private_key_header]))
        self.assertIn("GITHUB_TOKEN_PREFIX", codes)
        self.assertIn("GOOGLE_OAUTH_CLIENT_SECRET", codes)
        self.assertIn("GOOGLE_API_KEY", codes)
        self.assertIn("AWS_ACCESS_KEY_ID", codes)
        self.assertIn("PRIVATE_KEY_HEADER", codes)

    def test_sensitive_literal_detects_value_but_not_fixture_placeholder(self) -> None:
        realish = '"refresh' + '_token": "1//' + ("AbCd9_" * 8) + '"'
        placeholder = '"client' + '_secret": "fixture-client-secret"'
        self.assertIn("SENSITIVE_LITERAL_REFRESH_TOKEN", _codes(realish))
        self.assertFalse(_codes(placeholder))

    def test_uppercase_env_assignment_is_detected_but_env_reference_is_not(self) -> None:
        realish = "GOOGLE_DRIVE_REFRESH_TOKEN=1//" + ("AbCd9_" * 8)
        placeholder = "GOOGLE_DRIVE_REFRESH_TOKEN=${GOOGLE_DRIVE_REFRESH_TOKEN}"
        self.assertIn("SENSITIVE_ENV_ASSIGNMENT", _codes(realish))
        self.assertFalse(_codes(placeholder))

    def test_variable_to_variable_assignment_is_not_a_secret_literal(self) -> None:
        text = "client_secret=credentials.client_secret\nrefresh_token=payload.refresh_token"
        self.assertFalse(_codes(text))

    def test_env_example_is_not_a_sensitive_filename(self) -> None:
        findings = mod._suspicious_path_findings([".env.example"])
        self.assertEqual([], findings)

    def test_real_env_and_private_key_filename_require_review(self) -> None:
        findings = mod._suspicious_path_findings([".env", "config/service.key"])
        self.assertEqual({".env", "config/service.key"}, {item["path"] for item in findings})

    def test_audit_source_never_emits_matched_secret_value(self) -> None:
        token = "gh" + "o_" + ("Xy7" * 12)
        findings = mod.scan_text(token)
        self.assertTrue(findings)
        self.assertNotIn(token, repr(findings))


if __name__ == "__main__":
    unittest.main()
