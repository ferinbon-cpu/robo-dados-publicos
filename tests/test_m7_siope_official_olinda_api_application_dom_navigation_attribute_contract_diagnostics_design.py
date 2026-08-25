from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_design import (
    SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsDesignError,
    load_json,
    run_design,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_structural_binding_diagnostics_review import run_review

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_design.json"
REVIEW_CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_structural_binding_diagnostics_review.json"


class TestM7SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        review_config = load_json(REVIEW_CONFIG)
        cls.review = run_review(review_config, load_json(ROOT / review_config["evidence_path"]))

    def test_design_passes_and_returns_exact_boolean_classification(self):
        result = run_design(self.config, self.review)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DESIGN")
        self.assertEqual(len(result["returned_observations"]), 13)
        self.assertEqual(result["matching_attribute_names"], ["href", "action"])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["navigation_execution_authorized"])
        self.assertFalse(result["raw_navigation_value_return_authorized"])
        self.assertFalse(result["resource_get_authorized"])

    def test_review_must_keep_target_and_resource_route_unproven(self):
        for key, value in {
            "navigation_target_semantics_status": "PROVEN",
            "resource_route_contract_status": "PROVEN",
            "resource_get_authorized": True,
        }.items():
            review = copy.deepcopy(self.review)
            review[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsDesignError, msg=key):
                run_design(self.config, review)

    def test_raw_navigation_material_and_execution_cannot_be_enabled(self):
        mutations = {
            "navigation_attribute_value_return": "ALLOWED",
            "navigation_path_return": "ALLOWED",
            "navigation_query_return": "ALLOWED",
            "navigation_fragment_return": "ALLOWED",
            "element_material_return": "ALLOWED",
            "dom_interaction": "ALLOWED",
            "navigation_execution": "ALLOWED",
            "resource_get_authorized": True,
            "collection_authorized": True,
            "schedule_enabled": True,
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsDesignError, msg=key):
                run_design(config, self.review)

    def test_callable_and_parameters_are_exact_prior_public_identifiers(self):
        self.assertEqual(self.config["technical_callable_pattern_name"], "Dados_Gerais_Siope")
        self.assertEqual(self.config["technical_parameter_names"], ["Ano_Consulta", "Num_Peri", "Sig_UF"])
        self.assertNotIn("352690", str(self.config))


if __name__ == "__main__":
    unittest.main()
