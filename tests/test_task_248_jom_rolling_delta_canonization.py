from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task248_jom_rolling_delta_canonization.v1.json"
SANITIZED = ROOT / "docs/evidence/TASK_248_JOM_ROLLING_DELTA_SANITIZED_RESULT_0.8.0.json"
CANONICAL = ROOT / "docs/evidence/TASK_248_JOM_ROLLING_DELTA_CANONICAL_RESULT_0.8.0.json"
PRIOR = ROOT / "docs/evidence/TASK_217C_JOM_2026_DISCOVERY_CANONICAL_RESULT_0.8.0.json"


class TestTask248JomRollingDeltaCanonization(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.result = json.loads(SANITIZED.read_text(encoding="utf-8"))
        self.canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
        self.prior = json.loads(PRIOR.read_text(encoding="utf-8"))

    def test_prior_snapshot_is_preserved_as_99_through_sep08(self):
        self.assertEqual(self.prior["status"], "PASS_COMPLETE_DISCOVERY_CANONIZED")
        self.assertEqual(self.prior["scope"]["total_documents"], 99)
        self.assertEqual(self.cfg["prior_baseline"]["document_count"], 99)
        self.assertEqual(self.cfg["prior_baseline"]["through_date"], "2026-09-08")
        self.assertEqual(self.cfg["prior_baseline"]["september_editions"], [7316, 7317, 7318, 7319, 7320])

    def test_live_result_hash_matches_pinned_runtime_hash(self):
        payload = dict(self.result)
        stored = payload.pop("result_sha256")
        canonical_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        calculated = hashlib.sha256(canonical_bytes).hexdigest()
        self.assertEqual(stored, calculated)
        self.assertEqual(calculated, self.cfg["runtime"]["result_sha256"])
        self.assertEqual(calculated, "28701eb442dee5bc74e34fe9c7c5a21cec27ffcbae680fe0988ef4a64c978b6d")

    def test_exact_four_identity_delta_is_canonized(self):
        self.assertEqual(self.result["status"], "PASS_JOM_ROLLING_DELTA_DISCOVERY")
        self.assertEqual(self.result["delta_count"], 4)
        self.assertEqual([r["edition"] for r in self.result["delta_editions"]], [7321, 7322, 7323, 7324])
        self.assertEqual(
            [r["publication_date"] for r in self.result["delta_editions"]],
            ["2026-09-09", "2026-09-10", "2026-09-11", "2026-09-12"],
        )
        self.assertEqual(self.cfg["canonized_state"]["known_identity_count"], 103)
        self.assertEqual(self.canonical["canonized_identity_state"]["known_identity_count"], 103)
        self.assertEqual(self.canonical["status"], "PASS_JOM_ROLLING_DELTA_CANONIZED")

    def test_metadata_discovery_does_not_promote_document_content(self):
        self.assertEqual(self.result["document_download_count"], 0)
        self.assertFalse(self.cfg["canonized_state"]["document_content_proven"])
        self.assertFalse(self.canonical["canonized_identity_state"]["pdf_content_materialized"])
        self.assertFalse(self.cfg["canonized_state"]["absence_inference_allowed"])
        self.assertFalse(self.cfg["canonized_state"]["future_editions_inference_allowed"])

    def test_canonization_has_no_remote_or_operational_side_effects(self):
        self.assertFalse(any(self.cfg["remote_effects_of_canonization"].values()))
        self.assertFalse(self.canonical["next_scope"]["document_downloads_authorized"])
        self.assertFalse(self.canonical["next_scope"]["drive_persistence_authorized"])
        self.assertFalse(self.canonical["next_scope"]["serving_update_authorized"])
        self.assertFalse(self.canonical["next_scope"]["recurrence_authorized"])
        self.assertFalse(self.canonical["next_scope"]["schedule_authorized"])

    def test_window_end_is_not_final_absence_claim(self):
        self.assertEqual(self.cfg["canonized_state"]["latest_observed_publication_date"], "2026-09-12")
        self.assertEqual(self.cfg["canonized_state"]["observed_window_end"], "2026-09-16")
        self.assertFalse(self.canonical["canonized_identity_state"]["absence_inference_allowed"])
        self.assertFalse(self.canonical["canonized_identity_state"]["future_editions_inference_allowed"])


if __name__ == "__main__":
    unittest.main()
