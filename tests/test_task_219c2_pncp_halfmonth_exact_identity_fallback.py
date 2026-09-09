import copy
import unittest
from urllib.parse import parse_qs, urlparse

from robo_dados_publicos.research.task219c2_pncp_halfmonth_exact_identity_fallback import (
    Task219C2Stop,
    execute,
    load_config,
    validate_owner_authorization,
)


def auth(cfg, sha="a" * 40):
    return {
        "schema": "TASK219C2_OWNER_AUTHORIZATION_V1",
        "task": "TASK_219C2_LIVE_AUTHORIZATION",
        "implementation_sha": sha,
        "runtime_branch": cfg["runtime"]["branch"],
        "source": "PNCP",
        "operation": "BOUNDED_2026_PNCP_HALFMONTH_EXACT_IDENTITY_DISCOVERY_303_KEYS",
        "attempt_count": 1,
        "owner_authorized": True,
        "authorization_token_batch": 10,
        "authorization_token_consumed_for_this_operation": 5,
        "authorization_tokens_remaining_after_this_operation": 5,
        "max_total_remote_get_count": 54,
        "pncp_read_authorized": True,
        "task216_authorization_reused": False,
        "task219a_authorization_reused": False,
        "task219c_authorization_reused": False,
        "task219c2_prior_authorization_reused": False,
        "tce_network_authorized": False,
        "drive_write_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
    }


class FakeSource:
    def __init__(self):
        self.calls = []

    def fetch(self, url, timeout, max_bytes):
        self.calls.append((url, timeout, max_bytes))
        qs = parse_qs(urlparse(url).query)
        self_page = int(qs["pagina"][0])
        assert self_page == 1
        assert qs["tamanhoPagina"] == ["250"]
        start = qs["dataInicial"][0]
        if start == "20260101":
            data = [{
                "processo": "900.195/2026",
                "numeroControlePNCPCompra": "PC-EXACT-1",
                "numeroControlePNCP": "REC-1",
                "numeroContratoEmpenho": "1/2026",
                "anoContrato": 2026,
                "tipoContratoNome": "Contrato",
                "niFornecedor": "04491116000121",
            }]
        else:
            data = []
        return (
            {
                "http_status": 200,
                "bytes_received": 100,
                "content_type": "application/json",
                "sha256": "b" * 64,
                "transport_error": None,
                "url": url,
            },
            {
                "data": data,
                "totalRegistros": len(data),
                "totalPaginas": 1 if data else 0,
                "numeroPagina": 1,
            },
        )


class TestTask219C2PncpHalfmonthFallback(unittest.TestCase):
    def test_contract_is_exact_contiguous_halfmonth_scope(self):
        cfg = load_config()
        self.assertEqual(len(cfg["partitions"]), 18)
        self.assertEqual(cfg["partitions"][0]["dataInicial"], "20260101")
        self.assertEqual(cfg["partitions"][-1]["dataFinal"], "20260908")
        self.assertEqual(cfg["source"]["tamanhoPagina"], 250)
        self.assertEqual(cfg["source"]["maxPaginasPerPartition"], 3)
        self.assertEqual(cfg["source"]["maxTotalRemoteGets"], 54)
        self.assertEqual(cfg["source"]["timeoutSeconds"], 120)
        self.assertEqual(cfg["source"]["retryMax"], 0)
        self.assertEqual(cfg["source"]["redirectsMax"], 0)
        self.assertFalse(cfg["first_runtime"]["authorization_reuse_allowed"])
        self.assertEqual(cfg["first_runtime"]["remote_get_count"], 1)
        self.assertEqual(cfg["first_runtime"]["bytes_received"], 0)
        self.assertEqual(cfg["first_runtime"]["scientific_effect"], "NONE")

    def test_fresh_token5_authorization_is_required(self):
        cfg = load_config()
        good = auth(cfg)
        got = validate_owner_authorization(good, cfg=cfg, expected_implementation_sha="a" * 40)
        self.assertEqual(got["authorization_token_consumed_for_this_operation"], 5)
        self.assertEqual(got["authorization_tokens_remaining_after_this_operation"], 5)

        for key in (
            "task216_authorization_reused",
            "task219a_authorization_reused",
            "task219c_authorization_reused",
            "task219c2_prior_authorization_reused",
            "tce_network_authorized",
            "drive_write_authorized",
            "serving_authorized",
            "publication_authorized",
            "promotion_authorized",
        ):
            bad = copy.deepcopy(good)
            bad[key] = True
            with self.assertRaises(Task219C2Stop):
                validate_owner_authorization(bad, cfg=cfg, expected_implementation_sha="a" * 40)

    def test_offline_fake_execution_uses_18_exact_partitions_and_adjudicates(self):
        cfg = load_config()
        src = FakeSource()
        got = execute(
            cfg,
            source=src,
            authorization=auth(cfg),
            expected_implementation_sha="a" * 40,
        )
        self.assertTrue(got["complete_all_partitions"])
        self.assertEqual(got["total_records_across_partitions"], 1)
        self.assertEqual(len(got["requests"]), 18)
        self.assertEqual(len(src.calls), 18)
        self.assertEqual(got["status"], "EXHAUSTIVE_COMPLETE_PNCP_EXACT_IDENTITIES_FOUND")
        counts = got["identity"]["counts"]
        self.assertEqual(counts["matched_identity_count"], 1)
        self.assertEqual(counts["matched_process_identity_count"], 1)
        self.assertEqual(counts["matched_purchase_id_count"], 1)
        self.assertFalse(got["identity"]["end_to_end_jom_pncp_tce_chain_proven"])
        self.assertFalse(got["promotion_performed"])
        self.assertEqual(got["drive_write_count"], 0)
        self.assertEqual(got["publication_count"], 0)


if __name__ == "__main__":
    unittest.main()
