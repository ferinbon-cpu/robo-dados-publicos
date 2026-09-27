from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_structural_binding_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsReviewError,
    load_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_structural_binding_diagnostics_review.json"


class TestM7SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_exact_pinned_evidence_passes_with_six_of_nine_relations(self):
        result = run_review(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["structural_binding_status"], "PROVEN_CALLABLE_AND_PARAMETERS_COLOCATED_ORDERED_ON_PINNED_RUN")
        self.assertEqual(result["navigation_attribute_presence_status"], "PROVEN_CALLABLE_NAME_IN_NAVIGATION_ATTRIBUTE_ON_PINNED_RUN")
        self.assertEqual(result["navigation_target_semantics_status"], "UNPROVEN_VALUE_NOT_RETURNED")
        self.assertFalse(result["resource_get_authorized"])

    def test_identity_artifact_digest_and_qa_are_pinned(self):
        self.assertEqual(self.config["pinned_run_id"], 32909096430)
        self.assertEqual(self.config["pinned_job_id"], 97999407379)
        self.assertEqual(self.config["pinned_artifact_id"], 9585882913)
        self.assertEqual(self.config["pinned_artifact_digest"], "sha256:641408effd4aa6728cb737ba7cf5ac8c17a4bab7bb51b3af4a5b5b74a7210e74")
        self.assertEqual(self.evidence["qa"]["unit_tests"], 664)
        self.assertEqual(self.evidence["qa"]["historical_regressions"], 109)

    def test_tampered_signature_or_digest_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["structural_boolean_signature"]["navigation_attribute_contains_callable_name"] = False
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsReviewError):
            run_review(self.config, evidence)
        config = copy.deepcopy(self.config)
        config["pinned_artifact_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsReviewError):
            run_review(config, self.evidence)

    def test_operational_authorizations_cannot_be_opened(self):
        for key, value in {
            "dom_interaction_authorized": True,
            "resource_get_authorized": True,
            "collection_authorized": True,
            "processing_authorized": True,
            "recurrence_authorized": True,
            "schedule_enabled": True,
            "automatic_route_promotion": "ALLOWED",
        }.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsReviewError, msg=key):
                run_review(config, self.evidence)


if __name__ == "__main__":
    unittest.main()
