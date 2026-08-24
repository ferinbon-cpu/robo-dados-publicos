import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestM6Promotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.active = json.loads((ROOT / "release_manifest_v01_0.7.0_active.json").read_text(encoding="utf-8"))
        cls.candidate = json.loads((ROOT / "release_manifest_v01_0.7.0.json").read_text(encoding="utf-8"))
        cls.current = json.loads((ROOT / "release_manifest_v01.json").read_text(encoding="utf-8"))
        cls.publication_script = (ROOT / "scripts" / "github_product_publication_gate.py").read_text(encoding="utf-8")

    def test_candidate_evidence_is_preserved_after_promotion(self):
        self.assertEqual("CANDIDATE", self.candidate["status"])
        self.assertEqual("0.7.0", self.candidate["version"])
        self.assertEqual("release_manifest_v01_0.7.0.json", self.active["candidate_manifest"])
        self.assertEqual("release_manifest_v01_0.7.0.json", self.current["preserved_candidate_manifest"])

    def test_live_publication_gate_is_pinned(self):
        live = self.active["live_gate"]
        self.assertEqual("PASS_M6_PRODUCT_OUTPUT_PUBLICATION_GATE", live["status"])
        self.assertEqual(32787729769, live["github_run"])
        self.assertEqual(97622956591, live["github_job"])
        self.assertEqual(3, live["created_count"])
        self.assertFalse(live["overwrite_performed"])
        self.assertFalse(live["secret_values_exposed"])
        self.assertFalse(live["remote_identifiers_exposed"])

    def test_drive_outputs_and_completion_marker_are_recorded(self):
        evidence = self.active["drive_evidence"]
        self.assertEqual("08_OUTPUTS", evidence["target"])
        self.assertEqual("application/vnd.google-apps.spreadsheet", evidence["google_sheet"]["mime_type"])
        self.assertEqual("application/pdf", evidence["pdf"]["mime_type"])
        self.assertEqual("application/json", evidence["completion_manifest"]["mime_type"])
        self.assertTrue(evidence["completion_manifest"]["written_last"])
        self.assertFalse(evidence["completion_manifest"]["overwrite_allowed"])

    def test_publication_rerun_is_blocked_and_next_gate_is_design_only(self):
        self.assertIn('RELEASE_STATUS == "CANDIDATE"', self.publication_script)
        self.assertEqual("BLOCKED_BY_ACTIVE_RELEASE_IDENTITY", self.active["safety"]["publication_rerun"])
        self.assertEqual("DESIGN_ONLY_NOT_AUTHORIZED", self.active["open_gates"]["controlled_source_expansion_0_8_0"])
        self.assertEqual("M7_CONTROLLED_SOURCE_EXPANSION_DESIGN_0_8_0", self.current["next_action"])


if __name__ == "__main__":
    unittest.main()
