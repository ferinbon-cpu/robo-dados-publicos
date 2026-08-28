import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_m8_readonly_secret_cloudshell",
    ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class TestM8ReadonlySecretBootstrapCloudShell(unittest.TestCase):
    def test_desktop_client_payload_contains_only_expected_oauth_shape(self):
        payload = mod.build_desktop_client_payload(
            "client-id.example.apps.googleusercontent.com",
            "fixture-secret",
            "robo-dados-publicos-pessoal",
        )
        installed = payload["installed"]
        self.assertEqual("client-id.example.apps.googleusercontent.com", installed["client_id"])
        self.assertEqual("fixture-secret", installed["client_secret"])
        self.assertEqual(["http://localhost"], installed["redirect_uris"])
        self.assertEqual(mod.TOKEN_URL, installed["token_uri"])

    def test_adc_must_be_authorized_user_for_exact_client(self):
        token = mod.validate_adc_payload(
            {
                "type": "authorized_user",
                "client_id": "client-id",
                "refresh_token": "fixture-refresh-token",
            },
            client_id="client-id",
        )
        self.assertEqual("fixture-refresh-token", token)

        with self.assertRaisesRegex(mod.CloudShellReadonlyBootstrapError, "STOP_READONLY_ADC_CLIENT_ID_MISMATCH"):
            mod.validate_adc_payload(
                {
                    "type": "authorized_user",
                    "client_id": "other-client",
                    "refresh_token": "fixture-refresh-token",
                },
                client_id="client-id",
            )

    def test_source_uses_remote_gcloud_flow_and_isolates_adc(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py").read_text(encoding="utf-8")
        self.assertIn('"--no-launch-browser"', source)
        self.assertIn('env["CLOUDSDK_CONFIG"] = str(config_dir)', source)
        self.assertIn('f"--scopes={READONLY_SCOPE}"', source)
        self.assertIn('f"--client-id-file={client_file}"', source)
        self.assertNotIn("webbrowser.open", source)
        self.assertNotIn("HTTPServer", source)

    def test_source_never_places_refresh_token_or_client_secret_in_cli_args(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py").read_text(encoding="utf-8")
        self.assertIn("getpass.getpass", source)
        self.assertIn("input_text=refresh_token", source)
        self.assertNotIn('"--body", refresh_token', source)
        self.assertNotIn("print(client_secret", source)
        self.assertNotIn("print(refresh_token", source)

    def test_scope_proof_is_fail_closed_and_no_execution_is_authorized(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py").read_text(encoding="utf-8")
        self.assertIn('scopes == {READONLY_SCOPE}', source)
        self.assertIn('"scope_proof": "tokeninfo_exact"', source)
        self.assertIn('"m8_executed": False', source)
        self.assertIn('"m8_no_click_authorized": False', source)
        self.assertIn('"publication_authorized": False', source)
        self.assertIn('"future_batch_execution_authorized": False', source)


if __name__ == "__main__":
    unittest.main()
