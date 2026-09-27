import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "github_m8_readonly_credential_capability_gate",
    ROOT / "scripts" / "github_m8_readonly_credential_capability_gate.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class TestM8ReadonlyCredentialCapability(unittest.TestCase):
    def test_exact_scope_helper_accepts_only_drive_readonly(self):
        self.assertTrue(mod.exact_scope(mod.READONLY_SCOPE))
        self.assertFalse(mod.exact_scope(mod.READONLY_SCOPE + " https://www.googleapis.com/auth/drive.file"))
        self.assertFalse(mod.exact_scope(""))
        self.assertFalse(mod.exact_scope(None))

    @patch.object(mod, "_get_json")
    @patch.object(mod, "_post_form")
    def test_capability_proof_passes_with_exact_scope_and_exposes_no_secret(self, post_form, get_json):
        post_form.return_value = {
            "access_token": "fixture-access-token",
            "scope": mod.READONLY_SCOPE,
        }
        get_json.return_value = {"scope": mod.READONLY_SCOPE}

        result = mod.prove_capability(
            client_id="fixture-client-id",
            client_secret="fixture-client-secret",
            refresh_token="fixture-refresh-token",
        )

        self.assertEqual("PASS_M8_READONLY_CREDENTIAL_CAPABILITY", result["status"])
        self.assertEqual("oauth_refresh_and_tokeninfo_exact", result["scope_proof"])
        self.assertEqual(0, result["drive_api_request_count"])
        self.assertEqual(0, result["drive_write_count"])
        self.assertFalse(result["secret_values_exposed"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["m8_no_click_authorized"])

    @patch.object(mod, "_get_json")
    @patch.object(mod, "_post_form")
    def test_extra_scope_fails_closed(self, post_form, get_json):
        post_form.return_value = {"access_token": "fixture-access-token"}
        get_json.return_value = {
            "scope": mod.READONLY_SCOPE + " https://www.googleapis.com/auth/drive.file"
        }
        with self.assertRaisesRegex(
            mod.ReadonlyCredentialCapabilityError,
            "STOP_READONLY_TOKENINFO_SCOPE_NOT_EXACT",
        ):
            mod.prove_capability(
                client_id="fixture-client-id",
                client_secret="fixture-client-secret",
                refresh_token="fixture-refresh-token",
            )

    def test_source_contains_no_drive_api_endpoint_or_secret_prints(self):
        source = (ROOT / "scripts" / "github_m8_readonly_credential_capability_gate.py").read_text(encoding="utf-8")
        self.assertNotIn("www.googleapis.com/drive/", source)
        self.assertNotIn("print(client_secret", source)
        self.assertNotIn("print(refresh_token", source)
        self.assertNotIn("print(access_token", source)


if __name__ == "__main__":
    unittest.main()
