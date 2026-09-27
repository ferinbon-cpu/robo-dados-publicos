from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_discovery_design import (
    SiopeOfficialOlindaApiDiscoveryDesignError,
    load_json,
    validate_discovery_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_discovery_design.json"


class TestM7SiopeOfficialOlindaApiDiscoveryDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.base = load_json(ROOT / cls.config["base_source_config_path"])
        cls.html = load_json(ROOT / cls.config["blocked_html_track_config_path"])
        cls.research = load_json(ROOT / cls.config["public_research_evidence_path"])

    def validate(self, config=None):
        return validate_discovery_design(config or self.config, self.base, self.html, self.research)

    def test_design_passes_offline_and_routes_to_service_discovery(self):
        result = self.validate()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_DISCOVERY_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_0_8_0")

    def test_exact_official_root_has_no_query_or_pilot_values(self):
        result = self.validate()
        contract = result["official_service_contract"]
        self.assertEqual(contract["host"], "www.fnde.gov.br")
        self.assertEqual(contract["path"], "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/")
        self.assertEqual(contract["query_keys"], [])
        self.assertEqual(contract["max_requests"], 1)
        self.assertNotIn("352690", self.config["official_service_root"])
        self.assertNotIn("Limeira", self.config["official_service_root"])

    def test_html_track_remains_blocked_and_independent(self):
        result = self.validate()
        self.assertEqual(result["html_track_status"], "BLOCKED_PENDING_EXPLICIT_SECOND_PUBLIC_EXAMPLE")
        self.assertEqual(result["alternate_track_status"], "DESIGN_ONLY_UNVERIFIED_SERVICE_DOCUMENT")
        self.assertFalse(self.html["runtime_gate_creation_authorized"])

    def test_resource_is_reference_candidate_not_runtime_proof(self):
        result = self.validate()
        self.assertEqual(result["public_reference_candidate_resource"], "Dados_Gerais_Siope")
        self.assertEqual(result["candidate_resource_runtime_status"], "UNPROVEN_BY_REPO_RUNTIME")
        self.assertEqual(result["parameter_semantics_runtime_status"], "UNPROVEN_BY_REPO_RUNTIME")

    def test_operational_switches_remain_closed(self):
        result = self.validate()
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertFalse(result["collection_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertFalse(result["schedule_enabled"])
        for key in (
            "network_access", "browser_execution", "dom_interaction", "form_submission",
            "post_request", "pilot_limeira_values_send", "authentication", "captcha_bypass",
            "head_request", "artifact_download", "remote_writes", "route_synthesis_or_guessing",
            "automatic_value_promotion",
        ):
            config = copy.deepcopy(self.config)
            config[key] = "ALLOWED"
            with self.assertRaises(SiopeOfficialOlindaApiDiscoveryDesignError, msg=key):
                self.validate(config)

    def test_live_probe_cannot_gain_query_body_or_multiple_requests(self):
        for key, bad in (("query_keys", ["x"]), ("request_body", True), ("max_requests", 2), ("municipality_parameter", True), ("year_parameter", True)):
            config = copy.deepcopy(self.config)
            config["initial_live_probe"][key] = bad
            with self.assertRaises(SiopeOfficialOlindaApiDiscoveryDesignError, msg=key):
                self.validate(config)

    def test_design_code_is_offline(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_discovery_design.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_official_olinda_api_discovery_design_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        self.assertIn("from urllib.parse import urlparse", combined)
        for forbidden in (
            "import requests", "from requests", "import urllib.request", "from urllib.request",
            "urlopen(", "import websocket", "Page.navigate", "Fetch.enable", "cod_muni=352690",
        ):
            self.assertNotIn(forbidden, combined)

    def test_tampered_prerequisite_or_research_fails_closed(self):
        html = copy.deepcopy(self.html)
        html["runtime_gate_creation_authorized"] = True
        with self.assertRaises(SiopeOfficialOlindaApiDiscoveryDesignError):
            validate_discovery_design(self.config, self.base, html, self.research)

        research = copy.deepcopy(self.research)
        research["repo_interpretation"]["limeira_api_request_authorized"] = True
        with self.assertRaises(SiopeOfficialOlindaApiDiscoveryDesignError):
            validate_discovery_design(self.config, self.base, self.html, research)


if __name__ == "__main__":
    unittest.main()
