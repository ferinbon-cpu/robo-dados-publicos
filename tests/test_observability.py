import unittest
from datetime import datetime, timezone

from robo_dados_publicos.observability import MetricCard, RunCard, SourceCard, evaluate_source_health


class TestObservabilityCards(unittest.TestCase):
    def source(self, **overrides):
        data = {
            "source_id": "SOURCE_A",
            "institution": "Institution",
            "source_url": "https://example.test/data",
            "formats": ("application/json",),
            "periodicity": "daily",
            "scope": "test source",
            "expected_update_interval_hours": 24,
        }
        data.update(overrides)
        return SourceCard(**data)

    def make_run(self, **overrides):
        data = {
            "run_id": "run-1",
            "source_id": "SOURCE_A",
            "software_version": "0.6.3",
            "started_at": "2026-08-24T12:00:00+00:00",
            "finished_at": "2026-08-24T12:00:10+00:00",
            "status": "PASS",
            "records_in": 10,
            "records_out": 10,
        }
        data.update(overrides)
        return RunCard(**data)

    def test_source_card_rejects_non_positive_freshness_threshold(self):
        with self.assertRaises(ValueError):
            self.source(expected_update_interval_hours=0)

    def test_run_card_exposes_latency_without_remote_identifiers(self):
        payload = self.make_run().to_dict()
        self.assertEqual(10.0, payload["latency_seconds"])
        self.assertNotIn("remote_id", payload)

    def test_metric_card_requires_explicit_null_semantics(self):
        with self.assertRaises(ValueError):
            MetricCard(
                metric_id="m1",
                name="Completeness",
                definition="ratio",
                formula="out/in",
                unit="ratio",
                source_fields=("in", "out"),
                null_semantics="",
            )

    def test_stale_source_is_not_hidden_by_success(self):
        health = evaluate_source_health(
            self.source(expected_update_interval_hours=24),
            self.make_run(
                started_at="2026-08-22T11:59:50+00:00",
                finished_at="2026-08-22T12:00:00+00:00",
            ),
            now=datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual("STALE", health["dimensions"]["freshness"]["status"])
        self.assertEqual("FAIL", health["overall_status"])

    def test_missing_records_fail_even_if_other_dimensions_pass(self):
        health = evaluate_source_health(
            self.source(),
            self.make_run(records_in=10, records_out=9),
            now=datetime(2026, 8, 24, 12, 1, tzinfo=timezone.utc),
        )
        self.assertEqual("INCOMPLETE", health["dimensions"]["completeness"]["status"])
        self.assertEqual("FAIL", health["overall_status"])

    def test_expected_absence_is_distinct_from_failure_and_zero(self):
        health = evaluate_source_health(
            self.source(expected_update_interval_hours=None),
            self.make_run(
                status="EXPECTED_ABSENCE",
                expected_absence=True,
                records_in=0,
                records_out=0,
            ),
            now=datetime(2026, 8, 24, 12, 1, tzinfo=timezone.utc),
        )
        self.assertEqual("NOT_APPLICABLE", health["dimensions"]["completeness"]["status"])
        self.assertEqual("PASS", health["dimensions"]["collection"]["status"])
        self.assertEqual("PASS", health["overall_status"])

    def test_validation_error_forces_fail(self):
        health = evaluate_source_health(
            self.source(),
            self.make_run(warnings=("VALIDATION_ERROR",)),
            now=datetime(2026, 8, 24, 12, 1, tzinfo=timezone.utc),
        )
        self.assertEqual("FAIL", health["dimensions"]["consistency"]["status"])
        self.assertEqual("FAIL", health["overall_status"])

    def test_health_pass_keeps_dimensions_separate(self):
        health = evaluate_source_health(
            self.source(),
            self.make_run(),
            now=datetime(2026, 8, 24, 12, 1, tzinfo=timezone.utc),
        )
        self.assertEqual("PASS", health["overall_status"])
        self.assertEqual(1.0, health["dimensions"]["completeness"]["ratio"])
        self.assertEqual(
            {"freshness", "completeness", "consistency", "collection", "latency"},
            set(health["dimensions"]),
        )

    def test_metric_card_from_mapping_normalizes_sequences(self):
        card = MetricCard.from_mapping(
            {
                "metric_id": "m1",
                "name": "Coverage",
                "definition": "Coverage of records",
                "formula": "out/in",
                "unit": "ratio",
                "source_fields": ["in", "out"],
                "null_semantics": "NULL means unavailable, not zero",
                "limitations": ["Requires a known denominator"],
            }
        )
        self.assertEqual(("in", "out"), card.source_fields)
        self.assertEqual(("Requires a known denominator",), card.limitations)


if __name__ == "__main__":
    unittest.main()
