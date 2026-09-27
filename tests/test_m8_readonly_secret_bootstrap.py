import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_m8_readonly_secret",
    ROOT / "scripts" / "bootstrap_m8_readonly_secret.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class TestM8ReadonlySecretBootstrap(unittest.TestCase):
    def test_exact_readonly_scope_is_accepted(self):
        token = mod.validate_token_payload(
            {
                "refresh_token": "fixture-refresh-token",
                "scope": mod.READONLY_SCOPE,
            }
        )
        self.assertEqual("fixture-refresh-token", token)

    def test_extra_scope_is_rejected_fail_closed(self):
        with self.assertRaisesRegex(mod.ReadonlySecretBootstrapError, "STOP_READONLY_TOKEN_SCOPE_NOT_EXACT"):
            mod.validate_token_payload(
                {
                    "refresh_token": "fixture-refresh-token",
                    "scope": mod.READONLY_SCOPE + " https://www.googleapis.com/auth/drive.file",
                }
            )

    def test_missing_scope_or_refresh_token_is_rejected(self):
        with self.assertRaisesRegex(mod.ReadonlySecretBootstrapError, "STOP_READONLY_TOKEN_SCOPE_MISSING"):
            mod.validate_token_payload({"refresh_token": "fixture-refresh-token"})
        with self.assertRaisesRegex(mod.ReadonlySecretBootstrapError, "STOP_READONLY_REFRESH_TOKEN_MISSING"):
            mod.validate_token_payload({"scope": mod.READONLY_SCOPE})

    def test_helper_never_uses_secret_value_as_cli_argument(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret.py").read_text(encoding="utf-8")
        self.assertIn('input_text=refresh_token', source)
        self.assertNotIn('"--body", refresh_token', source)
        self.assertIn('"secret_value_exposed": False', source)
        self.assertIn('"m8_no_click_authorized": False', source)

    def test_windows_wrapper_prompts_secret_securely_and_clears_env(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret.ps1").read_text(encoding="utf-8")
        self.assertIn("-AsSecureString", source)
        self.assertIn("Remove-Item Env:GOOGLE_DRIVE_CLIENT_SECRET", source)
        self.assertNotIn("Write-Host $clientSecret", source)


if __name__ == "__main__":
    unittest.main()
