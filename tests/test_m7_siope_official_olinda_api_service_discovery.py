from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_service_discovery import (
    ServiceResponse,
    SiopeOfficialOlindaApiServiceDiscoveryError,
    discover_service,
    dry_run,
    load_and_validate_design,
    load_json,
    parse_service_document,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_service_discovery.json"


class FakeTransport:
    def __init__(self, response: ServiceResponse):
        self.response = response
        self.request_count = 0
        self.calls = []

    def get(self, url, *, max_bytes, timeout_seconds, accepted_content_types):
        self.request_count += 1
        self.calls.append((url, max_bytes, timeout_seconds, accepted_content_types))
        return self.response


XML_SERVICE = b'''<?xml version="1.0" encoding="utf-8"?>
<service xmlns="http://www.w3.org/2007/app" xmlns:atom="http://www.w3.org/2005/Atom">
  <workspace>
    <atom:title>Default</atom:title>
    <collection href="Dados_Gerais_Siope"><atom:title>Dados_Gerais_Siope</atom:title></collection>
    <collection href="Receita_Siope"><atom:title>Receita_Siope</atom:title></collection>
  </workspace>
</service>'''


class TestM7SiopeOfficialOlindaApiServiceDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.design = load_and_validate_design(ROOT, cls.config)

    def test_dry_run_has_zero_network_and_no_authorization(self):
        result = dry_run(self.config, self.design)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertEqual(result["request_count"], 0)
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertFalse(result["collection_authorized"])

    def test_xml_service_document_returns_only_sanitized_collection_names(self):
        names = parse_service_document(XML_SERVICE, "application/xml", name_pattern=r"^[A-Za-z0-9_]+$", max_names=64)
        self.assertEqual(names, ("Dados_Gerais_Siope", "Receita_Siope"))

    def test_json_service_document_is_supported(self):
        raw = b'{"value":[{"name":"Dados_Gerais_Siope","url":"Dados_Gerais_Siope"},{"name":"Despesas_Siope","url":"Despesas_Siope"}]}'
        names = parse_service_document(raw, "application/json", name_pattern=r"^[A-Za-z0-9_]+$", max_names=64)
        self.assertEqual(names, ("Dados_Gerais_Siope", "Despesas_Siope"))

    def test_unsafe_collection_name_is_not_emitted(self):
        raw = b'''<service xmlns="http://www.w3.org/2007/app"><workspace><collection href="Dados_Gerais_Siope?token=secret"/><collection href="Receita_Siope"/></workspace></service>'''
        names = parse_service_document(raw, "application/xml", name_pattern=r"^[A-Za-z0-9_]+$", max_names=64)
        self.assertEqual(names, ("Receita_Siope",))

    def test_collection_limit_fails_closed(self):
        collections = "".join(f'<collection href="R{i}"/>' for i in range(65))
        raw = f'<service xmlns="http://www.w3.org/2007/app"><workspace>{collections}</workspace></service>'.encode()
        with self.assertRaises(SiopeOfficialOlindaApiServiceDiscoveryError):
            parse_service_document(raw, "application/xml", name_pattern=r"^[A-Za-z0-9_]+$", max_names=64)

    def test_exact_one_get_passes_when_candidate_is_present(self):
        transport = FakeTransport(ServiceResponse(200, "application/xml", XML_SERVICE))
        result = discover_service(self.config, self.design, transport=transport)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY")
        self.assertEqual(transport.request_count, 1)
        self.assertEqual(result["request_count"], 1)
        self.assertTrue(result["candidate_resource_present"])
        self.assertEqual(result["collection_names"], ["Dados_Gerais_Siope", "Receita_Siope"])
        self.assertFalse(result["raw_response_persisted"])
        self.assertFalse(result["query_values_persisted"])
        self.assertFalse(result["request_body_sent"])
        self.assertFalse(result["redirect_followed"])
        self.assertFalse(result["service_link_followed"])
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_REVIEW_0_8_0")

    def test_candidate_absent_stops_with_only_sanitized_diagnostics(self):
        raw = b'''<service xmlns="http://www.w3.org/2007/app"><workspace><collection href="Receita_Siope"/></workspace></service>'''
        transport = FakeTransport(ServiceResponse(200, "application/xml", raw))
        with self.assertRaises(SiopeOfficialOlindaApiServiceDiscoveryError) as ctx:
            discover_service(self.config, self.design, transport=transport)
        diagnostics = ctx.exception.diagnostics
        self.assertEqual(diagnostics["collection_names"], ["Receita_Siope"])
        self.assertFalse(diagnostics["candidate_resource_present"])
        self.assertNotIn("body", diagnostics)

    def test_config_cannot_open_query_redirect_post_or_pilot(self):
        mutations = {
            "query_keys": ["x"],
            "follow_redirects": True,
            "follow_service_links": True,
            "max_requests": 2,
            "request_body": True,
            "post_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "raw_response_persistence": "ALLOWED",
            "head_request": "ALLOWED",
            "collection_authorized": True,
            "schedule_enabled": True,
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiServiceDiscoveryError, msg=key):
                validate_config(config, self.design)

    def test_runtime_code_has_no_browser_post_or_head_request_path(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_service_discovery.py").read_text(encoding="utf-8")
        self.assertNotIn("Page.navigate", source)
        self.assertNotIn("websocket", source)
        self.assertNotIn('method="POST"', source)
        self.assertNotIn('method="HEAD"', source)
        self.assertNotIn("352690", source)


if __name__ == "__main__":
    unittest.main()
