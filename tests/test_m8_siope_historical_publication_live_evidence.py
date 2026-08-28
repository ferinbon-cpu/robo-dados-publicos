import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_RUN_1_0.8.0.json"


class TestM8SiopeHistoricalPublicationLiveEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_live_run_and_artifact_are_pinned(self):
        run = self.data["run"]
        artifact = self.data["evidence_artifact"]
        self.assertEqual(33171163738, run["id"])
        self.assertEqual(98848411366, run["job_id"])
        self.assertEqual("ac80cff2672b91ded2838d18ddd4d4fdcf15b075", run["head_sha"])
        self.assertEqual("success", run["conclusion"])
        self.assertEqual(9685670191, artifact["id"])
        self.assertEqual(625, artifact["zip_size_bytes"])
        self.assertEqual(
            "sha256:7876f9606acfaa357e006c6983dc99172d730206dc40aceffb455d0d389e1c95",
            artifact["digest"],
        )

    def test_gate_created_exactly_three_objects_without_overwrite(self):
        result = self.data["publication_result"]
        self.assertEqual("08_OUTPUTS", result["drive_target"])
        self.assertEqual(3, result["created_count"])
        self.assertEqual(3, len(result["remote_names"]))
        self.assertTrue(result["completion_manifest_written_last"])
        self.assertFalse(result["overwrite_performed"])
        self.assertFalse(result["source_collection_performed"])
        self.assertFalse(result["future_batch_execution_authorized"])
        self.assertEqual("READY_WITH_CAUTION", result["report_status"])

    def test_pdf_and_completion_manifest_readback_are_exact(self):
        readback = self.data["independent_drive_readback"]
        self.assertEqual(3, readback["exact_remote_name_count"])
        self.assertTrue(readback["pdf"]["matches_pinned_source"])
        self.assertEqual(21854, readback["pdf"]["bytes"])
        self.assertEqual(
            "f0e75f41bf1fef333e929b698a2e1e6b404b10f8d0ea2d4916c29063ede3a87b",
            readback["pdf"]["sha256"],
        )
        manifest = readback["completion_manifest"]
        self.assertEqual(1036, manifest["bytes"])
        self.assertEqual(
            "2245a441d2f28a79d662d967ee8e01e58b8129a781c98276c45e00ec90bde50a",
            manifest["sha256"],
        )
        self.assertTrue(manifest["completion_marker_written_last"])
        self.assertFalse(manifest["remote_identifiers_recorded"])
        self.assertFalse(manifest["overwrite_allowed"])

    def test_sheet_structure_defect_is_fail_closed(self):
        sheet = self.data["independent_drive_readback"]["google_sheet"]
        self.assertEqual(9, sheet["expected_logical_rows"])
        self.assertEqual(7, sheet["expected_logical_columns"])
        self.assertEqual(1, sheet["observed_header_cell_count"])
        self.assertFalse(sheet["content_structure_match"])
        self.assertEqual(
            "CSV_DELIMITER_LOCALE_MISMATCH_ON_GOOGLE_SHEETS_IMPORT",
            sheet["diagnosis"],
        )
        self.assertEqual(
            "PUBLICATION_EXECUTED_WITH_SHEET_STRUCTURE_DEFECT",
            self.data["status"],
        )
        self.assertEqual(
            "STOP_CORRECTIVE_REPUBLICATION_REQUIRED",
            self.data["post_publication_audit_status"],
        )

    def test_corrective_republication_needs_new_authorization(self):
        governance = self.data["governance"]
        self.assertTrue(governance["existing_v0_8_0_objects_are_immutable"])
        self.assertFalse(governance["rerun_v0_8_0_authorized"])
        self.assertFalse(governance["overwrite_allowed"])
        self.assertFalse(governance["delete_allowed"])
        self.assertFalse(governance["replace_allowed"])
        self.assertTrue(governance["corrective_publication_requires_new_remote_names"])
        self.assertTrue(governance["corrective_publication_requires_new_explicit_owner_authorization"])
        self.assertFalse(governance["t3_automation_authorized"])
        self.assertFalse(governance["future_batch_execution_authorized"])

    def test_live_qa_counts_are_pinned(self):
        qa = self.data["qa"]
        self.assertEqual({"passed": 1278, "total": 1278}, qa["unit_tests"])
        self.assertEqual({"passed": 109, "total": 109}, qa["historical_regression"])
        self.assertEqual("PASS", qa["compileall"])


if __name__ == "__main__":
    unittest.main()
