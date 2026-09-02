from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.manual_ingest.reconciliation import (
    F01ReconciliationStop,
    load_reconciliation_contract,
    reconcile_f01_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/manual_supervised_ingest_f01_reconciliation.v1.json"
FIXTURE = ROOT / "tests/fixtures/task_026_f01_staging_reconciliation.json"


class TestTask026F01StagingReconciliation(unittest.TestCase):
    def setUp(self):
        self.contract = load_reconciliation_contract(CONTRACT)
        self.bundle = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_valid_bundle_passes_but_remains_not_silver(self):
        result = reconcile_f01_bundle(self.contract, self.bundle)
        self.assertEqual(result["status"], "PASS_F01_STAGING_RECONCILED_OFFLINE")
        self.assertEqual(result["promotion"], "BLOCKED_NOT_SILVER")
        self.assertEqual(result["financial_identity"], "EVIDENCIA_INSUFICIENTE")
        self.assertEqual(result["loa_full_parse"], "BLOCKED")

    def test_silver_promotion_attempt_fails_closed(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["promotion_status"] = "SILVER"
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_UNAUTHORIZED_PROMOTION"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_source_hash_drift_fails_closed(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["sources"]["PPA"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_SOURCE_HASH_DRIFT"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_derived_hash_closure_drift_fails_closed(self):
        bundle = deepcopy(self.bundle)
        bundle["derived_hashes"]["QA_F01_STRUCTURED_PARSE_V01.json"] = "f" * 64
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_DERIVED_HASH_CLOSURE_MISMATCH"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_ppa_target_drift_fails_closed(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["ppa"]["indicator_eiti"]["2029"] = 60
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_PPA_TARGET_DRIFT"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_review_required_row_cannot_be_promoted(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["ppa"]["review_required_rows"][0]["promoted"] = True
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_REVIEW_ROW_PROMOTED"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_ldo_marker_loss_fails_closed(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["ldo"]["structural_markers"][0]["found"] = False
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_LDO_MARKER_DRIFT"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_loa_prior_bridge_cannot_be_promoted_to_eiti(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["loa"]["prior_action_evidence"][0]["eiti_specific"] = True
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_LOA_PRIOR_EVIDENCE_FALSE_EITI_PROMOTION"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_loa_full_parse_must_remain_blocked(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["loa"]["header"]["full_structured_parse_status"] = "PARSED"
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_LOA_FULL_PARSE_NOT_BLOCKED"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_financial_identity_cannot_be_promoted(self):
        bundle = deepcopy(self.bundle)
        bundle["staging"]["financial_identity"]["eiti_specific_status"] = "FINANCIAL_IDENTITY_PROVEN"
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_FINANCIAL_IDENTITY_PROMOTED"):
            reconcile_f01_bundle(self.contract, bundle)

    def test_qa_failure_fails_closed(self):
        bundle = deepcopy(self.bundle)
        bundle["qa"]["checks"][0]["result"] = "FAIL"
        with self.assertRaisesRegex(F01ReconciliationStop, "STOP_F01_QA_CHECK_FAILURE"):
            reconcile_f01_bundle(self.contract, bundle)


if __name__ == "__main__":
    unittest.main()
