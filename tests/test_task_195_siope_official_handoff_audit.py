import json
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task195_siope_official_handoff_audit.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_195_SIOPE_OFFICIAL_HANDOFF_AUDIT_0.8.0.json"


class TestTask195SiopeOfficialHandoffAudit(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_scope_and_provenance_are_pinned(self):
        scope = self.config["scope"]
        self.assertEqual(scope["tipo"], "Municipal")
        self.assertEqual(scope["num_ano"], 2025)
        self.assertEqual(scope["num_peri"], 6)
        self.assertEqual(scope["sig_uf"], "SP")
        self.assertEqual(scope["cod_muni"], 352690)
        self.assertEqual(scope["nom_muni"], "Limeira")
        self.assertFalse(self.config["provenance"]["raw_endpoint_bytes_preserved"])
        self.assertIsNone(self.config["provenance"]["raw_endpoint_sha256"])
        self.assertTrue(self.config["provenance"]["derived_evidence_ne_raw_endpoint_capture"])

    def test_receita_labels_and_alias_reconciliations_are_exact(self):
        labels = self.config["receita_labels"]
        self.assertEqual(labels["PA"], "Previsão Atualizada")
        self.assertEqual(labels["RR"], "Receitas Realizadas")
        self.assertEqual(labels["DF"], "Deduções FUNDEB")

        prev = self.config["exact_reconciliations"]["VAL_RECE_PREV_ATUA"]
        real = self.config["exact_reconciliations"]["VAL_RECE_REAL"]
        self.assertEqual(
            Decimal(prev["receitas_correntes_pa"]) + Decimal(prev["receitas_capital_pa"]),
            Decimal(prev["existing_alias_value"]),
        )
        self.assertEqual(Decimal(prev["variance"]), Decimal("0.00"))
        self.assertEqual(
            Decimal(real["receitas_correntes_rr"]) + Decimal(real["receitas_capital_rr"]),
            Decimal(real["existing_alias_value"]),
        )
        self.assertEqual(Decimal(real["variance"]), Decimal("0.00"))

    def test_despesa_labels_and_vaar_cross_resource_equality(self):
        labels = self.config["despesas_labels"]
        self.assertEqual(labels, {
            "DE": "Desp. Empenhadas",
            "DL": "Desp. Liquidadas",
            "DP": "Desp. Pagas",
        })
        vaar = self.config["exact_reconciliations"]["VAAR"]
        vals = {
            Decimal(vaar["receita_realizada_rr"]),
            Decimal(vaar["despesa_empenhada_de"]),
            Decimal(vaar["despesa_liquidada_dl"]),
            Decimal(vaar["despesa_paga_dp"]),
        }
        self.assertEqual(vals, {Decimal("885554.43")})

    def test_drive_artifacts_are_pinned_by_id_size_and_derived_hash(self):
        artifacts = self.config["drive_artifacts"]
        self.assertEqual(artifacts["receita_evidence"]["id"], "1XS0swEF0pgBdTjPII51z4PJFctwe0grT")
        self.assertEqual(artifacts["receita_evidence"]["size_bytes"], 3959)
        self.assertEqual(
            artifacts["receita_evidence"]["sha256"],
            "8c105d51d5227b3deac5afa03e67e853e0f4cdf4f9d9893c59976fc5bdcf5b73",
        )
        self.assertEqual(artifacts["despesas_probe_evidence"]["size_bytes"], 5466)
        self.assertEqual(artifacts["manifest"]["size_bytes"], 1546)

    def test_transport_finding_does_not_trigger_unneeded_client_patch(self):
        t = self.config["transport_findings"]
        self.assertEqual(t["canonical_robot_dados_gerais_filter_encoding"], "%20")
        self.assertTrue(t["canonical_robot_client_already_uses_percent20"])
        self.assertTrue(t["manual_plus_space_encoding_observed_as_invalid"])
        self.assertFalse(t["robot_client_patch_required"])

    def test_fail_closed_blockers_remain_open(self):
        blockers = self.config["remaining_blockers"]
        self.assertEqual(blockers["S1_NUM_POPU"], "NOT_PROVEN")
        self.assertEqual(blockers["VL_DESP_DOTA_ATUA_EDU"], "NOT_PROVEN_PENDING_DA_SOURCE_DEFINED_ROWS_AND_RULE")
        self.assertEqual(blockers["S2_FINANCIAL_ALIAS_BRIDGE"], "NOT_PROVEN")
        self.assertEqual(self.evidence["adjudication"]["VL_DESP_DOTA_ATUA_EDU"], "NOT_PROVEN")
        self.assertEqual(self.evidence["next_probe"], "DESPESAS_SIOPE_LIMEIRA_2025_P6_IDN_CLAS_DA")
        self.assertIn("MISSING_DA_NE_ZERO", self.config["guards"])
        self.assertIn("NO_S2_PROMOTION_BEFORE_DA_RULE_PROOF", self.evidence["guards"])


if __name__ == "__main__":
    unittest.main()
