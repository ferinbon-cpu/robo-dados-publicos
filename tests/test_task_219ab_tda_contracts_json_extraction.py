from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219AB_TDA_CONTRACTS_JSON_EXTRACTION_0.8.0.json"


class TestTask219ABTDAContractsJsonExtraction(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_schema_status_and_route_correction(self) -> None:
        obj = self.obj
        self.assertEqual(obj["schema"], "TASK219AB_TDA_CONTRACTS_JSON_EXTRACTION_V1")
        self.assertEqual(obj["task"], "TASK_219AB")
        self.assertEqual(obj["issue"], 746)
        self.assertEqual(obj["status"], "PASS_OFFICIAL_TDA_CONTRACTS_MACHINE_READABLE_EXTRACTION")
        self.assertEqual(obj["source"]["acquisition_control"], "THREE_BARS_EXTRACTION_MENU")
        self.assertTrue(obj["source"]["json_icon_inside_extraction_panel"])
        self.assertFalse(obj["source"]["black_cloud_icon_was_source"])
        self.assertFalse(obj["artifact"]["raw_zip_committed"])
        self.assertFalse(obj["artifact"]["raw_json_committed"])

    def test_hashes_export_status_and_filters(self) -> None:
        obj = self.obj
        self.assertEqual(obj["artifact"]["outer_sha256"], "16f40d099b5234116ccd264202cdea127de7c5d36abbfb81a38d513e51a7c0b9b")
        self.assertEqual(obj["artifact"]["inner_sha256"], "7a7a995c9d41c83889da5eb422c92643e309b89485d3c109f291313fc2633b9b")
        self.assertEqual(obj["export_metadata"]["Status"], "OK")
        self.assertEqual(obj["export_metadata"]["Usuario"], "Convidado")
        self.assertEqual(obj["filters"]["Ano Contrato"], "2026")
        self.assertEqual(obj["filters"]["Nro Contrato"], "45")

    def test_summary_row_is_not_counted_as_contract(self) -> None:
        sem = self.obj["row_semantics"]
        self.assertEqual(sem["raw_valores_row_count"], 2)
        self.assertEqual(sem["summary_total_row_count"], 1)
        self.assertEqual(sem["data_row_count"], 1)
        self.assertFalse(sem["summary_row_is_contract"])

    def test_exact_machine_readable_contract_row(self) -> None:
        row = self.obj["contract_row"]
        self.assertEqual(row["Ano"], "2026")
        self.assertEqual(row["Nro SIAM (Fiscalizadores)"], "0000000045")
        self.assertEqual(row["normalized_contract_number"], "45/2026")
        self.assertEqual(row["supplier_cnpj_digits"], "37457979000131")
        self.assertEqual(row["Fornecedor"], "Med Doctor Acessorios Ltda")
        self.assertEqual(row["Data Inicial"], "13/04/2026")
        self.assertEqual(row["Data final"], "12/04/2027")
        self.assertEqual(row["Valor Contratado"], "210000.00")
        self.assertEqual(row["Valor Empenhado"], "174999.99")
        self.assertEqual(row["Valor Processado"], "35000.00")
        self.assertEqual(row["Valor Pago"], "35000.00")
        self.assertEqual(row["Objeto Contrato"], "LOCACAO DE SISTEMA DE ENDOSCOPIA")
        self.assertEqual(row["typed_procurement_identifier"], "E00010/2026")
        self.assertEqual(row["Nro Processo Adm"], "902281")

    def test_strong_edge_and_weak_join_guards(self) -> None:
        role = self.obj["identity_role"]
        self.assertTrue(role["machine_readable_tda_contract_row_proven"])
        self.assertTrue(role["typed_procurement_identifier_proven_in_contract_row"])
        self.assertEqual(role["strong_bridge_to_task219aa_empenhado_export_key"], "E00010/2026")
        self.assertFalse(role["supplier_cnpj_is_primary_identity_edge"])
        self.assertFalse(role["amount_is_primary_identity_edge"])
        self.assertFalse(role["object_text_is_primary_identity_edge"])
        self.assertFalse(role["weak_join_used"])
        self.assertTrue(all(v is False for v in self.obj["claim_boundaries"].values()))
        self.assertTrue(all(v is False for v in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
