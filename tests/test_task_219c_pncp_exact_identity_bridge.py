import copy
import unittest

from robo_dados_publicos.research.task219c_pncp_exact_identity_bridge import (
    Task219CStop,
    adjudicate_pncp_records,
    load_combined_anchors,
    load_config,
    validate_owner_authorization,
)


def anchor(event_id, typ, value, supplier=None):
    return {
        "event_id": event_id,
        "event_type": "CONTRATO" if typ == "CONTRACT_IDENTITY" else "EDITAL",
        "publication_date": "2026-05-01",
        "anchor_type": typ,
        "anchor_value": value,
        "supplier_cnpj": supplier,
    }


def record(
    *,
    process="",
    contract="",
    purchase="P1",
    control="C1",
    type_name="Contrato",
    supplier=None,
    year=2026,
):
    row = {
        "processo": process,
        "numeroContratoEmpenho": contract,
        "numeroControlePNCPCompra": purchase,
        "numeroControlePNCP": control,
        "tipoContratoNome": type_name,
        "anoContrato": year,
    }
    if supplier:
        row["niFornecedor"] = supplier
    return row


class TestTask219CPncpExactIdentityBridge(unittest.TestCase):
    def test_canonical_input_is_449_rows_and_303_unique_identities(self):
        cfg = load_config()
        rows = load_combined_anchors(cfg)
        self.assertEqual(len(rows), 449)
        keys = {(r["anchor_type"], r["anchor_value"]) for r in rows}
        self.assertEqual(len(keys), 303)
        self.assertEqual(sum(1 for t, _ in keys if t == "PROCESS_IDENTITY"), 195)
        self.assertEqual(sum(1 for t, _ in keys if t == "CONTRACT_IDENTITY"), 108)

    def test_exact_process_allows_multiple_suppliers_when_purchase_identity_is_one(self):
        anchors = [
            anchor("JOEV_A", "PROCESS_IDENTITY", "900.001/2026", "11111111000111"),
            anchor("JOEV_B", "PROCESS_IDENTITY", "900.001/2026", "22222222000122"),
        ]
        records = [
            record(process="900.001/2026", purchase="PC1", control="R1", supplier="33333333000133"),
            record(
                process="900.001/2026",
                contract="123/2026",
                purchase="PC1",
                control="R2",
                type_name="Nota de Empenho",
                supplier="44444444000144",
            ),
        ]
        got = adjudicate_pncp_records(records, anchors)
        self.assertEqual(got["counts"]["matched_identity_count"], 1)
        self.assertEqual(got["counts"]["matched_process_identity_count"], 1)
        self.assertEqual(got["accepted_exact_identities"][0]["purchase_control_id"], "PC1")
        self.assertFalse(got["accepted_exact_identities"][0]["supplier_used_as_identity"])
        self.assertEqual(got["counts"]["typed_empenho_tce_candidate_count"], 1)
        self.assertFalse(got["end_to_end_jom_pncp_tce_chain_proven"])

    def test_exact_process_with_multiple_purchase_ids_is_conflict(self):
        anchors = [anchor("JOEV_A", "PROCESS_IDENTITY", "900.001/2026")]
        records = [
            record(process="900.001/2026", purchase="PC1", control="R1"),
            record(process="900.001/2026", purchase="PC2", control="R2"),
        ]
        got = adjudicate_pncp_records(records, anchors)
        self.assertEqual(got["counts"]["matched_identity_count"], 0)
        self.assertEqual(got["counts"]["conflict_identity_count"], 1)
        self.assertEqual(
            got["identity_conflicts"][0]["reason"],
            "MULTIPLE_PURCHASE_CONTROL_IDS_FOR_EXACT_IDENTIFIER",
        )

    def test_exact_typed_contract_with_matching_supplier_is_accepted(self):
        anchors = [anchor("JOEV_A", "CONTRACT_IDENTITY", "42/2026", "11111111000111")]
        records = [
            record(
                contract="42/2026",
                purchase="PC42",
                control="R42",
                type_name="Contrato",
                supplier="11111111000111",
            )
        ]
        got = adjudicate_pncp_records(records, anchors)
        self.assertEqual(got["counts"]["matched_contract_identity_count"], 1)
        self.assertEqual(got["accepted_exact_identities"][0]["purchase_control_id"], "PC42")

    def test_contract_supplier_conflict_is_blocked(self):
        anchors = [anchor("JOEV_A", "CONTRACT_IDENTITY", "42/2026", "11111111000111")]
        records = [
            record(
                contract="42/2026",
                purchase="PC42",
                control="R42",
                type_name="Contrato",
                supplier="22222222000122",
            )
        ]
        got = adjudicate_pncp_records(records, anchors)
        self.assertEqual(got["counts"]["matched_identity_count"], 0)
        self.assertEqual(got["identity_conflicts"][0]["reason"], "CONTRACT_SUPPLIER_CNPJ_CONFLICT")

    def test_non_contract_record_cannot_satisfy_contract_anchor(self):
        anchors = [anchor("JOEV_A", "CONTRACT_IDENTITY", "42/2026")]
        records = [
            record(
                contract="42/2026",
                purchase="PC42",
                control="R42",
                type_name="Nota de Empenho",
            )
        ]
        got = adjudicate_pncp_records(records, anchors)
        self.assertEqual(got["counts"]["matched_identity_count"], 0)

    def test_weak_fields_cannot_create_identity(self):
        anchors = [anchor("JOEV_A", "PROCESS_IDENTITY", "900.001/2026", "11111111000111")]
        row = record(process="999.999/2026", purchase="PC1", control="R1", supplier="11111111000111")
        row["objetoContrato"] = "same descriptive text"
        row["valorInicial"] = 100.0
        row["dataAssinatura"] = "2026-05-01"
        got = adjudicate_pncp_records([row], anchors)
        self.assertEqual(got["counts"]["matched_identity_count"], 0)

    def test_authorization_is_fresh_and_pinned(self):
        cfg = load_config()
        sha = "a" * 40
        auth = {
            "schema": "TASK219C_OWNER_AUTHORIZATION_V1",
            "task": "TASK_219C_LIVE_AUTHORIZATION",
            "implementation_sha": sha,
            "runtime_branch": cfg["runtime"]["branch"],
            "source": "PNCP",
            "operation": "BOUNDED_2026_PNCP_EXACT_IDENTITY_DISCOVERY_303_KEYS",
            "attempt_count": 1,
            "owner_authorized": True,
            "authorization_token_batch": 10,
            "authorization_token_consumed_for_this_operation": 4,
            "authorization_tokens_remaining_after_this_operation": 6,
            "max_total_remote_get_count": 18,
            "pncp_read_authorized": True,
            "task216_authorization_reused": False,
            "task219a_authorization_reused": False,
            "task219c_prior_authorization_reused": False,
            "tce_network_authorized": False,
            "drive_write_authorized": False,
            "serving_authorized": False,
            "publication_authorized": False,
            "promotion_authorized": False,
            "recurrence_authorized": False,
            "schedule_authorized": False,
        }
        got = validate_owner_authorization(auth, cfg=cfg, expected_implementation_sha=sha)
        self.assertEqual(got["authorization_token_consumed_for_this_operation"], 4)

        bad = copy.deepcopy(auth)
        bad["task216_authorization_reused"] = True
        with self.assertRaises(Task219CStop):
            validate_owner_authorization(bad, cfg=cfg, expected_implementation_sha=sha)

        bad = copy.deepcopy(auth)
        bad["implementation_sha"] = "b" * 40
        with self.assertRaises(Task219CStop):
            validate_owner_authorization(bad, cfg=cfg, expected_implementation_sha=sha)

        bad = copy.deepcopy(auth)
        bad["tce_network_authorized"] = True
        with self.assertRaises(Task219CStop):
            validate_owner_authorization(bad, cfg=cfg, expected_implementation_sha=sha)


if __name__ == "__main__":
    unittest.main()
