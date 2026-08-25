from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_signature_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReviewError,
    load_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_signature_diagnostics_review.json"


class TestM7SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_exact_pinned_evidence_passes_with_four_of_five_signature(self):
        result = run_review(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["technical_callable_pattern_status"], "PROVEN_PRESENT_ON_OFFICIAL_APPLICATION_PINNED_RUN")
        self.assertEqual(result["technical_parameter_presence_status"], "PROVEN_ALL_THREE_PRESENT_ON_OFFICIAL_APPLICATION_PINNED_RUN")
        self.assertEqual(result["service_document_name_application_status"], "NOT_OBSERVED_ON_PINNED_APPLICATION_RUN")
        self.assertEqual(result["cross_surface_name_relation_status"], "UNPROVEN_DIFFERENT_OFFICIAL_SURFACES")
        self.assertEqual(result["structural_binding_status"], "UNPROVEN")
        self.assertFalse(result["resource_get_authorized"])

    def test_evidence_identity_artifact_and_blob_are_pinned(self):
        self.assertEqual(self.config["pinned_evidence_blob_sha"], "918eeae965ccc1d5039703a36446fa03adb09462")
        self.assertEqual(self.config["pinned_run_id"], 32906968072)
        self.assertEqual(self.config["pinned_job_id"], 97993079105)
        self.assertEqual(self.config["pinned_artifact_id"], 9585158177)
        self.assertEqual(self.config["expected_matched_signature_count"], 4)

    def test_tampered_signature_or_digest_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["boolean_signature"]["technical_callable_pattern_name_present"] = False
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReviewError):
            run_review(self.config, evidence)
        evidence = copy.deepcopy(self.evidence)
        evidence["artifact"]["digest"] = "sha256:bad"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReviewError):
            run_review(self.config, evidence)

    def test_operational_authorizations_cannot_be_opened(self):
        for key, value in {
            "resource_get_authorized": True,
            "collection_authorized": True,
            "processing_authorized": True,
            "recurrence_authorized": True,
            "schedule_enabled": True,
            "dom_interaction_authorized": True,
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
        }.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReviewError, msg=key):
                run_review(config, self.evidence)


if __name__ == "__main__":
    unittest.main()
