from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.manual_ingest.ephemeral_reproducibility import (
    DIGEST_PASS,
    ReproducibilityStop,
    capture_digest_observation,
    compare_historical_observation,
    persist_observation_then_compare,
    runtime_fingerprint,
)


def digest_result(*, silver=79, gold=15, rag=126):
    names = (
        "edition_manifest.json",
        "pages_silver.jsonl",
        "events_gold.jsonl",
        "chunks_rag.jsonl",
    )
    candidates = [
        {"name": name, "bytes": index + 10, "sha256": f"{index + 1:064x}"}
        for index, name in enumerate(names)
    ]
    return {
        "status": DIGEST_PASS,
        "persistence_authorized": False,
        "result_sha256": "a" * 64,
        "processor_git_blob_sha": "b" * 40,
        "candidate_set_sha256": "c" * 64,
        "input_count": 1,
        "candidate_file_count": 4,
        "items": [
            {
                "source_key": "journal-7024",
                "family": "JORNAL_OFICIAL",
                "source_sha256": "d" * 64,
                "source_bytes": 17615179,
                "silver_rows": silver,
                "gold_rows": gold,
                "rag_rows": rag,
                "candidate_files": candidates,
            }
        ],
    }


def expectation(*, silver=79, gold=15, rag=126):
    return {
        "schema": "EPHEMERAL_DIGEST_HISTORICAL_EXPECTATION_V1",
        "items": [
            {
                "source_key": "journal-7024",
                "source_sha256": "d" * 64,
                "counts": {
                    "silver_rows": silver,
                    "gold_rows": gold,
                    "rag_rows": rag,
                },
            }
        ],
    }


FIXED_FP = {
    "python": "3.12.11",
    "python_implementation": "CPython",
    "platform_system": "Linux",
    "platform_release": "fixture",
    "platform_machine": "x86_64",
    "pypdf": "6.10.0",
    "project_version": "0.8.0",
    "runner_os": "Linux",
    "runner_image_os": "ubuntu24",
    "runner_image_version": "fixture",
}


class TestTask092EphemeralReproducibility(unittest.TestCase):
    def test_capture_freezes_counts_hashes_and_runtime_before_comparison(self):
        observation = capture_digest_observation(
            digest_result(),
            fingerprint=FIXED_FP,
        )
        self.assertEqual(DIGEST_PASS, observation["digest_status"])
        self.assertEqual(FIXED_FP, observation["runtime_fingerprint"])
        item = observation["items"][0]
        self.assertEqual(
            {"silver_rows": 79, "gold_rows": 15, "rag_rows": 126},
            item["counts"],
        )
        self.assertEqual(4, len(item["candidate_files"]))
        self.assertEqual("1".zfill(64), item["candidate_files"][0]["sha256"])
        self.assertEqual(64, len(observation["observation_sha256"]))

    def test_matching_history_is_separate_from_digest_pass(self):
        observation = capture_digest_observation(
            digest_result(),
            fingerprint=FIXED_FP,
        )
        report = compare_historical_observation(observation, expectation())
        self.assertEqual(DIGEST_PASS, report["digest_status"])
        self.assertEqual(
            "HISTORICAL_REPRODUCTION_MATCH",
            report["historical_reproduction_status"],
        )
        self.assertEqual(0, report["mismatch_count"])

    def test_historical_drift_does_not_turn_digest_pass_into_stop(self):
        observation = capture_digest_observation(
            digest_result(silver=80, gold=14, rag=130),
            fingerprint=FIXED_FP,
        )
        report = compare_historical_observation(observation, expectation())
        self.assertEqual(DIGEST_PASS, report["digest_status"])
        self.assertEqual(
            "HISTORICAL_REPRODUCTION_DRIFT",
            report["historical_reproduction_status"],
        )
        self.assertEqual(3, report["mismatch_count"])
        fields = {item["field"] for item in report["mismatches"]}
        self.assertEqual({"silver_rows", "gold_rows", "rag_rows"}, fields)
        self.assertTrue(report["digest_pass_preserved_on_historical_drift"])

    def test_observation_is_written_before_malformed_expectation_can_stop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            observation_path = root / "observation.json"
            report_path = root / "report.json"
            malformed = {"schema": "WRONG", "items": []}
            with self.assertRaisesRegex(ReproducibilityStop, "EXPECTATION_SCHEMA"):
                persist_observation_then_compare(
                    digest_result(),
                    malformed,
                    observation_path=observation_path,
                    report_path=report_path,
                    fingerprint=FIXED_FP,
                )
            self.assertTrue(observation_path.exists())
            self.assertFalse(report_path.exists())
            stored = json.loads(observation_path.read_text(encoding="utf-8"))
            self.assertEqual(DIGEST_PASS, stored["digest_status"])
            self.assertEqual(79, stored["items"][0]["counts"]["silver_rows"])

    def test_create_only_semantics_prevent_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            observation_path = root / "observation.json"
            report_path = root / "report.json"
            observation_path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ReproducibilityStop, "CREATE_ONLY_PATH_EXISTS"):
                persist_observation_then_compare(
                    digest_result(),
                    expectation(),
                    observation_path=observation_path,
                    report_path=report_path,
                    fingerprint=FIXED_FP,
                )
            self.assertEqual("{}\n", observation_path.read_text(encoding="utf-8"))
            self.assertFalse(report_path.exists())

    def test_non_pass_digest_cannot_be_promoted_to_observation(self):
        result = digest_result()
        result["status"] = "STOP_EPHEMERAL_RUNTIME_DIGEST"
        with self.assertRaisesRegex(ReproducibilityStop, "DIGEST_NOT_PASS"):
            capture_digest_observation(result, fingerprint=FIXED_FP)

    def test_runtime_fingerprint_contains_required_versions(self):
        fingerprint = runtime_fingerprint()
        for key in (
            "python",
            "python_implementation",
            "platform_system",
            "pypdf",
            "project_version",
        ):
            self.assertIn(key, fingerprint)
            self.assertIsNotNone(fingerprint[key])


if __name__ == "__main__":
    unittest.main()
