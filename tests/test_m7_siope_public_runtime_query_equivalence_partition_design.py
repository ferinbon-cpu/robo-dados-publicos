from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_query_equivalence_partition_design import (
    SiopePublicRuntimeQueryEquivalencePartitionDesignError,
    load_json,
    validate_partition_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_query_equivalence_partition_design.json"


class TestM7SiopePublicRuntimeQueryEquivalencePartitionDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.action_review = load_json(ROOT / cls.config["action_semantics_review_config_path"])
        cls.value_review = load_json(ROOT / cls.config["value_consistency_review_config_path"])

    def test_exact_partition_passes_offline(self):
        result = validate_partition_design(self.config, self.action_review, self.value_review)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_QUERY_EQUIVALENCE_PARTITION_DESIGN")
        self.assertEqual(result["query_equivalent_control_names"], ["admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"])
        self.assertEqual(result["non_equivalent_same_name_control_names"], ["acao"])
        self.assertFalse(result["same_name_implies_value_equivalence"])
        self.assertFalse(result["same_name_implies_semantic_role_equivalence"])
        self.assertTrue(result["independent_public_example_required_before_generalization"])
        self.assertFalse(result["post_authorized"])

    def test_seven_matches_are_not_generalized(self):
        result = validate_partition_design(self.config, self.action_review, self.value_review)
        self.assertEqual(result["seven_control_generalization_status"], "UNPROVEN_BEYOND_PINNED_PUBLIC_EXAMPLE")
        self.assertEqual(result["query_equivalent_status"], "OBSERVED_QUERY_VALUE_EQUALITY_ON_PINNED_PUBLIC_EXAMPLE_ONLY")

    def test_acao_stays_non_equivalent_and_semantics_unproven(self):
        result = validate_partition_design(self.config, self.action_review, self.value_review)
        self.assertEqual(result["non_equivalent_same_name_status"], "STABLE_NON_EQUIVALENT_SAME_NAME_ON_PINNED_PUBLIC_EXAMPLE")
        self.assertEqual(result["acao_value_origin_status"], "UNPROVEN")
        self.assertEqual(result["acao_query_semantics_status"], "UNPROVEN")

    def test_partition_overlap_or_coverage_fails_closed(self):
        config = copy.deepcopy(self.config)
        config["query_equivalent_control_names"] = list(config["query_equivalent_control_names"]) + ["acao"]
        with self.assertRaises(SiopePublicRuntimeQueryEquivalencePartitionDesignError):
            validate_partition_design(config, self.action_review, self.value_review)

    def test_prerequisite_cannot_promote_acao_or_post(self):
        action = copy.deepcopy(self.action_review)
        action["query_action_semantics_disposition"] = "PROVEN"
        with self.assertRaisesRegex(SiopePublicRuntimeQueryEquivalencePartitionDesignError, "ACTION_QUERY_SEMANTICS"):
            validate_partition_design(self.config, action, self.value_review)

    def test_second_example_must_be_explicit_not_synthesized(self):
        config = copy.deepcopy(self.config)
        config["second_example_must_be_explicitly_proven_not_synthesized"] = False
        with self.assertRaises(SiopePublicRuntimeQueryEquivalencePartitionDesignError):
            validate_partition_design(config, self.action_review, self.value_review)

    def test_operational_switches_cannot_be_opened(self):
        for key in ("network_access", "browser_execution", "dom_interaction", "form_submission", "post_request", "pilot_limeira_values_send", "automatic_value_promotion", "route_synthesis_or_guessing"):
            config = copy.deepcopy(self.config)
            config[key] = "ALLOWED"
            with self.assertRaises(SiopePublicRuntimeQueryEquivalencePartitionDesignError, msg=key):
                validate_partition_design(config, self.action_review, self.value_review)

    def test_design_code_is_offline_and_has_no_pilot_request(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_query_equivalence_partition_design.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_runtime_query_equivalence_partition_design_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        for forbidden in ("import requests", "from requests", "import urllib", "from urllib", "import websocket", "from websocket", "Page.navigate", "Fetch.enable", "cod_muni=352690"):
            self.assertNotIn(forbidden, combined)

    def test_next_gate_is_second_explicit_example_discovery_design(self):
        result = validate_partition_design(self.config, self.action_review, self.value_review)
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_DISCOVERY_DESIGN_0_8_0")


if __name__ == "__main__":
    unittest.main()
