from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from robo_dados_publicos.research.task216b_pncp_partitioned_strong_identity_fallback import (
    Task216BStop,
    _scan_page,
    build_url,
    execute,
    load_config,
)


class TestTask216BPartitionedStrongIdentityFallback(unittest.TestCase):
    def test_contract_is_monthly_exact_scope_and_fail_closed(self):
        cfg = load_config()
        self.assertEqual(cfg["issue"], 676)
        self.assertEqual(len(cfg["partitions"]), 9)
        self.assertEqual(cfg["partitions"][0]["dataInicial"], "20260101")
        self.assertEqual(cfg["partitions"][-1]["dataFinal"], "20260908")
        self.assertEqual(cfg["source"]["retryMax"], 0)
        self.assertEqual(cfg["source"]["redirectsMax"], 0)
        self.assertFalse(cfg["persistence"]["rawPayloadGit"])
        self.assertFalse(cfg["persistence"]["rawPayloadDrive"])
        self.assertFalse(cfg["persistence"]["rawPayloadWorkflowArtifact"])

    def test_url_preserves_partition_and_cnpj(self):
        cfg = load_config()
        part = cfg["partitions"][7]
        url = build_url(cfg, part, 2)
        q = parse_qs(urlparse(url).query)
        self.assertEqual(q["dataInicial"], ["20260801"])
        self.assertEqual(q["dataFinal"], ["20260831"])
        self.assertEqual(q["cnpjOrgao"], ["45132495000140"])
        self.assertEqual(q["pagina"], ["2"])
        self.assertEqual(q["tamanhoPagina"], ["500"])

    def test_complete_partitions_can_prove_one_strong_chain(self):
        cfg = load_config()

        def fake_fetch(url: str, timeout: int, max_bytes: int):
            q = parse_qs(urlparse(url).query)
            start = q["dataInicial"][0]
            if start == "20260801":
                data = [
                    {
                        "numeroControlePNCP": "PNCP-CONTRACT-1",
                        "numeroControlePNCPCompra": "PNCP-PURCHASE-1",
                        "numeroContratoEmpenho": "126/2026",
                        "anoContrato": 2026,
                        "processo": "900.433/2026",
                        "tipoContratoNome": "Contrato",
                        "niFornecedor": "52386933000162",
                    },
                    {
                        "numeroControlePNCP": "PNCP-EMPENHO-1",
                        "numeroControlePNCPCompra": "PNCP-PURCHASE-1",
                        "numeroContratoEmpenho": "6457/2026",
                        "anoContrato": 2026,
                        "processo": "900.433/2026",
                        "tipoContratoNome": "Nota de Empenho",
                        "niFornecedor": "52386933000162",
                    },
                ]
            else:
                data = []
            payload = {
                "data": data,
                "totalRegistros": len(data),
                "totalPaginas": 1 if data else 0,
                "numeroPagina": 1,
            }
            return {
                "http_status": 200,
                "bytes_received": 1,
                "content_type": "application/json",
                "sha256": "0" * 64,
                "transport_error": None,
                "url": url,
            }, payload

        with patch(
            "robo_dados_publicos.research.task216b_pncp_partitioned_strong_identity_fallback.fetch_route",
            side_effect=fake_fetch,
        ):
            got = execute(cfg)

        self.assertEqual(got["status"], "EXHAUSTIVE_COMPLETE_STRONG_CHAINS_FOUND")
        self.assertTrue(got["complete_all_partitions"])
        self.assertEqual(got["total_records_across_partitions"], 2)
        self.assertEqual(
            got["identity"]["counts"]["end_to_end_identity_chain_count"],
            1,
        )
        chain = got["identity"]["end_to_end_identity_chains"][0]
        self.assertEqual(chain["event_id"], "JOEV_2178029f7a825500c290")
        self.assertEqual(chain["jom_anchor_type"], "PROCESS_IDENTITY")
        self.assertEqual(chain["jom_anchor_value"], "900.433/2026")
        self.assertEqual(chain["canonical_commitment_key"], "2026:6457")
        self.assertEqual(chain["supplier_cnpj"], "52386933000162")
        self.assertFalse(chain["weak_fields_used"])

    def test_one_partition_transport_failure_stops_before_identity(self):
        cfg = load_config()

        def fake_fetch(url: str, timeout: int, max_bytes: int):
            q = parse_qs(urlparse(url).query)
            start = q["dataInicial"][0]
            if start == "20260401":
                return {
                    "http_status": 502,
                    "bytes_received": 0,
                    "content_type": None,
                    "sha256": None,
                    "transport_error": "HTTP_ERROR_502",
                    "url": url,
                }, None
            payload = {
                "data": [],
                "totalRegistros": 0,
                "totalPaginas": 0,
                "numeroPagina": 1,
            }
            return {
                "http_status": 200,
                "bytes_received": 1,
                "content_type": "application/json",
                "sha256": "0" * 64,
                "transport_error": None,
                "url": url,
            }, payload

        with patch(
            "robo_dados_publicos.research.task216b_pncp_partitioned_strong_identity_fallback.fetch_route",
            side_effect=fake_fetch,
        ):
            got = execute(cfg)

        self.assertEqual(
            got["status"],
            "STOP_PARTITION_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE",
        )
        self.assertEqual(got["failed_partition"], "2026-04")
        self.assertEqual(got["failed_page"], 1)
        self.assertFalse(got["complete_all_partitions"])
        self.assertNotIn("identity", got)

    def test_page_cap_is_fail_closed(self):
        cfg = load_config()
        payload = {
            "data": [],
            "totalRegistros": 0,
            "totalPaginas": 6,
            "numeroPagina": 1,
        }
        with self.assertRaises(Task216BStop):
            _scan_page(payload, 1, cfg)


if __name__ == "__main__":
    unittest.main()
