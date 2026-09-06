import json
import unittest
from pathlib import Path


EVIDENCE = Path("docs/evidence/TASK_168B_PNCP_CONSULTA_CONTRACTS_FALLBACK_0.8.0.json")


class TestTask168BPncpConsultaContractsLiveEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_scope_and_complete_pagination_are_pinned(self):
        e = self.e
        self.assertEqual(e["exact_scope"]["cnpjOrgao"], "45132495000140")
        self.assertEqual(e["exact_scope"]["dataInicial"], "20260608")
        self.assertEqual(e["exact_scope"]["dataFinal"], "20260905")
        self.assertEqual(e["pagination"]["totalRegistros"], 759)
        self.assertEqual(e["pagination"]["totalPaginas"], 2)
        self.assertEqual(e["pagination"]["pages_scanned"], [1, 2])
        self.assertTrue(e["pagination"]["exhaustive_within_exact_scope"])

    def test_both_pages_were_http_200_with_source_hashes(self):
        e = self.e
        self.assertEqual(len(e["requests"]), 2)
        self.assertEqual([x["http_status"] for x in e["requests"]], [200, 200])
        self.assertEqual([x["bytes_received"] for x in e["requests"]], [773538, 404347])
        self.assertTrue(all(len(x["source_sha256"]) == 64 for x in e["requests"]))

    def test_zero_target_match_is_bounded_not_global(self):
        e = self.e
        self.assertEqual(e["result"]["target_match_count"], 0)
        self.assertEqual(
            e["result"]["scoped_conclusion"],
            "BOUNDED_NO_LINKED_CONTRACT_MATCH_IN_EXACT_DATE_CNPJ_SCOPE",
        )
        adj = e["epistemic_adjudication"]
        self.assertFalse(adj["global_pncp_contract_absence"])
        self.assertFalse(adj["future_contract_absence"])
        self.assertFalse(adj["purchase_absence"])
        self.assertTrue(adj["task166_stable_purchase_ids_remain_proven"])
        self.assertFalse(adj["pncp_no_match_created"])

    def test_financial_and_transaction_identity_remain_unproven(self):
        adj = self.e["epistemic_adjudication"]
        self.assertEqual(adj["payment_inference_from_pncp"], "FORBIDDEN")
        self.assertFalse(adj["eiti_financial_identity_proven"])
        self.assertFalse(adj["eiti_transaction_identity_proven"])
        self.assertIn("STILL_UNKNOWN", adj["scientific_state"])

    def test_no_raw_payload_persisted(self):
        self.assertFalse(self.e["execution"]["raw_payload_persisted"])


if __name__ == "__main__":
    unittest.main()
