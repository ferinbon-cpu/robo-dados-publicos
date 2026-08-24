import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.observability.cards import (
    build_observability_report,
    render_markdown,
    write_report_bundle,
)


class TestObservabilityCards(unittest.TestCase):
    def payload(self):
        return {
            "status": "PASS_GITHUB_SOURCE_COLLECTION_GATE",
            "software_version": "0.6.3",
            "release_status": "CANDIDATE",
            "state_source": "REMOTE_EXISTING",
            "state_remote_mode": "REPLACED",
            "append_only_log_created": True,
            "remote_identifiers_exposed": False,
            "secret_values_exposed": False,
            "checks": {"runtime": True, "qa": True},
            "source_collection": {
                "status": "PASS",
                "inventory": {"enabled": 1},
                "results": [{
                    "source_id": "PUBLIC_SOURCE",
                    "status": "DOWNLOADED_NEW",
                    "http_status": 200,
                    "content_type": "application/pdf",
                    "bytes": 123,
                    "sha256": "abc",
                    "remote_id": "must-not-propagate",
                }],
            },
            "client_secret": "must-not-propagate",
        }

    def test_pass_payload_builds_healthy_cards(self):
        report = build_observability_report(self.payload())
        self.assertEqual("HEALTHY", report["overall_health"])
        self.assertEqual(2, report["run"]["checks_passed"])
        self.assertEqual(1, report["source"]["enabled_sources"])
        self.assertEqual("PASS", report["privacy"]["status"])

    def test_allowlist_projection_drops_secrets_and_remote_ids(self):
        serialized = json.dumps(build_observability_report(self.payload()))
        self.assertNotIn("must-not-propagate", serialized)
        self.assertNotIn("client_secret", serialized)
        self.assertNotIn('"remote_id":', serialized)

    def test_infrastructure_only_source_is_explicit(self):
        payload = self.payload()
        payload["source_collection"] = "NOT_CONFIGURED"
        report = build_observability_report(payload)
        self.assertEqual("NOT_CONFIGURED", report["source"]["health"])
        self.assertEqual(0, report["source"]["enabled_sources"])

    def test_unsafe_contract_stops_report(self):
        payload = self.payload()
        payload["secret_values_exposed"] = True
        report = build_observability_report(payload)
        self.assertEqual("STOPPED", report["overall_health"])
        self.assertEqual("STOP_UNSAFE_INPUT_CONTRACT", report["privacy"]["status"])

    def test_markdown_is_operator_readable(self):
        markdown = render_markdown(build_observability_report(self.payload()))
        self.assertIn("Relatório de observabilidade", markdown)
        self.assertIn("HEALTHY", markdown)
        self.assertIn("PUBLIC_SOURCE", json.dumps(build_observability_report(self.payload())))

    def test_bundle_is_immutable_run_artifact_shape(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "observability"
            write_report_bundle(self.payload(), out)
            expected = {
                out / "report.json",
                out / "report.md",
                out / "cards" / "run.json",
                out / "cards" / "source.json",
                out / "cards" / "metrics.json",
            }
            self.assertTrue(all(path.is_file() for path in expected))

    def test_invalid_payload_type_is_rejected(self):
        with self.assertRaises(TypeError):
            build_observability_report([])


if __name__ == "__main__":
    unittest.main()
