from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_signature_diagnostics_design import (
    SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesignError,
    load_json,
    run_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_signature_diagnostics_design.json"


class TestM7SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.fragment_review = {
            "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_REVIEW",
            "application_surface_status": "PROVEN_FRAGMENT_TOLERANT_ON_PINNED_RUN",
            "passive_network_route_status": "EXHAUSTED_ZERO_DYNAMIC_CANDIDATES_ON_PINNED_RUN",
            "resource_get_authorized": False,
        }
        cls.resource_design = {
            "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN",
            "service_document_declared_name": "_Dados_Gerais_Siope",
            "technical_callable_pattern_name": "Dados_Gerais_Siope",
            "technical_callable_parameter_names": ["Ano_Consulta", "Num_Peri", "Sig_UF"],
            "resource_get_authorized": False,
        }

    def test_design_targets_exactly_five_public_identifiers_and_returns_booleans_only(self):
        result = run_design(self.config, self.fragment_review, self.resource_design)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_DESIGN")
        self.assertEqual(result["target_public_identifier_count"], 5)
        self.assertEqual(result["returned_observations"], self.config["allowed_return_fields"])
        self.assertFalse(result["body_or_dom_text_return_authorized"])
        self.assertFalse(result["attribute_value_return_authorized"])
        self.assertFalse(result["resource_get_authorized"])

    def test_design_requires_passive_network_exhaustion_prerequisite(self):
        review = copy.deepcopy(self.fragment_review)
        review["passive_network_route_status"] = "UNPROVEN"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesignError):
            run_design(self.config, review, self.resource_design)

    def test_resource_identity_remains_ambiguous_and_cannot_be_promoted(self):
        design = copy.deepcopy(self.resource_design)
        design["resource_get_authorized"] = True
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesignError):
            run_design(self.config, self.fragment_review, design)

    def test_operational_switches_remain_closed(self):
        for key, value in {
            "dom_interaction": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "post_request_send": "ALLOWED",
            "head_request": "ALLOWED",
            "collection_authorized": True,
            "schedule_enabled": True,
        }.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesignError, msg=key):
                run_design(config, self.fragment_review, self.resource_design)


if __name__ == "__main__":
    unittest.main()
