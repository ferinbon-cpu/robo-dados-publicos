from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_control_inventory_review import (
    SiopePublicRuntimeControlInventoryReviewError,
    load_json,
    review_public_runtime_control_inventory,
    validate_review_config,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_control_inventory_review.json"


class TestM7SiopePublicRuntimeControlInventoryReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_review_promotes_only_structural_identity_not_values_or_post(self):
        result = review_public_runtime_control_inventory(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_REVIEW")
        self.assertTrue(result["indexed_get_query_key_controls_structurally_covered"])
        self.assertEqual(result["control_identity_status"], "STRUCTURALLY_OBSERVED_NOT_VALUE_PROVEN")
        self.assertEqual(result["control_value_semantics"], "UNPROVEN")
        self.assertEqual(result["option_value_mapping"], "UNPROVEN")
        self.assertEqual(result["form_post_status"], "OBSERVED_STRUCTURAL_ONLY_NOT_AUTHORIZED")
        self.assertFalse(result["post_authorized"])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["dom_interaction_authorized"])
        self.assertEqual(
            result["next_gate"],
            "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_DESIGN_0_8_0",
        )

    def test_exact_stable_label_bindings_are_reviewed(self):
        result = review_public_runtime_control_inventory(self.config, self.evidence)
        self.assertEqual(
            result["stable_label_bindings"],
            {"Exibir:": "tp_relatorio", "Ano:": "num_ano", "UF:": "cod_uf", "Planilha:": "planilhas"},
        )

    def test_all_public_indexed_get_query_keys_have_structural_controls(self):
        result = review_public_runtime_control_inventory(self.config, self.evidence)
        self.assertEqual(
            result["indexed_get_query_key_control_names"],
            ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        )

    def test_tampered_control_shape_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["controls_structural_summary"][7]["option_count"] = 419
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryReviewError, "CONTROL_STRUCTURAL_SUMMARY"):
            review_public_runtime_control_inventory(self.config, evidence)

    def test_post_observation_cannot_become_authorization(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["form_submission"] = True
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryReviewError, "FORM_SUBMISSION"):
            review_public_runtime_control_inventory(self.config, evidence)

        config = copy.deepcopy(self.config)
        config["post_request"] = "ALLOWED"
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryReviewError, "CONFIG_POST_REQUEST"):
            validate_review_config(config)

    def test_values_interaction_or_limeira_fail_closed(self):
        for key in ("control_values_captured", "option_values_captured", "dom_interaction_performed", "pilot_limeira_values_sent"):
            evidence = copy.deepcopy(self.evidence)
            evidence["result"][key] = True
            with self.assertRaises(SiopePublicRuntimeControlInventoryReviewError, msg=key):
                review_public_runtime_control_inventory(self.config, evidence)

    def test_evidence_identity_artifact_and_form_are_pinned(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["artifact"]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryReviewError, "ARTIFACT_DIGEST"):
            review_public_runtime_control_inventory(self.config, evidence)

        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["form_contract"]["method"] = "GET"
        with self.assertRaisesRegex(SiopePublicRuntimeControlInventoryReviewError, "FORM_CONTRACT"):
            review_public_runtime_control_inventory(self.config, evidence)

    def test_config_keeps_all_operational_authorizations_closed(self):
        validate_review_config(self.config)
        for key in (
            "network_access", "dom_interaction", "form_submission", "post_request", "captcha_bypass",
            "authentication", "control_value_capture", "option_text_capture", "option_value_capture",
            "html_capture", "free_text_capture", "request_body_capture", "response_body_capture",
            "query_value_persistence", "head_request", "artifact_download", "remote_writes",
        ):
            self.assertEqual(self.config[key], "PROHIBITED")
        self.assertFalse(self.config["collection_authorized"])
        self.assertFalse(self.config["processing_authorized"])
        self.assertFalse(self.config["recurrence_authorized"])
        self.assertFalse(self.config["schedule_enabled"])

    def test_module_and_script_are_offline_and_do_not_embed_limeira_code(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_control_inventory_review.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_runtime_control_inventory_review_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        for forbidden in ("urllib", "requests", "http.client", "websocket", "subprocess", "Page.navigate", "Fetch.enable"):
            self.assertNotIn(forbidden, combined)
        self.assertNotIn("352690", combined)


if __name__ == "__main__":
    unittest.main()
