from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy
from robo_dados_publicos.product.publication import PublicationNames
from robo_dados_publicos.product.siope_historical_publication_gate import (
    GATE_ID,
    M8HistoricalPublicationGateError,
    PASS_DRY_RUN,
    REMOTE_BASENAME,
    SOURCE_ARTIFACT_ID,
    SOURCE_ARTIFACT_ZIP_SHA256,
    dry_run_result,
    validate_owner_authorization,
    validate_source_zip,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/m8-siope-historical-product-output-publication-gate.yml"


class M8SiopeHistoricalPublicationGateTests(unittest.TestCase):
    def test_owner_authorization_is_exactly_one_manual_t3_publication(self) -> None:
        evidence = validate_owner_authorization(root=ROOT)
        names = PublicationNames.from_basename(REMOTE_BASENAME)
        self.assertEqual(evidence["gate_id"], GATE_ID)
        self.assertEqual(evidence["remote_names"], list(names.all()))
        self.assertEqual(evidence["required_remote_count"], 3)
        self.assertTrue(evidence["create_only"])
        self.assertTrue(evidence["manual_execution_required"])
        self.assertTrue(evidence["single_execution"])
        self.assertFalse(evidence["overwrite_allowed"])
        self.assertFalse(evidence["replace_allowed"])
        self.assertFalse(evidence["delete_allowed"])
        self.assertFalse(evidence["future_batch_execution_authorized"])
        self.assertFalse(evidence["t3_auto_allowed"])

    def test_policy_still_blocks_automatic_publication(self) -> None:
        policy = load_policy(ROOT)
        publication = evaluate_gate(policy, "PRODUCT_OUTPUT_PUBLICATION")
        self.assertEqual(publication["decision"], "BLOCK")
        self.assertEqual(publication["tier"], "T3_MUTATING_OR_PUBLICATION")
        self.assertIn("PUBLICATION_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION", publication["blockers"])

    def test_remote_names_are_the_reviewed_three_objects(self) -> None:
        names = PublicationNames.from_basename(REMOTE_BASENAME)
        self.assertEqual(
            list(names.all()),
            [
                "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_TABELA",
                "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0.pdf",
                "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_publication_manifest.json",
            ],
        )

    def test_source_artifact_is_hard_pinned_and_drift_fails_closed(self) -> None:
        self.assertEqual(SOURCE_ARTIFACT_ID, 9684264254)
        self.assertEqual(
            SOURCE_ARTIFACT_ZIP_SHA256,
            "213693b37e8a2123d1d4df4b4dec0495a5ca9536cb51b23f0549e94da72d080e",
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "wrong.zip"
            path.write_bytes(b"not-the-pinned-artifact")
            with self.assertRaisesRegex(
                M8HistoricalPublicationGateError,
                "STOP_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_SOURCE_ARTIFACT_ZIP_BYTES",
            ):
                validate_source_zip(path)

    def test_dry_run_contract_has_zero_network_and_zero_writes(self) -> None:
        result = dry_run_result(
            source={
                "source": {
                    "zip_sha256": SOURCE_ARTIFACT_ZIP_SHA256,
                }
            }
        )
        self.assertEqual(result["status"], PASS_DRY_RUN)
        self.assertEqual(result["would_create"], 3)
        self.assertEqual(result["drive_target"], "08_OUTPUTS")
        self.assertFalse(result["network_called"])
        self.assertEqual(result["drive_writes"], 0)
        self.assertTrue(result["preflight_all_names_before_first_write"])
        self.assertTrue(result["completion_manifest_written_last"])
        self.assertFalse(result["future_batch_execution_authorized"])

    def test_workflow_is_manual_only_and_t3_does_not_become_no_click(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("workflow_call:", text)
        self.assertNotIn("\n  push:", text)
        self.assertNotIn("\n  schedule:", text)
        self.assertIn("confirm_m8_siope_historical_product_output_publication", text)
        self.assertIn('test "$GITHUB_REF" = "refs/heads/main"', text)
        self.assertIn("cancel-in-progress: false", text)

    def test_workflow_uses_pinned_artifact_and_write_credentials_only_for_t3(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('SOURCE_ARTIFACT_ID: "9684264254"', text)
        self.assertIn("actions: read", text)
        self.assertIn("contents: read", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_SECRET: ${{ secrets.GOOGLE_DRIVE_CLIENT_SECRET }}", text)
        self.assertIn("GOOGLE_DRIVE_REFRESH_TOKEN: ${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}", text)
        self.assertNotIn("GOOGLE_DRIVE_READONLY_REFRESH_TOKEN", text)
        self.assertIn("--owner-authorized", text)
        self.assertIn("--dry-run", text)
        self.assertNotIn("schedule_authorized: true", text)


if __name__ == "__main__":
    unittest.main()
