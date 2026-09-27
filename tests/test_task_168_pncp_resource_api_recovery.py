import unittest
from pathlib import Path

from robo_dados_publicos.research.task168_pncp_resource_api_recovery import (
    Task168Stop,
    build_target_url,
    load_config,
    sanitize_preflight,
    validate_cross_route_control_identity,
)


def config():
    return load_config(Path("config/task168_pncp_resource_api_recovery.v1.json"))


class TestTask168PncpResourceApiRecovery(unittest.TestCase):
    def test_config_pins_minimal_preflight_and_bounded_budget(self):
        cfg = config()
        self.assertEqual(
            cfg["preflight"]["url"],
            "https://pncp.gov.br/api/pncp/v1/modalidades?statusAtivo=true",
        )
        self.assertEqual(cfg["requestBudget"]["totalMaxIfHealthy"], 7)
        self.assertEqual(cfg["requestBudget"]["totalMaxIfPreflightUnavailable"], 1)
        self.assertFalse(cfg["fallback"]["htmlDomJsReverseEngineeringAuthorized"])

    def test_target_urls_stay_on_documented_resource_api_family(self):
        cfg = config()
        target = cfg["targets"][0]
        urls = [
            build_target_url(cfg, target, route)
            for route in cfg["essentialRoutes"]
        ]
        self.assertEqual(
            urls[0],
            "https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/368",
        )
        self.assertTrue(urls[1].endswith("/compras/2026/368/fonte-orcamentaria"))
        self.assertTrue(urls[2].endswith("/contratos/contratacao/2026/368"))

    def test_preflight_requires_active_modality_9(self):
        payload = [
            {"id": 6, "nome": "Pregão", "statusAtivo": True},
            {"id": 9, "nome": "Inexigibilidade", "statusAtivo": True},
        ]
        sanitized = sanitize_preflight(payload, 9, "Inexigibilidade")
        self.assertEqual(sanitized["required_modality"]["id"], 9)
        self.assertTrue(sanitized["required_modality"]["statusAtivo"])

    def test_preflight_fails_closed_when_required_domain_identity_missing(self):
        with self.assertRaises(Task168Stop):
            sanitize_preflight(
                [{"id": 6, "nome": "Pregão", "statusAtivo": True}],
                9,
                "Inexigibilidade",
            )

    def test_budget_source_control_identity_mismatch_fails_closed(self):
        target = config()["targets"][0]
        payload = [{"numeroControlePNCPCompra": "45132495000140-1-000999/2026"}]
        with self.assertRaises(Task168Stop):
            validate_cross_route_control_identity(payload, target, "BUDGET_SOURCES")

    def test_contract_control_identity_exact_value_is_accepted(self):
        target = config()["targets"][1]
        payload = [{"numeroControlePNCPCompra": target["numeroControlePNCP"]}]
        result = validate_cross_route_control_identity(payload, target, "LINKED_CONTRACTS")
        self.assertTrue(result["identity_confirmed_by_payload_field"])


if __name__ == "__main__":
    unittest.main()
