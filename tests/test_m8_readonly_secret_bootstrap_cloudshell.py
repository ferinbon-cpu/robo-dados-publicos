import importlib.util
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_m8_readonly_secret_cloudshell",
    ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class TestM8ReadonlySecretBootstrapCloudShell(unittest.TestCase):
    def test_cloudshell_redirect_uri_is_https_and_exact_callback(self):
        uri = mod.cloudshell_redirect_uri(
            port=8080,
            web_host="example-default.cs-us-central1-b-user.cloudshell.dev",
        )
        self.assertEqual(
            "https://8080-example-default.cs-us-central1-b-user.cloudshell.dev/oauth2callback",
            uri,
        )
        with self.assertRaisesRegex(mod.CloudShellReadonlyBootstrapError, "STOP_CLOUDSHELL_WEB_HOST_UNEXPECTED"):
            mod.cloudshell_redirect_uri(port=8080, web_host="example.invalid")

    def test_authorization_url_requests_only_drive_readonly(self):
        uri = mod.cloudshell_redirect_uri(
            port=8080,
            web_host="example-default.cs-us-central1-b-user.cloudshell.dev",
        )
        url = mod.build_authorization_url(
            client_id="client-id.apps.googleusercontent.com",
            redirect_uri=uri,
            state="fixture-state",
        )
        query = parse_qs(urlparse(url).query)
        self.assertEqual([mod.READONLY_SCOPE], query["scope"])
        self.assertEqual([uri], query["redirect_uri"])
        self.assertEqual(["offline"], query["access_type"])
        self.assertEqual(["consent"], query["prompt"])
        self.assertEqual(["fixture-state"], query["state"])

    def test_token_payload_requires_refresh_token_and_exact_scope(self):
        access_token, refresh_token = mod.validate_token_payload(
            {
                "access_token": "fixture-access-token",
                "refresh_token": "fixture-refresh-token",
                "scope": mod.READONLY_SCOPE,
            }
        )
        self.assertEqual("fixture-access-token", access_token)
        self.assertEqual("fixture-refresh-token", refresh_token)

        with self.assertRaisesRegex(mod.CloudShellReadonlyBootstrapError, "STOP_READONLY_TOKEN_SCOPE_NOT_EXACT"):
            mod.validate_token_payload(
                {
                    "access_token": "fixture-access-token",
                    "refresh_token": "fixture-refresh-token",
                    "scope": mod.READONLY_SCOPE + " https://www.googleapis.com/auth/drive.file",
                }
            )

    def test_source_uses_web_preview_callback_not_broken_gcloud_remote_flag(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py").read_text(encoding="utf-8")
        self.assertIn("HTTPServer", source)
        self.assertIn('CALLBACK_PATH = "/oauth2callback"', source)
        self.assertIn('host.endswith("cloudshell.dev")', source)
        self.assertNotIn('"--no-launch-browser"', source)
        self.assertNotIn('"--no-browser"', source)
        self.assertNotIn("application-default", source)

    def test_source_never_places_secret_values_in_cli_args(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py").read_text(encoding="utf-8")
        self.assertIn("getpass.getpass", source)
        self.assertIn("input_text=value", source)
        self.assertNotIn('"--body", refresh_token', source)
        self.assertNotIn('"--body", client_secret', source)
        self.assertNotIn("print(client_secret", source)
        self.assertNotIn("print(refresh_token", source)

    def test_dedicated_readonly_secret_names_are_isolated(self):
        self.assertEqual(
            {
                "GOOGLE_DRIVE_READONLY_CLIENT_ID",
                "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
                "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
            },
            set(mod.SECRET_NAMES.values()),
        )

    def test_scope_proof_is_fail_closed_and_no_execution_is_authorized(self):
        source = (ROOT / "scripts" / "bootstrap_m8_readonly_secret_cloudshell.py").read_text(encoding="utf-8")
        self.assertIn('scopes == {READONLY_SCOPE}', source)
        self.assertIn('"scope_proof": "token_response_and_tokeninfo_exact"', source)
        self.assertIn('"m8_executed": False', source)
        self.assertIn('"m8_no_click_authorized": False', source)
        self.assertIn('"publication_authorized": False', source)
        self.assertIn('"future_batch_execution_authorized": False', source)


if __name__ == "__main__":
    unittest.main()
