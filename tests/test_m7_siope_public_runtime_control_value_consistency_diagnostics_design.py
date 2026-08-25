from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_control_value_consistency_diagnostics_design import (
    SiopePublicRuntimeControlValueConsistencyDesignError,
    load_json,
    validate_design,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_control_value_consistency_diagnostics_design.json"


class TestM7SiopePublicRuntimeControlValueConsistencyDiagnosticsDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.review = load_json(ROOT / cls.config["prerequisite_review_config_path"])
        cls.public = load_json(ROOT / cls.config["public_runtime_config_path"])

    def test_design_is_boolean_only_and_offline(self):
        result = validate_design(self.config, self.review, self.public)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertTrue(result["comparison_result_boolean_only"])
        self.assertFalse(result["browser_may_return_actual_control_values"])
        self.assertFalse(result["browser_may_return_actual_query_values"])
        self.assertFalse(result["dom_interaction_authorized"])
        self.assertFalse(result["form_submission_authorized"])
        self.assertFalse(result["post_authorized"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_0_8_0")

    def test_comparison_scope_is_exactly_the_eight_public_query_keys(self):
        result = validate_design(self.config, self.review, self.public)
        self.assertEqual(
            result["comparison_control_names"],
            ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        )
        self.assertEqual(result["comparison_control_names"], self.public["expected_query_keys"])

    def test_actual_values_and_text_cannot_be_returned(self):
        for key in (
            "actual_control_value_return", "actual_query_value_return", "option_text_return", "option_value_return",
            "html_return", "free_text_return",
        ):
            config = copy.deepcopy(self.config)
            config[key] = "ALLOWED"
            with self.assertRaises(SiopePublicRuntimeControlValueConsistencyDesignError, msg=key):
                validate_design(config, self.review, self.public)

    def test_interaction_submit_post_and_limeira_remain_closed(self):
        for key in ("dom_interaction", "form_submission", "post_request", "pilot_limeira_values_send"):
            config = copy.deepcopy(self.config)
            config[key] = "ALLOWED"
            with self.assertRaises(SiopePublicRuntimeControlValueConsistencyDesignError, msg=key):
                validate_design(config, self.review, self.public)

    def test_prerequisite_review_must_keep_values_unproven(self):
        review = copy.deepcopy(self.review)
        review["control_value_semantics"] = "PROVEN"
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyDesignError, "REVIEW_VALUE_SEMANTICS"):
            validate_design(self.config, review, self.public)

    def test_public_example_must_stay_non_pilot(self):
        public = copy.deepcopy(self.public)
        public["public_indexed_example_url"] += "&sentinel=352690"
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyDesignError, "PUBLIC_CONFIG_PILOT_VALUE"):
            validate_design(self.config, self.review, public)

    def test_module_and_script_are_offline_and_do_not_encode_pilot_request(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_control_value_consistency_diagnostics_design.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_runtime_control_value_consistency_diagnostics_design_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        for forbidden in (
            "import urllib", "from urllib", "import requests", "from requests", "http.client",
            "import websocket", "from websocket", "import subprocess", "from subprocess",
            "Page.navigate", "Fetch.enable",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertNotIn("cod_muni=352690", combined)


if __name__ == "__main__":
    unittest.main()
