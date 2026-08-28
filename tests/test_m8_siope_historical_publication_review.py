from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy
from robo_dados_publicos.product import siope_historical_publication_review as review_module
from robo_dados_publicos.product.siope_historical_publication_review import (
    PASS,
    SiopeHistoricalPublicationReviewError,
    review_publication,
)

ROOT = Path(__file__).resolve().parents[1]


def _blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


class M8SiopeHistoricalPublicationReviewTests(unittest.TestCase):
    def test_offline_review_passes_and_does_not_authorize_publication(self) -> None:
        result = review_publication(root=ROOT)
        self.assertEqual(result["status"], PASS)
        self.assertEqual(result["decision"], "READY_FOR_EXPLICIT_OWNER_PUBLICATION_DECISION")
        self.assertEqual(result["publication_plan"]["required_remote_count"], 3)
        self.assertEqual(
            result["publication_plan"]["publications"],
            [
                "GOOGLE_SHEET_FROM_TABLE_CSV",
                "REPORT_PDF",
                "COMPLETION_MANIFEST_JSON",
            ],
        )
        self.assertTrue(result["publication_plan"]["create_only"])
        self.assertTrue(result["publication_plan"]["preflight_all_names_before_first_write"])
        self.assertTrue(result["publication_plan"]["completion_manifest_written_last"])
        self.assertFalse(result["publication_plan"]["overwrite_allowed"])
        self.assertFalse(result["publication_plan"]["replace_allowed"])
        self.assertFalse(result["publication_plan"]["delete_allowed"])
        self.assertEqual(result["publication_plan"]["remote_writes_performed"], 0)
        self.assertFalse(result["publication_plan"]["publication_performed"])
        self.assertFalse(result["publication_plan"]["publication_authorized"])
        self.assertTrue(result["publication_plan"]["owner_authorization_required"])
        self.assertFalse(result["future_batch_execution_authorized"])
        self.assertFalse(result["years_before_2016_authorized"])

    def test_selected_publication_sources_are_exactly_pinned(self) -> None:
        result = review_publication(root=ROOT)
        selected = result["product"]["selected_publication_sources"]
        self.assertEqual(
            selected["table.csv"],
            {
                "bytes": 23115,
                "sha256": "749b8dd8f56b4ced755f634e08c9b4f8d7cd6f75c448e4c55bbfe77f6d7f8a8e",
            },
        )
        self.assertEqual(
            selected["report.pdf"],
            {
                "bytes": 21854,
                "sha256": "f0e75f41bf1fef333e929b698a2e1e6b404b10f8d0ea2d4916c29063ede3a87b",
            },
        )
        self.assertEqual(result["product"]["report_status"], "READY_WITH_CAUTION")
        self.assertFalse(result["product"]["compliance_claims_authorized"])

    def test_policy_allows_only_the_offline_review_not_publication(self) -> None:
        policy = load_policy(ROOT)
        review = evaluate_gate(policy, "M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW")
        publication = evaluate_gate(policy, "PRODUCT_OUTPUT_PUBLICATION")
        self.assertEqual(review["decision"], "AUTO_ALLOWED")
        self.assertEqual(review["tier"], "T0_OFFLINE")
        self.assertEqual(publication["decision"], "BLOCK")
        self.assertEqual(publication["tier"], "T3_MUTATING_OR_PUBLICATION")
        self.assertIn("PUBLICATION_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION", publication["blockers"])

    def test_semantic_drift_to_publication_authorized_fails_closed(self) -> None:
        evidence = json.loads((ROOT / review_module.EVIDENCE_PATH).read_text(encoding="utf-8"))
        evidence["governance"]["publication_authorized"] = True
        with tempfile.TemporaryDirectory() as raw:
            temp_root = Path(raw)
            evidence_path = temp_root / review_module.EVIDENCE_PATH
            evidence_path.parent.mkdir(parents=True)
            evidence_raw = (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            evidence_path.write_bytes(evidence_raw)
            policy_path = temp_root / review_module.POLICY_PATH
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text((ROOT / review_module.POLICY_PATH).read_text(encoding="utf-8"), encoding="utf-8")
            with patch.object(review_module, "EVIDENCE_BLOB_SHA", _blob_sha(evidence_raw)):
                with self.assertRaisesRegex(
                    SiopeHistoricalPublicationReviewError,
                    "STOP_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW_GOV_PUBLICATION",
                ):
                    review_publication(root=temp_root)

    def test_evidence_blob_drift_fails_before_semantic_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp_root = Path(raw)
            evidence_path = temp_root / review_module.EVIDENCE_PATH
            evidence_path.parent.mkdir(parents=True)
            evidence_path.write_bytes((ROOT / review_module.EVIDENCE_PATH).read_bytes() + b"\n")
            policy_path = temp_root / review_module.POLICY_PATH
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text((ROOT / review_module.POLICY_PATH).read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(
                SiopeHistoricalPublicationReviewError,
                "STOP_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW_EVIDENCE_BLOB_SHA",
            ):
                review_publication(root=temp_root)


if __name__ == "__main__":
    unittest.main()
