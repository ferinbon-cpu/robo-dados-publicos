from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_service_discovery_review import (
    SiopeOfficialOlindaApiServiceDiscoveryReviewError,
    load_json,
    review_service_discovery,
    validate_review_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_service_discovery_review.json"


class TestM7SiopeOfficialOlindaApiServiceDiscoveryReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_exact_pinned_stop_evidence_passes_as_offline_review(self):
        result = review_service_discovery(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_REVIEW")
        self.assertEqual(result["service_root_status"], "PROVEN_PUBLIC_OFFICIAL_SERVICE_ROOT_ON_PINNED_RUN")
        self.assertEqual(result["service_document_status"], "PARSEABLE_XML_EIGHT_COLLECTIONS_OBSERVED")
        self.assertEqual(result["reference_candidate_status"], "REJECTED_NAME_MISMATCH")
        self.assertEqual(result["observed_target_collection"], "_Dados_Gerais_Siope")
        self.assertEqual(result["resource_call_status"], "NOT_CALLED")
        self.assertEqual(result["resource_schema_status"], "UNPROVEN")
        self.assertEqual(result["parameter_semantics_status"], "UNPROVEN")

    def test_observed_target_is_exact_service_document_name_not_reference_guess(self):
        names = self.evidence["result"]["collection_names"]
        self.assertIn("_Dados_Gerais_Siope", names)
        self.assertNotIn("Dados_Gerais_Siope", names)
        self.assertFalse(self.evidence["result"]["original_reference_candidate_present"])

    def test_review_keeps_every_operational_authorization_closed(self):
        result = review_service_discovery(self.config, self.evidence)
        for key in (
            "network_called",
            "route_synthesized_or_guessed",
            "automatic_value_promotion",
            "resource_get_authorized",
            "pilot_limeira_values_sent",
            "collection_authorized",
            "processing_authorized",
            "recurrence_authorized",
            "schedule_enabled",
        ):
            self.assertFalse(result[key], key)

    def test_tampered_collection_inventory_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["collection_names"][6] = "Dados_Gerais_Siope"
        with self.assertRaises(SiopeOfficialOlindaApiServiceDiscoveryReviewError):
            review_service_discovery(self.config, evidence)

    def test_tampered_run_or_artifact_identity_fails_closed(self):
        for path, value in (
            (("workflow_run_id",), 1),
            (("head_sha",), "deadbeef"),
            (("artifact", "id"), 1),
            (("artifact", "digest"), "sha256:deadbeef"),
        ):
            evidence = copy.deepcopy(self.evidence)
            target = evidence
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(SiopeOfficialOlindaApiServiceDiscoveryReviewError, msg=path):
                review_service_discovery(self.config, evidence)

    def test_config_cannot_authorize_resource_query_post_or_pilot(self):
        mutations = {
            "resource_get": "ALLOWED",
            "query_parameters": "ALLOWED",
            "post_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "route_synthesis_or_guessing": "ALLOWED",
            "automatic_value_promotion": "ALLOWED",
            "collection_authorized": True,
            "processing_authorized": True,
            "recurrence_authorized": True,
            "schedule_enabled": True,
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiServiceDiscoveryReviewError, msg=key):
                validate_review_config(config)

    def test_review_code_is_offline_and_does_not_embed_pilot_request(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_service_discovery_review.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_official_olinda_api_service_discovery_review_gate.py").read_text(encoding="utf-8")
        combined = source + script
        self.assertNotIn("https://", combined)
        self.assertNotIn("urllib", combined)
        self.assertNotIn("http.client", combined)
        self.assertNotIn("requests.", combined)
        self.assertNotIn("352690", combined)

    def test_next_gate_is_resource_contract_design_only(self):
        result = review_service_discovery(self.config, self.evidence)
        self.assertEqual(result["next_gate"], "M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN_0_8_0")
        self.assertFalse(result["resource_get_authorized"])


if __name__ == "__main__":
    unittest.main()
