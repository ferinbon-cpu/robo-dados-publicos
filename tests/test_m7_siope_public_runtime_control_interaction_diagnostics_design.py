from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_control_interaction_diagnostics_design import (
    SiopePublicRuntimeControlInteractionDesignError,
    load_json,
    validate_design,
)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config" / "source_expansion.siope_public_runtime_control_interaction_diagnostics_design.json"
REVIEW = ROOT / "config" / "source_expansion.siope_public_runtime_route_contract_review.json"


class TestM7SiopePublicRuntimeControlInteractionDiagnosticsDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = load_json(DESIGN)
        cls.review = load_json(REVIEW)

    def test_design_routes_to_inventory_without_authorizing_interaction(self):
        result = validate_design(self.design, self.review)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN")
        self.assertEqual(result["control_identity_status"], "UNPROVEN")
        self.assertFalse(result["control_interaction_authorized"])
        self.assertTrue(result["control_inventory_required"])
        self.assertFalse(result["network_called"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_0_8_0")

    def test_label_only_control_selection_is_prohibited(self):
        tampered = copy.deepcopy(self.design)
        tampered["label_only_control_selection"] = "ALLOWED"
        with self.assertRaisesRegex(SiopePublicRuntimeControlInteractionDesignError, "LABEL_ONLY_CONTROL_SELECTION"):
            validate_design(tampered, self.review)

    def test_inventory_cannot_capture_values_text_or_html(self):
        inventory = self.design["inventory_observation_scope"]
        for key in ("control_value_capture", "option_text_capture", "option_value_capture", "html_capture", "free_text_capture"):
            self.assertEqual(inventory[key], "PROHIBITED")
        tampered = copy.deepcopy(self.design)
        tampered["inventory_observation_scope"]["option_value_capture"] = "ALLOWED"
        with self.assertRaisesRegex(SiopePublicRuntimeControlInteractionDesignError, "OPTION_VALUE_CAPTURE"):
            validate_design(tampered, self.review)

    def test_future_inventory_aborts_every_nonstatic_request_and_performs_no_interaction(self):
        runtime = self.design["future_inventory_runtime"]
        self.assertEqual(runtime["initial_document_send"], "EXACT_PINNED_PUBLIC_INDEXED_EXAMPLE_ONCE_ONLY")
        self.assertEqual(runtime["all_other_requests"], "ABORT_BEFORE_NETWORK")
        self.assertEqual(runtime["dom_interaction"], "PROHIBITED")
        self.assertEqual(runtime["form_submission"], "PROHIBITED")
        self.assertEqual(runtime["navigation_after_initial_document"], "PROHIBITED")

    def test_review_prerequisite_must_still_be_zero_candidate_unproven(self):
        review = copy.deepcopy(self.review)
        review["dynamic_route_contract_disposition"] = "PROVEN"
        with self.assertRaisesRegex(SiopePublicRuntimeControlInteractionDesignError, "PREREQUISITE_DYNAMIC_ROUTE"):
            validate_design(self.design, review)

    def test_design_gate_has_no_network_or_browser_execution(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_control_interaction_diagnostics_design.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_runtime_control_interaction_diagnostics_design_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        for forbidden in ("urllib", "requests", "http.client", "websocket", "subprocess", "Page.navigate", "Fetch.enable", "Runtime.evaluate"):
            self.assertNotIn(forbidden, combined)
        self.assertNotIn("352690", combined)

    def test_all_operational_authorizations_remain_closed(self):
        self.assertFalse(self.design["collection_authorized"])
        self.assertFalse(self.design["processing_authorized"])
        self.assertFalse(self.design["recurrence_authorized"])
        self.assertFalse(self.design["schedule_enabled"])
        for key in (
            "pilot_limeira_values_send", "dynamic_candidate_network_send", "form_submission", "captcha_bypass",
            "authentication", "credential_capture", "cookie_capture", "request_body_capture", "response_body_capture",
            "query_value_persistence", "head_request", "artifact_download", "remote_writes", "route_synthesis_or_guessing",
            "network_access_for_design_gate",
        ):
            self.assertEqual(self.design[key], "PROHIBITED")


if __name__ == "__main__":
    unittest.main()
