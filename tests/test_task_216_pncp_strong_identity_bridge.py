from __future__ import annotations

import unittest

from robo_dados_publicos.research.task216_pncp_strong_identity_bridge import (
    _canonical_pncp_commitment,
    _canonical_tce_commitment,
    _scan_page,
    adjudicate_records,
    load_config,
    load_jom_anchors,
    load_tce_index,
    normalize_admin_identifier,
)


class TestTask216PncpStrongIdentityBridge(unittest.TestCase):
    def test_contract_and_real_local_identity_inputs_validate(self):
        cfg = load_config()
        self.assertEqual(cfg["issue"], 676)
        self.assertEqual(cfg["pncp"]["retryMax"], 0)
        self.assertEqual(cfg["pncp"]["redirectsMax"], 0)
        self.assertFalse(cfg["persistence"]["rawPayloadGit"])
        self.assertFalse(cfg["persistence"]["rawPayloadDrive"])
        self.assertFalse(cfg["persistence"]["rawPayloadWorkflowArtifact"])

        tce = load_tce_index(cfg)
        self.assertEqual(tce["row_count"], 140)
        self.assertEqual(tce["supplier_count"], 31)
        self.assertEqual(
            tce["rows_sha256"],
            "d544bec0719a48ea33a2e06ca9232c95d8a96f34b7bcac64350ac842caa2fca6",
        )

        anchors = load_jom_anchors(cfg)
        self.assertTrue(anchors)
        weak_candidate = [
            row for row in anchors
            if row["event_id"] == "JOEV_2178029f7a825500c290"
        ]
        self.assertEqual(
            [(row["anchor_type"], row["anchor_value"]) for row in weak_candidate],
            [("PROCESS_IDENTITY", "900.433/2026")],
        )
        complete = [
            row for row in anchors
            if row["event_id"] == "JOEV_47b57708b7471058a828"
        ]
        self.assertEqual(
            {(row["anchor_type"], row["anchor_value"]) for row in complete},
            {
                ("CONTRACT_IDENTITY", "127/2026"),
                ("PROCESS_IDENTITY", "900.693/2026"),
            },
        )

    def test_identifier_cleanup_is_only_trailing_noise(self):
        self.assertEqual(normalize_admin_identifier(" 26.144/2025. "), "26.144/2025")
        self.assertEqual(normalize_admin_identifier("900.433/2026"), "900.433/2026")
        self.assertNotEqual(
            normalize_admin_identifier("900433/2026"),
            normalize_admin_identifier("900.433/2026"),
        )

    def test_typed_commitment_canonicalization(self):
        self.assertEqual(
            _canonical_pncp_commitment(
                {
                    "tipoContratoNome": "Nota de Empenho",
                    "numeroContratoEmpenho": "006457/2026",
                    "anoContrato": 2026,
                }
            ),
            "2026:6457",
        )
        self.assertIsNone(
            _canonical_pncp_commitment(
                {
                    "tipoContratoNome": "Contrato",
                    "numeroContratoEmpenho": "6457/2026",
                    "anoContrato": 2026,
                }
            )
        )
        self.assertEqual(
            _canonical_tce_commitment("2026:6457-2026"),
            "2026:6457",
        )
        self.assertIsNone(_canonical_tce_commitment("2025:6457-2026"))

    def test_process_to_purchase_to_typed_empenho_to_tce_is_strong_chain(self):
        anchors = [{
            "event_id": "J1",
            "event_type": "CONTRATO",
            "publication_date": "2026-08-20",
            "supplier_cnpj": "52386933000162",
            "anchor_type": "PROCESS_IDENTITY",
            "anchor_value": "900.433/2026",
        }]
        records = [
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
        tce = {
            "columns": ["commitment_number", "supplier_cnpj", "official_record_id"],
            "rows": [["2026:6457-2026", "52386933000162", "676972294"]],
        }
        got = adjudicate_records(records, anchors, tce)
        self.assertEqual(got["counts"]["end_to_end_identity_chain_count"], 1)
        chain = got["end_to_end_identity_chains"][0]
        self.assertEqual(chain["canonical_commitment_key"], "2026:6457")
        self.assertEqual(chain["supplier_cnpj"], "52386933000162")
        self.assertEqual(
            chain["identity_chain"],
            ["PROCESS_IDENTITY", "PNCP_PURCHASE_IDENTITY", "COMMITMENT_IDENTITY"],
        )
        self.assertFalse(chain["weak_fields_used"])
        self.assertEqual(
            chain["tce_matches"],
            [{"commitment_number": "2026:6457-2026", "official_record_id": "676972294"}],
        )

    def test_contract_anchor_never_matches_pncp_empenho_number(self):
        anchors = [{
            "event_id": "J2",
            "event_type": "CONTRATO",
            "publication_date": "2026-08-20",
            "supplier_cnpj": "29161710000185",
            "anchor_type": "CONTRACT_IDENTITY",
            "anchor_value": "127/2026",
        }]
        records = [{
            "numeroControlePNCP": "E1",
            "numeroControlePNCPCompra": "P1",
            "numeroContratoEmpenho": "127/2026",
            "anoContrato": 2026,
            "processo": "OTHER/2026",
            "tipoContratoNome": "Empenho",
            "niFornecedor": "29161710000185",
        }]
        tce = {"columns": ["commitment_number", "supplier_cnpj", "official_record_id"], "rows": []}
        got = adjudicate_records(records, anchors, tce)
        self.assertEqual(got["counts"]["accepted_jom_pncp_anchor_count"], 0)
        self.assertEqual(got["counts"]["end_to_end_identity_chain_count"], 0)

    def test_supplier_cnpj_alone_cannot_anchor(self):
        records = [{
            "numeroControlePNCP": "X",
            "numeroControlePNCPCompra": "P",
            "numeroContratoEmpenho": "6457/2026",
            "anoContrato": 2026,
            "processo": "UNRELATED/2026",
            "tipoContratoNome": "Empenho",
            "niFornecedor": "52386933000162",
        }]
        tce = {
            "columns": ["commitment_number", "supplier_cnpj", "official_record_id"],
            "rows": [["2026:6457-2026", "52386933000162", "676972294"]],
        }
        got = adjudicate_records(records, [], tce)
        self.assertEqual(got["counts"]["accepted_jom_pncp_anchor_count"], 0)
        self.assertEqual(got["counts"]["end_to_end_identity_chain_count"], 0)

    def test_supplier_conflict_blocks_exact_process_anchor(self):
        anchors = [{
            "event_id": "J3",
            "event_type": "CONTRATO",
            "publication_date": "2026-08-20",
            "supplier_cnpj": "52386933000162",
            "anchor_type": "PROCESS_IDENTITY",
            "anchor_value": "900.433/2026",
        }]
        records = [{
            "numeroControlePNCP": "C",
            "numeroControlePNCPCompra": "P",
            "numeroContratoEmpenho": "126/2026",
            "anoContrato": 2026,
            "processo": "900.433/2026",
            "tipoContratoNome": "Contrato",
            "niFornecedor": "00000000000000",
        }]
        tce = {"columns": ["commitment_number", "supplier_cnpj", "official_record_id"], "rows": []}
        got = adjudicate_records(records, anchors, tce)
        self.assertEqual(got["counts"]["accepted_jom_pncp_anchor_count"], 0)
        self.assertEqual(got["counts"]["anchor_conflict_count"], 1)
        self.assertEqual(got["anchor_conflicts"][0]["reason"], "SUPPLIER_CNPJ_CONFLICT")

    def test_purchase_siblings_require_exact_purchase_control(self):
        anchors = [{
            "event_id": "J4",
            "event_type": "CONTRATO",
            "publication_date": "2026-08-20",
            "supplier_cnpj": None,
            "anchor_type": "PROCESS_IDENTITY",
            "anchor_value": "900.433/2026",
        }]
        records = [
            {
                "numeroControlePNCP": "C",
                "numeroControlePNCPCompra": "PURCHASE-A",
                "numeroContratoEmpenho": "126/2026",
                "anoContrato": 2026,
                "processo": "900.433/2026",
                "tipoContratoNome": "Contrato",
            },
            {
                "numeroControlePNCP": "E-WRONG",
                "numeroControlePNCPCompra": "PURCHASE-B",
                "numeroContratoEmpenho": "6457/2026",
                "anoContrato": 2026,
                "processo": "OTHER",
                "tipoContratoNome": "Empenho",
                "niFornecedor": "52386933000162",
            },
        ]
        tce = {
            "columns": ["commitment_number", "supplier_cnpj", "official_record_id"],
            "rows": [["2026:6457-2026", "52386933000162", "676972294"]],
        }
        got = adjudicate_records(records, anchors, tce)
        self.assertEqual(
            {row["numeroControlePNCP"] for row in got["exact_purchase_siblings"]},
            {"C"},
        )
        self.assertEqual(got["counts"]["end_to_end_identity_chain_count"], 0)

    def test_page_validation_is_fail_closed(self):
        cfg = load_config()
        payload = {
            "data": [{"numeroControlePNCP": "X"}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "numeroPagina": 1,
        }
        got = _scan_page(payload, 1, cfg)
        self.assertEqual(got["record_count"], 1)
        bad = dict(payload)
        bad["numeroPagina"] = 2
        with self.assertRaises(Exception):
            _scan_page(bad, 1, cfg)


if __name__ == "__main__":
    unittest.main()
