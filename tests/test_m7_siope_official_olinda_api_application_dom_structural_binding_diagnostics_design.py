from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_structural_binding_diagnostics_design import (
    SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsDesignError,
    load_json,
    run_design,
)
from scripts.github_siope_official_olinda_api_application_dom_signature_diagnostics_review_gate import run_gate as run_signature_review
from scripts.github_siope_official_olinda_api_resource_contract_design_gate import run_gate as run_resource_design

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_structural_binding_diagnostics_design.json"


class TestM7SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.signature_review = run_signature_review()
        cls.resource_design = run_resource_design()

    def test_design_passes_and_targets_exact_boolean_relations(self):
        result = run_design(self.config, self.signature_review, self.resource_design)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DESIGN")
        self.assertEqual(result["returned_observations"], self.config["allowed_return_fields"])
        self.assertEqual(len(result["returned_observations"]), 9)
        self.assertEqual(result["structural_binding_status"], "UNPROVEN_PENDING_BOOLEAN_DIAGNOSTICS")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["resource_get_authorized"])

    def test_prerequisite_keeps_cross_surface_identity_and_binding_unproven(self):
        self.assertEqual(self.signature_review["cross_surface_name_relation_status"], "UNPROVEN_DIFFERENT_OFFICIAL_SURFACES")
        self.assertEqual(self.signature_review["structural_binding_status"], "UNPROVEN")
        self.assertEqual(self.resource_design["name_identity_relation_status"], "UNPROVEN")
        self.assertEqual(self.resource_design["direct_resource_get_safe_status"], "NOT_PROVEN_SAFE")

    def test_no_raw_dom_or_element_material_can_be_returned(self):
        for key in (
            "dom_text_return", "dom_attribute_value_return", "element_text_return", "element_attribute_return",
            "tag_name_return", "fragment_value_capture", "html_capture", "script_source_capture",
            "response_body_capture", "request_body_capture", "query_value_persistence",
        ):
            self.assertEqual(self.config[key], "PROHIBITED")

    def test_operational_switches_remain_closed(self):
        mutations = {
            "resource_get_authorized": True,
            "collection_authorized": True,
            "processing_authorized": True,
            "recurrence_authorized": True,
            "schedule_enabled": True,
            "dom_interaction": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsDesignError, msg=key):
                run_design(config, self.signature_review, self.resource_design)


if __name__ == "__main__":
    unittest.main()
