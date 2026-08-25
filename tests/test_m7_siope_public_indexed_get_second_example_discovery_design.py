from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_indexed_get_second_example_discovery_design import (
    SiopePublicIndexedGetSecondExampleDiscoveryDesignError,
    load_json,
    validate_discovery_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_indexed_get_second_example_discovery_design.json"


class TestM7SiopePublicIndexedGetSecondExampleDiscoveryDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.partition = load_json(ROOT / cls.config["partition_design_config_path"])
        cls.public = load_json(ROOT / cls.config["public_runtime_config_path"])

    def test_design_passes_without_selecting_candidate(self):
        result = validate_discovery_design(self.config, self.partition, self.public)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_DISCOVERY_DESIGN")
        self.assertFalse(result["candidate_selected"])
        self.assertEqual(result["candidate_status"], "UNRESOLVED_NO_EXPLICIT_ELIGIBLE_SECOND_EXAMPLE_PINNED")
        self.assertEqual(result["next_state"], "BLOCKED_PENDING_EXPLICIT_SECOND_PUBLIC_EXAMPLE")
        self.assertFalse(result["runtime_gate_creation_authorized"])

    def test_contract_is_current_exact_eight_key_shape(self):
        result = validate_discovery_design(self.config, self.partition, self.public)
        self.assertEqual(result["required_contract"]["host"], "www.fnde.gov.br")
        self.assertEqual(result["required_contract"]["path"], "/siope/dadosInformadosMunicipio.do")
        self.assertEqual(result["required_contract"]["query_keys"], ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"])

    def test_legacy_or_incomplete_surface_cannot_qualify(self):
        result = validate_discovery_design(self.config, self.partition, self.public)
        self.assertFalse(result["legacy_schema_eligible"])
        self.assertFalse(result["base_surface_without_complete_query_eligible"])

    def test_parameter_substitution_and_guessing_remain_prohibited(self):
        result = validate_discovery_design(self.config, self.partition, self.public)
        self.assertFalse(result["parameter_substitution_authorized"])
        self.assertFalse(result["route_synthesized_or_guessed"])
        for key in ("candidate_must_not_be_constructed_by_parameter_substitution", "candidate_must_not_be_synthesized_or_guessed"):
            config = copy.deepcopy(self.config)
            config[key] = False
            with self.assertRaises(SiopePublicIndexedGetSecondExampleDiscoveryDesignError, msg=key):
                validate_discovery_design(config, self.partition, self.public)

    def test_candidate_cannot_be_silently_added_in_design(self):
        config = copy.deepcopy(self.config)
        config["candidate_selected"] = True
        config["candidate_url"] = "https://example.invalid/"
        with self.assertRaises(SiopePublicIndexedGetSecondExampleDiscoveryDesignError):
            validate_discovery_design(config, self.partition, self.public)

    def test_generalization_and_runtime_remain_blocked(self):
        result = validate_discovery_design(self.config, self.partition, self.public)
        self.assertFalse(result["cross_example_generalization_authorized"])
        self.assertEqual(result["seven_control_generalization_status"], "UNPROVEN_BEYOND_PINNED_PUBLIC_EXAMPLE")
        self.assertEqual(result["acao_query_semantics_status"], "UNPROVEN")
        self.assertFalse(result["post_authorized"])
        self.assertFalse(result["pilot_limeira_values_sent"])

    def test_operational_switches_cannot_be_opened(self):
        for key in ("network_access", "browser_execution", "dom_interaction", "form_submission", "post_request", "pilot_limeira_values_send", "route_synthesis_or_guessing", "automatic_value_promotion"):
            config = copy.deepcopy(self.config)
            config[key] = "ALLOWED"
            with self.assertRaises(SiopePublicIndexedGetSecondExampleDiscoveryDesignError, msg=key):
                validate_discovery_design(config, self.partition, self.public)

    def test_design_code_is_offline_and_does_not_embed_pilot_request(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_indexed_get_second_example_discovery_design.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_indexed_get_second_example_discovery_design_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        self.assertIn("from urllib.parse import urlparse", combined)
        for forbidden in (
            "import requests",
            "from requests",
            "import urllib.request",
            "from urllib.request",
            "urlopen(",
            "import websocket",
            "from websocket",
            "Page.navigate",
            "Fetch.enable",
            "cod_muni=352690",
        ):
            self.assertNotIn(forbidden, combined)

    def test_future_candidate_requires_review_gate(self):
        result = validate_discovery_design(self.config, self.partition, self.public)
        self.assertEqual(result["next_gate_when_candidate_exists"], "M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_CANDIDATE_REVIEW_0_8_0")


if __name__ == "__main__":
    unittest.main()
