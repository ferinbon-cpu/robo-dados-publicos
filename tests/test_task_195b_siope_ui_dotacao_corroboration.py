import json
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task195b_siope_ui_dotacao_corroboration.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_195B_SIOPE_UI_DOTACAO_CORROBORATION_0.8.0.json"


class TestTask195BSiopeUiDotacaoCorroboration(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_scope_is_exact_official_ui_dotacao(self):
        scope = self.config["scope"]
        self.assertEqual(scope["year"], 2025)
        self.assertEqual(scope["period"], "Anual")
        self.assertEqual(scope["municipality"], "Limeira")
        self.assertEqual(scope["expense_phase"], "Dotação Atualizada")
        self.assertEqual(
            scope["report_title"],
            "Quadro Resumo da Dotação Atualizada Segundo SubFunções/Natureza",
        )

    def test_raw_artifacts_are_pinned(self):
        a = self.config["drive_artifacts"]
        self.assertEqual(a["csv"]["bytes"], 6775)
        self.assertEqual(
            a["csv"]["sha256"],
            "6e3b7d7043b22fc5862994e0c5d92f36c5be3c8c208958e8dd02041175d1b499",
        )
        self.assertEqual(a["screenshot"]["bytes"], 143818)
        self.assertEqual(a["derived_evidence"]["bytes"], 3449)

    def test_detail_rows_sum_exactly_to_official_total(self):
        rows = self.config["nonzero_detail_rows"]
        self.assertEqual(len(rows), 9)
        total = sum((Decimal(r["value"]) for r in rows), Decimal("0"))
        self.assertEqual(total, Decimal("526804985.21"))
        self.assertEqual(
            Decimal(self.config["official_ui_total"]["value"]),
            Decimal("526804985.21"),
        )

    def test_ui_total_exactly_corroborates_m3(self):
        r = self.config["cross_evidence_reconciliation"]
        self.assertEqual(Decimal(r["difference"]), Decimal("0.00"))
        self.assertEqual(
            Decimal(r["previous_m3_consolidated_DA_total"]),
            Decimal(r["ui_csv_total"]),
        )
        self.assertEqual(r["status"], "INDEPENDENT_EXACT_CORROBORATION")
        self.assertTrue(self.evidence["reconciliation"]["all_equal"])

    def test_alias_comparison_preserves_all_three_distinct_values(self):
        c = self.config["alias_comparison"]
        self.assertEqual(
            Decimal(c["UI_TOTAL"]) - Decimal(c["VL_DESP_DOTA_ATUA_EDU"]),
            Decimal("6405729.74"),
        )
        self.assertEqual(
            Decimal(c["UI_TOTAL"]) - Decimal(c["RREO_LINE_33_DA"]),
            Decimal("6406729.74"),
        )
        self.assertEqual(
            Decimal(c["VL_DESP_DOTA_ATUA_EDU"]) - Decimal(c["RREO_LINE_33_DA"]),
            Decimal("1000.00"),
        )

    def test_fail_closed_decision(self):
        a = self.config["adjudication"]
        self.assertEqual(a["VL_DESP_DOTA_ATUA_EDU"], "NOT_PROVEN")
        self.assertEqual(a["S2_FINANCIAL_ALIAS_BRIDGE"], "NOT_PROVEN")
        self.assertEqual(
            self.evidence["decision"],
            "KEEP_VL_DESP_DOTA_ATUA_EDU_AND_S2_NOT_PROVEN",
        )
        self.assertIn("NO_S2_PROMOTION", self.config["guards"])


if __name__ == "__main__":
    unittest.main()
