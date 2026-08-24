import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.observability import SourceCard
from robo_dados_publicos.observability.report import (
    build_observability_report,
    render_markdown,
    write_report_bundle,
)


class TestObservabilityReport(unittest.TestCase):
    def payload(self, **overrides):
        data = {
            "status": "PASS_GITHUB_LIVE_GATE",
            "software_version": "0.6.3",
            "release_status": "CANDIDATE",
            "run_id": 17,
            "started_at": "2026-08-24T20:00:00+00:00",
            "finished_at": "2026-08-24T20:00:10+00:00",
            "state_source": "REMOTE_EXISTING",
            "state_remote_mode": "REPLACED",
            "append_only_log_created": True,
            "remote_identifiers_exposed": False,
            "secret_values_exposed": False,
            "checks": {"runtime": True, "qa": True},
            "source_collection": "NOT_CONFIGURED",
            "client_secret": "must-not-propagate",
        }
        data.update(overrides)
        return data

    def source_card(self):
        return SourceCard(
            source_id="PUBLIC_SOURCE",
            institution="Public institution",
            source_url="https://example.test/source.pdf",
            formats=("application/pdf",),
            periodicity="one_time_manual_gate",
            scope="test",
            expected_update_interval_hours=None,
            fields=("document_content",),
            license="NOT_DECLARED",
            risks=("SCHEMA_CHANGE",),
            owner="ROBO_DADOS_PUBLICOS",
        )

    def source_collection(self):
        return {
            "status": "PASS",
            "inventory": {"enabled": 1},
            "results": [
                {
                    "source_id": "PUBLIC_SOURCE",
                    "status": "DOWNLOADED_NEW",
                    "http_status": 200,
                    "content_type": "application/pdf",
                    "bytes": 123,
                    "sha256": "hash-must-not-propagate",
                    "remote_id": "remote-must-not-propagate",
                }
            ],
        }

    def test_pass_payload_builds_healthy_operator_report(self):
        report = build_observability_report(self.payload())
        self.assertEqual("HEALTHY", report["overall_health"])
        self.assertEqual(2, report["run"]["checks_passed"])
        self.assertEqual("NOT_CONFIGURED", report["source_execution"]["health"])
        self.assertEqual("PASS", report["privacy"]["status"])
        self.assertEqual(10.0, report["run"]["run_contract"]["latency_seconds"])

    def test_allowlist_projection_drops_secrets_hashes_and_remote_ids(self):
        payload = self.payload(source_collection=self.source_collection())
        serialized = json.dumps(build_observability_report(payload, source_card=self.source_card()))
        self.assertNotIn("must-not-propagate", serialized)
        self.assertNotIn("client_secret", serialized)
        self.assertNotIn("remote_id", serialized)
        self.assertNotIn("hash-must-not-propagate", serialized)
        self.assertIn("integrity_verified", serialized)

    def test_source_contract_and_execution_are_separate(self):
        payload = self.payload(source_collection=self.source_collection())
        report = build_observability_report(payload, source_card=self.source_card())
        self.assertEqual("PUBLIC_SOURCE", report["source_contract"]["source_id"])
        self.assertEqual(1, report["source_execution"]["enabled_sources"])
        self.assertEqual("NOT_CONFIGURED", report["health_dimensions"]["dimensions"]["freshness"]["status"])

    def test_metric_cards_keep_definition_and_observation_separate(self):
        report = build_observability_report(self.payload())
        metric = next(item for item in report["metrics"] if item["card"]["metric_id"] == "gate_checks_pass_rate")
        self.assertEqual(1.0, metric["value"])
        self.assertEqual("PASS", metric["status"])
        self.assertIn("NULL", metric["card"]["null_semantics"])

    def test_unsafe_privacy_contract_stops_report(self):
        payload = self.payload(secret_values_exposed=True)
        report = build_observability_report(payload)
        self.assertEqual("STOPPED", report["overall_health"])
        self.assertEqual("STOP_UNSAFE_INPUT_CONTRACT", report["privacy"]["status"])

    def test_failed_gate_stops_even_when_privacy_is_safe(self):
        report = build_observability_report(self.payload(status="STOP_GITHUB_LIVE_GATE"))
        self.assertEqual("STOPPED", report["overall_health"])
        self.assertEqual("PASS", report["privacy"]["status"])

    def test_markdown_is_operator_readable(self):
        markdown = render_markdown(build_observability_report(self.payload()))
        self.assertIn("Relatório de observabilidade", markdown)
        self.assertIn("HEALTHY", markdown)
        self.assertIn("Checks", markdown)
        self.assertIn("Privacidade", markdown)

    def test_bundle_contains_only_sanitized_cards_and_reports(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "observability"
            write_report_bundle(
                self.payload(source_collection=self.source_collection()),
                out,
                source_card=self.source_card(),
            )
            expected = {
                out / "report.json",
                out / "report.md",
                out / "cards" / "run.json",
                out / "cards" / "source_execution.json",
                out / "cards" / "source_contract.json",
                out / "cards" / "metrics.json",
                out / "cards" / "health.json",
            }
            self.assertTrue(all(path.is_file() for path in expected))
            serialized = "\n".join(path.read_text(encoding="utf-8") for path in expected)
            self.assertNotIn("remote-must-not-propagate", serialized)
            self.assertNotIn("hash-must-not-propagate", serialized)

    def test_invalid_payload_type_is_rejected(self):
        with self.assertRaises(TypeError):
            build_observability_report([])


if __name__ == "__main__":
    unittest.main()
