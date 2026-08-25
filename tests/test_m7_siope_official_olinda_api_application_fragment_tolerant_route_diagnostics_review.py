from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_tolerant_route_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsReviewError,
    load_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_fragment_tolerant_route_diagnostics_review.json"


class TestM7SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_exact_pinned_run_passes_and_exhausts_passive_route_observation(self):
        result = run_review(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["application_surface_status"], "PROVEN_FRAGMENT_TOLERANT_ON_PINNED_RUN")
        self.assertEqual(result["passive_network_route_status"], "EXHAUSTED_ZERO_DYNAMIC_CANDIDATES_ON_PINNED_RUN")
        self.assertEqual(result["dynamic_route_contract_status"], "UNPROVEN_ZERO_CANDIDATES")
        self.assertFalse(result["resource_get_authorized"])

    def test_run_artifact_digest_and_zero_candidates_are_pinned(self):
        self.assertEqual(self.config["pinned_run_id"], 32904143482)
        self.assertEqual(self.config["pinned_job_id"], 97984314798)
        self.assertEqual(self.config["pinned_artifact_id"], 9584165097)
        self.assertEqual(self.evidence["candidate_shape_count"], 0)
        self.assertEqual(self.evidence["candidate_shapes"], [])
        self.assertEqual(self.evidence["artifact"]["digest"], self.config["pinned_artifact_digest"])

    def test_tampered_candidate_or_digest_fails_closed(self):
        for mutation in ("candidate", "digest"):
            evidence = copy.deepcopy(self.evidence)
            if mutation == "candidate":
                evidence["candidate_shape_count"] = 1
            else:
                evidence["artifact"]["digest"] = "sha256:" + "0" * 64
            with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsReviewError):
                run_review(self.config, evidence)

    def test_operational_authorization_cannot_be_opened(self):
        config = copy.deepcopy(self.config)
        config["resource_get_authorized"] = True
        with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsReviewError):
            run_review(config, self.evidence)


if __name__ == "__main__":
    unittest.main()
