from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash import (
    F02FundebMonthlyCashStop,
    parse_monthly_text,
    reconcile_series,
    run_monthly_series,
    validate_contract,
    validate_manifest,
    validate_runtime_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/f02_fundeb_monthly_cash_series.v1.json"
AUTH = ROOT / "docs/evidence/f02_fundeb_monthly_cash/F02_FUNDEB_MONTHLY_2026_JAN_MAR_RUNTIME_AUTHORIZATION.json"


def monthly_text(month_name, opening, transfer, auto_income, classic_income, fti, inflows, outflows, closing, opening_eti=None, closing_eti=()):
    opening_lines = [
        "SALDO INICIAL Contabilidade Banco Diferença",
        f"(1) Conta Corrente - Nº 112.185-5 {opening} {opening} -",
    ]
    if opening_eti is not None:
        opening_lines.append(f"(2) Conta Corrente - Nº 112.185-5 ETI {opening_eti} {opening_eti} -")
    closing_lines = [
        "SALDO FINAL Contabilidade Banco Diferença",
        f"(22) Conta Corrente - Nº 112.185-5 {closing} {closing}",
    ]
    for i, value in enumerate(closing_eti, start=23):
        label = "Conta Corrente - Nº 112.185-5 ETI" if i == 23 else "Conta Corrente - Nº 114.947-4 (Residual) ETI"
        closing_lines.append(f"({i}) {label} {value} {value} 0,00")
    return "\n".join([
        "Prefeitura Municipal de Limeira",
        "Secretaria Municipal de Fazenda",
        "Divisão de Contabilidade",
        f"DEMONSTRATIVO MENSAL - RECURSOS DO FUNDEB - {month_name}/2026",
        *opening_lines,
        f"(3) TOTAL DO SALDO INICIAL (SOMA 1+2)=(3) {opening} {opening} -",
        "ENTRADAS Contabilidade Banco Diferença",
        f"(4) Transferências de Recursos do FUNDEB {transfer} {transfer} -",
        f"(6) Rendimento da Aplicação Financeira automatico {auto_income} {auto_income} -",
        f"BB RF CP Clássico {classic_income} {classic_income} -",
        f"(9) FTI- Fomento Tempo Integral {fti} {fti}",
        f"(9) TOTAL DAS ENTRADAS (SOMA 4+5+6+7+8)=(9) {inflows} {inflows} -",
        "SAÍDAS Contabilidade Banco Diferença",
        f"(24) TOTAL DAS SAÍDAS (SOMA 10...+...23)=(24) {outflows} {outflows} -",
        *closing_lines,
        f"(25) TOTAL DO SALDO FINAL (3)+(9)-(21)=(25) {closing} {closing} -",
    ])


JAN = monthly_text(
    "JANEIRO","17.741.157,40","19.807.535,04","107.669,53","9.650,43","182.462,26",
    "20.107.317,26","16.693.636,32","21.154.838,34",None,("1.232.081,93",)
)
FEB = monthly_text(
    "FEVEREIRO","21.154.838,34","12.642.357,44","133.147,86","9.011,80","0,00",
    "12.784.517,10","12.364.203,27","21.575.152,17","1.232.081,93",("1.241.093,73",)
)
MAR = monthly_text(
    "MARÇO","21.575.152,17","22.432.987,30","194.416,88","6.392,76","0,00",
    "22.633.796,94","13.136.468,10","31.072.481,01","1.241.093,73",("209.410,12","1.047.521,08")
)


class F02FundebMonthlyCashTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.authorization = json.loads(AUTH.read_text(encoding="utf-8"))

    def test_exact_monthly_values_and_semantic_boundary(self):
        jan = parse_monthly_text(JAN)
        feb = parse_monthly_text(FEB)
        mar = parse_monthly_text(MAR)
        self.assertEqual(jan["period"], "2026-01")
        self.assertEqual(jan["explicit_fti_inflow"], "182462.26")
        self.assertIsNone(jan["eti_opening_labeled_total"])
        self.assertEqual(jan["eti_closing_labeled_total"], "1232081.93")
        self.assertEqual(feb["eti_opening_labeled_total"], "1232081.93")
        self.assertEqual(feb["eti_closing_labeled_total"], "1241093.73")
        self.assertEqual(mar["eti_opening_labeled_total"], "1241093.73")
        self.assertEqual(mar["eti_closing_labeled_total"], "1256931.20")
        for record in (jan, feb, mar):
            self.assertFalse(record["semantic_scope"]["eti_spending_claim_authorized"])
            self.assertFalse(record["semantic_scope"]["eti_liquidated_claim_authorized"])

    def test_series_reconciliation_closes_jan_feb_mar(self):
        series = reconcile_series([
            parse_monthly_text(JAN),
            parse_monthly_text(FEB),
            parse_monthly_text(MAR),
        ])
        self.assertEqual(series["status"], "PASS_F02_FUNDEB_MONTHLY_SERIES_RECONCILIATION")
        self.assertEqual(series["months"], 3)
        self.assertEqual(series["period_start"], "2026-01")
        self.assertEqual(series["period_end"], "2026-03")
        self.assertEqual(
            series["continuity"][0]["explicit_eti_balance"],
            "PASS_EXPLICIT_ETI_BALANCE_CONTINUITY",
        )

    def test_monthly_identity_or_bank_divergence_fails_closed(self):
        bad = JAN.replace("21.154.838,34 21.154.838,34 -", "21.154.838,35 21.154.838,35 -")
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "ACCOUNTING_IDENTITY"):
            parse_monthly_text(bad)
        bad_bank = JAN.replace("20.107.317,26 20.107.317,26 -", "20.107.317,26 20.107.317,25 -")
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "ACCOUNTING_BANK_DIVERGENCE"):
            parse_monthly_text(bad_bank)

    def test_series_gap_balance_or_eti_continuity_fails_closed(self):
        records = [parse_monthly_text(JAN), parse_monthly_text(FEB)]
        bad = copy.deepcopy(records)
        bad[1]["opening_balance"] = "0.00"
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SERIES_BALANCE_CONTINUITY"):
            reconcile_series(bad)
        bad = copy.deepcopy(records)
        bad[1]["eti_opening_labeled_total"] = "0.00"
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SERIES_ETI_LABEL_CONTINUITY"):
            reconcile_series(bad)
        bad = [parse_monthly_text(JAN), parse_monthly_text(MAR)]
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SERIES_MONTH_GAP"):
            reconcile_series(bad)

    def test_contract_and_authorization_cannot_enable_financial_promotion(self):
        validate_contract(self.contract)
        validate_runtime_authorization(
            self.authorization,
            batch_id="F02_FUNDEB_MONTHLY_CASH_2026_JAN_MAR",
        )
        for key in (
            "eti_spending_claim_authorized",
            "eti_committed_claim_authorized",
            "eti_liquidated_claim_authorized",
            "eti_paid_claim_authorized",
            "mde_compliance_claim_authorized",
            "annual_compliance_claim_authorized",
        ):
            bad = copy.deepcopy(self.contract)
            bad["semantic_boundary"][key] = True
            with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SEMANTIC_PROMOTION_ENABLED"):
                validate_contract(bad)

    def test_manifest_remote_effect_or_path_traversal_fails_closed(self):
        manifest = {
            "schema":"F02_FUNDEB_MONTHLY_CASH_SOURCE_CUSTODY_V1",
            "mode":"MANUAL_SUPERVISED_INGEST",
            "family":"FUNDEB_MONTHLY_CASH_LOCAL",
            "batch_id":"X",
            "sources":[{
                "source_id":"S1","month":"2026-01","drive_file_id":"D1","file_name":"x.pdf",
                "sha256":"0"*64,"bytes":1,"pages":1,"snapshot_path":"runtime/x.pdf"
            }],
            "remote_effects_authorized":{
                "bronze_write":False,"silver_write":False,"gold_write":False,"serving":False,
                "publication":False,"site":False,"overwrite":False,"delete":False,"move":False,
                "schedule":False,"recurrence":False,
            },
        }
        validate_manifest(manifest)
        bad = copy.deepcopy(manifest)
        bad["remote_effects_authorized"]["gold_write"] = True
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "MANIFEST_REMOTE_EFFECT"):
            validate_manifest(bad)
        bad = copy.deepcopy(manifest)
        bad["sources"][0]["snapshot_path"] = "../escape.pdf"
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SNAPSHOT_PATH_UNSAFE"):
            validate_manifest(bad)

    def test_real_run_shape_with_synthetic_pdf_inspection_and_hash(self):
        payloads = [b"jan", b"feb", b"mar"]
        texts = [JAN, FEB, MAR]
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel = Path(td).relative_to(ROOT)
            sources = []
            text_by_payload = {}
            for idx, (payload, text) in enumerate(zip(payloads, texts), start=1):
                path = Path(td) / f"{idx}.pdf"
                path.write_bytes(payload)
                sources.append({
                    "source_id":f"S{idx}",
                    "month":f"2026-0{idx}",
                    "drive_file_id":f"D{idx}",
                    "file_name":f"{idx}.pdf",
                    "sha256":hashlib.sha256(payload).hexdigest(),
                    "bytes":len(payload),
                    "pages":1,
                    "snapshot_path":str(rel / f"{idx}.pdf"),
                })
                text_by_payload[payload] = text
            manifest = {
                "schema":"F02_FUNDEB_MONTHLY_CASH_SOURCE_CUSTODY_V1",
                "mode":"MANUAL_SUPERVISED_INGEST",
                "family":"FUNDEB_MONTHLY_CASH_LOCAL",
                "batch_id":"F02_FUNDEB_MONTHLY_CASH_2026_JAN_MAR",
                "sources":sources,
                "remote_effects_authorized":{
                    "bronze_write":False,"silver_write":False,"gold_write":False,"serving":False,
                    "publication":False,"site":False,"overwrite":False,"delete":False,"move":False,
                    "schedule":False,"recurrence":False,
                },
            }
            def inspect(payload):
                return {"pages":1,"text_pages":1,"text_chars":len(text_by_payload[payload]),"has_text_layer":True,"text":text_by_payload[payload]}
            with patch("robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash.inspect_f02_pdf", side_effect=inspect):
                result, telemetry = run_monthly_series(
                    self.contract, manifest, root=ROOT, authorization=self.authorization
                )
        self.assertEqual(result["status"], "PASS_F02_FUNDEB_MONTHLY_CASH_OFFLINE_NOT_PERSISTED")
        self.assertEqual(len(result["records"]), 3)
        self.assertEqual(telemetry["remote_effects"], 0)
        self.assertFalse(telemetry["silver_persisted"])
        self.assertFalse(telemetry["gold_authorized"])

    def test_source_hash_drift_fails_before_parse(self):
        payload = b"jan"
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel = Path(td).relative_to(ROOT)
            (Path(td)/"jan.pdf").write_bytes(payload)
            manifest = {
                "schema":"F02_FUNDEB_MONTHLY_CASH_SOURCE_CUSTODY_V1",
                "mode":"MANUAL_SUPERVISED_INGEST",
                "family":"FUNDEB_MONTHLY_CASH_LOCAL",
                "batch_id":"F02_FUNDEB_MONTHLY_CASH_2026_JAN_MAR",
                "sources":[{
                    "source_id":"S1","month":"2026-01","drive_file_id":"D1","file_name":"jan.pdf",
                    "sha256":"0"*64,"bytes":len(payload),"pages":1,"snapshot_path":str(rel/"jan.pdf")
                }],
                "remote_effects_authorized":{
                    "bronze_write":False,"silver_write":False,"gold_write":False,"serving":False,
                    "publication":False,"site":False,"overwrite":False,"delete":False,"move":False,
                    "schedule":False,"recurrence":False,
                },
            }
            with patch("robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash.inspect_f02_pdf", return_value={"pages":1,"text_pages":1,"text_chars":1,"has_text_layer":True,"text":JAN}):
                with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SOURCE_IMMUTABLE_MISMATCH"):
                    run_monthly_series(self.contract, manifest, root=ROOT, authorization=self.authorization)


if __name__ == "__main__":
    unittest.main()
