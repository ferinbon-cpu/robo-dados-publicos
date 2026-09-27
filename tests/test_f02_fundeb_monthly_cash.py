from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from robo_dados_publicos.manual_ingest.mde_fundeb import inspect_f02_pdf
from robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash import (
    F02FundebMonthlyCashStop,
    parse_monthly_text,
    _is_structurally_blank_export_page,
    inspect_monthly_pdf,
    load_manifest,
    load_pinned_authorization,
    reconcile_series,
    run_monthly_series,
    validate_contract,
    validate_manifest,
    validate_offline_telemetry,
    validate_runtime_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/f02_fundeb_monthly_cash_series.v1.json"
def synthetic_authorization():
    return {
        "schema":"F02_FUNDEB_MONTHLY_CASH_RUNTIME_AUTHORIZATION_V1",
        "authorization_id":"TEST_AUTH",
        "scope":"F02_FUNDEB_MONTHLY_CASH_LOCAL_SNAPSHOT_READ",
        "batch_id":"F02_FUNDEB_MONTHLY_CASH_2026_JAN_MAR",
        "authorized":True,
        "owner_instruction_verbatim":"synthetic unit-test authorization",
        "allowed_effects":["LOCAL_SNAPSHOT_READ","OFFLINE_PARSE","OFFLINE_RECONCILIATION"],
        "forbidden_effects":[
            "DELETE","OVERWRITE","SERVING","LOOKER","PUBLICATION","SITE",
            "SCHEDULE","RECURRENCE","GOLD_PROMOTION",
            "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
        ],
        "status":"TEST_ONLY",
    }


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


def synthetic_pdf_bytes(page_streams):
    import io
    writer = PdfWriter()
    for stream_bytes in page_streams:
        page = writer.add_blank_page(width=200, height=200)
        if stream_bytes is None:
            continue
        stream = DecodedStreamObject()
        stream.set_data(stream_bytes)
        page[NameObject("/Contents")] = writer._add_object(stream)
        if b"BT" in stream_bytes:
            font = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })
            fonts = DictionaryObject({NameObject("/F1"): writer._add_object(font)})
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): fonts,
            })
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


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
        self.authorization = synthetic_authorization()

    def test_exact_monthly_values_and_semantic_boundary(self):
        jan = parse_monthly_text(JAN)
        feb = parse_monthly_text(FEB)
        mar = parse_monthly_text(MAR)
        self.assertEqual(jan["period"], "2026-01")
        self.assertEqual(feb["period"], "2026-02")
        self.assertEqual(mar["period"], "2026-03")  # MARÇO is folded to MARCO
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

    def test_structurally_blank_export_page_policy_is_narrow(self):
        class PageWithImage:
            images = [object()]
            def extract_text(self):
                return ""
            def get_contents(self):
                return None

        self.assertFalse(
            _is_structurally_blank_export_page(PageWithImage(), reader=object())
        )

        class PageImageInspectionFailure:
            def extract_text(self):
                return ""
            @property
            def images(self):
                raise RuntimeError("image inspection failed")
            def get_contents(self):
                return None

        with self.assertRaisesRegex(
            F02FundebMonthlyCashStop, "BLANK_PAGE_IMAGE_INSPECTION_FAILED"
        ):
            _is_structurally_blank_export_page(
                PageImageInspectionFailure(), reader=object()
            )

        class FakeContents:
            def get_data(self):
                return b"q Q"

        class PageContentStreamInspectionFailure:
            images = []
            def extract_text(self):
                return ""
            def get_contents(self):
                return FakeContents()

        with patch(
            "robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash.ContentStream",
            side_effect=RuntimeError("content stream inspection failed"),
        ):
            with self.assertRaisesRegex(
                F02FundebMonthlyCashStop,
                "BLANK_PAGE_CONTENT_STREAM_INSPECTION_FAILED",
            ):
                _is_structurally_blank_export_page(
                    PageContentStreamInspectionFailure(), reader=object()
                )

        empty_pdf = synthetic_pdf_bytes([None])
        reader = PdfReader(__import__("io").BytesIO(empty_pdf))
        self.assertTrue(
            _is_structurally_blank_export_page(reader.pages[0], reader=reader)
        )

        ctm_pdf = synthetic_pdf_bytes([
            b"0.750000 0.000000 0.000000 -0.750000 0.000000 841.920044 cm\n"
        ])
        reader = PdfReader(__import__("io").BytesIO(ctm_pdf))
        self.assertTrue(
            _is_structurally_blank_export_page(reader.pages[0], reader=reader)
        )

        vector_pdf = synthetic_pdf_bytes([b"0 0 m 10 10 l S\n"])
        reader = PdfReader(__import__("io").BytesIO(vector_pdf))
        self.assertFalse(
            _is_structurally_blank_export_page(reader.pages[0], reader=reader)
        )

        double_ctm_pdf = synthetic_pdf_bytes([
            b"1 0 0 1 0 0 cm\n1 0 0 1 0 0 cm\n"
        ])
        reader = PdfReader(__import__("io").BytesIO(double_ctm_pdf))
        self.assertFalse(
            _is_structurally_blank_export_page(reader.pages[0], reader=reader)
        )

    def test_monthly_pdf_real_parser_allows_only_trailing_structural_blank(self):
        text_stream = b"BT /F1 12 Tf 10 100 Td (HELLO) Tj ET\n"
        ctm_stream = b"0.750000 0.000000 0.000000 -0.750000 0.000000 841.920044 cm\n"

        trailing = inspect_monthly_pdf(
            synthetic_pdf_bytes([text_stream, ctm_stream])
        )
        self.assertTrue(trailing["has_required_text_layer"])
        self.assertEqual(trailing["structurally_blank_trailing_pages"], [2])

        internal = inspect_monthly_pdf(
            synthetic_pdf_bytes([text_stream, None, text_stream])
        )
        self.assertFalse(internal["has_required_text_layer"])

        vector = inspect_monthly_pdf(
            synthetic_pdf_bytes([text_stream, b"0 0 m 10 10 l S\n"])
        )
        self.assertFalse(vector["has_required_text_layer"])

    def test_contract_rejects_blank_page_policy_drift(self):
        good = copy.deepcopy(self.contract)
        validate_contract(good)
        bad = copy.deepcopy(good)
        bad["source_page_policy"]["allow_internal_blank_pages"] = True
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SOURCE_PAGE_POLICY"):
            validate_contract(bad)
        missing = copy.deepcopy(good)
        del missing["source_page_policy"]
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "SOURCE_PAGE_POLICY"):
            validate_contract(missing)

    def test_pdf_inspection_is_local_only_even_with_socket_blocked(self):
        import io
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        buf = io.BytesIO()
        writer.write(buf)
        with patch("socket.socket", side_effect=AssertionError("network access attempted")):
            observed = inspect_f02_pdf(buf.getvalue())
        self.assertEqual(observed["pages"], 1)
        self.assertFalse(observed["has_text_layer"])

    def test_missing_document_marker_invalid_manifest_json_and_bad_auth_pin_stop(self):
        with self.assertRaisesRegex(F02FundebMonthlyCashStop, "DOCUMENT_SIGNATURE"):
            parse_monthly_text("Prefeitura Municipal de Limeira")

        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel = Path(td).relative_to(ROOT)
            bad_manifest = Path(td) / "bad.json"
            bad_manifest.write_text("{not-json", encoding="utf-8")
            with self.assertRaisesRegex(F02FundebMonthlyCashStop, "MANIFEST_INVALID_JSON"):
                load_manifest(root=ROOT, relative_path=rel / "bad.json")

            auth_path = Path(td) / "auth.json"
            auth_path.write_text(json.dumps(self.authorization), encoding="utf-8")
            with self.assertRaisesRegex(F02FundebMonthlyCashStop, "AUTHORIZATION_PIN"):
                load_pinned_authorization(
                    root=ROOT,
                    relative_path=rel / "auth.json",
                    expected_sha256="not-a-sha",
                )
            with self.assertRaisesRegex(F02FundebMonthlyCashStop, "AUTHORIZATION_SHA_DRIFT"):
                load_pinned_authorization(
                    root=ROOT,
                    relative_path=rel / "auth.json",
                    expected_sha256="0" * 64,
                )

    def test_unexpected_telemetry_fails_closed(self):
        good = {
            "remote_effects":0,
            "silver_persisted":False,
            "gold_authorized":False,
        }
        validate_offline_telemetry(good)
        for key, value in (
            ("remote_effects", 1),
            ("silver_persisted", True),
            ("gold_authorized", True),
        ):
            bad = dict(good)
            bad[key] = value
            with self.assertRaises(F02FundebMonthlyCashStop):
                validate_offline_telemetry(bad)

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
