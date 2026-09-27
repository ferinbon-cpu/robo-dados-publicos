from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_resource_contract_design import (
    SiopeOfficialOlindaApiResourceContractDesignError,
    design_resource_contract,
    load_json,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_resource_contract_design.json"


class TestM7SiopeOfficialOlindaApiResourceContractDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.review = load_json(ROOT / cls.config["review_config_path"])
        cls.research = load_json(ROOT / cls.config["public_research_evidence_path"])

    def test_design_preserves_two_names_without_equating_them(self):
        result = design_resource_contract(self.config, self.review, self.research)
        self.assertEqual(result["service_document_declared_name"], "_Dados_Gerais_Siope")
        self.assertEqual(result["technical_callable_pattern_name"], "Dados_Gerais_Siope")
        self.assertEqual(result["name_identity_relation_status"], "UNPROVEN")
        self.assertEqual(result["leading_underscore_semantics_status"], "UNPROVEN")
        self.assertEqual(result["callable_operation_kind_status"], "UNPROVEN")

    def test_design_does_not_authorize_direct_resource_or_parameters(self):
        result = design_resource_contract(self.config, self.review, self.research)
        self.assertEqual(result["direct_resource_get_safe_status"], "NOT_PROVEN_SAFE")
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["query_parameters_authorized"])
        self.assertFalse(result["collection_authorized"])
        self.assertFalse(result["pilot_limeira_values_sent"])

    def test_future_runtime_policy_blocks_dynamic_before_network(self):
        policy = self.config["future_runtime_policy"]
        self.assertEqual(policy["xhr_fetch"], "BLOCK_BEFORE_NETWORK_AND_RECORD_SANITIZED_SHAPE_ONLY")
        self.assertEqual(policy["other_dynamic_requests"], "BLOCK_BEFORE_NETWORK")
        self.assertEqual(policy["resource_data_request"], "PROHIBITED")
        self.assertEqual(policy["pilot_values"], "PROHIBITED")

    def test_review_must_keep_resource_uncalled_and_unproven(self):
        for key, value in (
            ("resource_call_disposition", "CALLED"),
            ("resource_schema_disposition", "PROVEN"),
            ("parameter_semantics_disposition", "PROVEN"),
            ("collection_authorized", True),
        ):
            review = copy.deepcopy(self.review)
            review[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiResourceContractDesignError, msg=key):
                validate_config(self.config, review, self.research)

    def test_research_cannot_silently_equate_names_or_enable_safe_get(self):
        for key, value in (("same_contract_identity_proven", True), ("safe_direct_resource_get_available", True)):
            research = copy.deepcopy(self.research)
            research["contract_ambiguity"][key] = value
            with self.assertRaises(SiopeOfficialOlindaApiResourceContractDesignError, msg=key):
                validate_config(self.config, self.review, research)

    def test_operational_switches_cannot_be_opened(self):
        for key, value in {
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
        }.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiResourceContractDesignError, msg=key):
                validate_config(config, self.review, self.research)

    def test_gate_is_offline_and_next_step_is_passive_application_diagnostics_design(self):
        result = design_resource_contract(self.config, self.review, self.research)
        self.assertFalse(result["network_called"])
        self.assertEqual(result["next_diagnostic_surface"], "OFFICIAL_APPLICATION_PAGE_PASSIVE_RUNTIME")
        self.assertEqual(result["next_gate"], "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DESIGN_0_8_0")
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_resource_contract_design.py").read_text(encoding="utf-8")
        self.assertNotIn("urllib", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("352690", source)


if __name__ == "__main__":
    unittest.main()
