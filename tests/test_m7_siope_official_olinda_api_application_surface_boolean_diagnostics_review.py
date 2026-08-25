from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_surface_boolean_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReviewError,
    load_json,
    review_surface_boolean_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_surface_boolean_diagnostics_review.json"


class TestM7SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReview(unittest.TestCase):
    def setUp(self):
        self.config = load_json(CONFIG)
        self.evidence = load_json(ROOT / self.config["evidence_path"])

    def test_exact_pinned_evidence_passes(self):
        result = review_surface_boolean_diagnostics(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["fragment_semantics_status"], "UNPROVEN")
        self.assertFalse(result["fragment_value_captured"])
        self.assertFalse(result["fragment_used_for_route_identity"])
        self.assertFalse(result["resource_get_authorized"])

    def test_tampered_fragment_or_ready_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["final_observation"]["fragment_empty"] = True
        with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReviewError):
            review_surface_boolean_diagnostics(self.config, evidence)
        evidence = copy.deepcopy(self.evidence)
        evidence["final_observation"]["ready_eligible"] = False
        with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReviewError):
            review_surface_boolean_diagnostics(self.config, evidence)

    def test_any_operational_authorization_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["safety"]["resource_get_authorized"] = True
        with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReviewError):
            review_surface_boolean_diagnostics(self.config, evidence)

    def test_next_gate_is_fragment_tolerant_route_diagnostics_only(self):
        result = review_surface_boolean_diagnostics(self.config, self.evidence)
        self.assertEqual(result["next_gate"], "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_0_8_0")
        self.assertFalse(result["surface_authorized"])


if __name__ == "__main__":
    unittest.main()
