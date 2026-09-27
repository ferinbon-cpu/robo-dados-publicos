import json
from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.manual_ingest.mde_fundeb import F02IngestStop, F02SourceContract
from robo_dados_publicos.manual_ingest.mde_fundeb_local_monitoring import (
    load_f02_local_monitoring_plan,
    normalize_f02_local_monitoring_document,
    parse_fundeb_local_monitoring,
    reconcile_f02_local_monitoring,
)
from robo_dados_publicos.manual_ingest.mde_fundeb_parser import parse_mde_25_local


FUNDEB_TEXT = """
Prefeitura Municipal de Limeira
APLICACAO COM RECURSOS DO FUNDEB
22/06/2026 POSICAO EM 31/05/2026 Pagina 1
RECEITA DO FUNDEB RETENCOES AO FUNDEB
Principal (I) 193.564.450,07 81.329.560,61 151.546.735,85 69.018.540,87
TOTAL (I+II+III+IV+V+VI+VII+VIII+IX+X) 202.418.930,44 85.705.568,77 81.329.560,61 69.018.540,87
PROFISSIONAIS DA EDUCACAO BASICA
DESPESAS LIQUIDAS
TOTAL ** 135.614.525,38 158,23 83.352.004,79 97,25 64.033.238,78 74,71
PROFISSIONAIS DA EDUCACAO BASICA* - exceto Complementacao da Uniao VAAR 135.390.547,29 157,97 83.128.026,70 96,99 63.809.260,69 74,45
"""

MDE25_TEXT = """
Prefeitura Municipal de Limeira
APLICACAO DOS RECURSOS PROPRIOS EM ENSINO - POR DATA
23/06/2026 POSICAO EM 31/05/2026 Pagina 1
RECEITA DE IMPOSTOS APLICACAO MINIMA CONSTITUCIONAL
Total 1.389.542.306,44 586.706.702,84
Retencoes ao FUNDEB 151.546.735,85 69.018.540,87
DESPESAS PROPRIAS EM EDUCACAO
DESPESAS TOTAIS
TOTAL * 207.464.562,74 35,36 138.465.313,16 23,60 126.809.299,88 21,61
DESPESAS LIQUIDAS
TOTAL 207.244.381,02 35,32 138.245.131,44 23,56 121.603.816,07 20,73
"""


def contract(family):
    return F02SourceContract(
        source_id="TEST_" + family,
        family=family,
        role="TEST",
        drive_file_id="drive-" + family,
        expected_sha256="0" * 64,
        expected_bytes=1,
        expected_pages=1,
    )


def base_config():
    return {
        "batch": "F02_LOCAL_MONITORING_2026_JAN_MAY",
        "contract": "F02_LOCAL_MONITORING_PERIOD_WITHOUT_RREO_V1",
        "mode": "MANUAL_SUPERVISED_INGEST",
        "official_period_context": {
            "annual_compliance_claim_authorized": False,
            "official_mde_claim_authorized": False,
            "reason": "NO_RREO_BIMONTHLY_MAY_PERIOD",
            "rreo_mde_same_period_available": False,
        },
        "promotion": {
            "bronze_mutation_authorized_by_this_contract": False,
            "gold_authorized": False,
            "serving_authorized": False,
            "silver_authorized_by_this_contract": False,
            "site_mutation_authorized": False,
        },
        "reference_period": {
            "closing_status": "PARTIAL_LOCAL_MONITORING",
            "end": "2026-05-31",
            "start": "2026-01-01",
        },
        "source_precedence": {
            "fundeb_local_report": "LOCAL_MONITORING_PRIMARY_FOR_THIS_LOCAL_ONLY_BATCH",
            "mde_25_local_report": "LOCAL_MONITORING_AUXILIARY_NOT_OFFICIAL_RREO_SUBSTITUTE",
            "mde_official_claim": "NOT_AUTHORIZED_NO_RREO_SAME_PERIOD",
        },
        "sources": [
            {
                "drive_file_id": "d1",
                "expected_bytes": 1,
                "expected_pages": 1,
                "expected_sha256": "1" * 64,
                "family": "FUNDEB_LOCAL",
                "role": "TEST",
                "source_id": "F",
            },
            {
                "drive_file_id": "d2",
                "expected_bytes": 1,
                "expected_pages": 1,
                "expected_sha256": "2" * 64,
                "family": "MDE_25_LOCAL",
                "role": "TEST",
                "source_id": "M",
            },
        ],
    }


class F02LocalMonitoringTests(unittest.TestCase):
    def write_config(self, config):
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
        try:
            json.dump(config, handle)
            return Path(handle.name)
        finally:
            handle.close()

    def test_plan_accepts_exact_local_only_contract(self):
        path = self.write_config(base_config())
        try:
            plan = load_f02_local_monitoring_plan(path)
            self.assertEqual(2, len(plan["contracts"]))
        finally:
            path.unlink(missing_ok=True)

    def test_plan_rejects_official_claim_authorization(self):
        config = base_config()
        config["official_period_context"]["official_mde_claim_authorized"] = True
        path = self.write_config(config)
        try:
            with self.assertRaisesRegex(F02IngestStop, "OFFICIAL_CONTEXT_MISMATCH"):
                load_f02_local_monitoring_plan(path)
        finally:
            path.unlink(missing_ok=True)

    def test_plan_rejects_promotion(self):
        config = base_config()
        config["promotion"]["silver_authorized_by_this_contract"] = True
        path = self.write_config(config)
        try:
            with self.assertRaisesRegex(F02IngestStop, "UNAUTHORIZED_PROMOTION"):
                load_f02_local_monitoring_plan(path)
        finally:
            path.unlink(missing_ok=True)

    def test_plan_rejects_rreo_or_third_source(self):
        config = base_config()
        config["sources"].append({
            "drive_file_id": "d3",
            "expected_bytes": 1,
            "expected_pages": 1,
            "expected_sha256": "3" * 64,
            "family": "RREO_MDE",
            "role": "TEST",
            "source_id": "R",
        })
        path = self.write_config(config)
        try:
            with self.assertRaisesRegex(F02IngestStop, "EXACTLY_TWO_SOURCES_REQUIRED"):
                load_f02_local_monitoring_plan(path)
        finally:
            path.unlink(missing_ok=True)

    def test_fundeb_may_parser(self):
        record = parse_fundeb_local_monitoring(FUNDEB_TEXT)
        self.assertEqual("2026-05-31", record["period_end"])
        self.assertEqual("85705568.77", record["metrics"]["fundeb_total_received"])
        self.assertEqual("83128026.70", record["metrics"]["fundeb_professionals_liquidated"])
        self.assertEqual("96.99", record["metrics"]["fundeb_professionals_liquidated_percent_local"])

    def test_mde25_may_existing_parser(self):
        record = parse_mde_25_local(MDE25_TEXT)
        self.assertEqual("2026-05-31", record["period_end"])
        self.assertEqual("586706702.84", record["metrics"]["tax_revenue_realized"])
        self.assertEqual("138465313.16", record["metrics"]["education_expense_liquidated"])
        self.assertEqual("23.60", record["metrics"]["education_expense_liquidated_percent"])

    def test_reconciliation_local_only_passes_and_forbids_official_claim(self):
        records = [parse_fundeb_local_monitoring(FUNDEB_TEXT), parse_mde_25_local(MDE25_TEXT)]
        result = reconcile_f02_local_monitoring(records)
        self.assertEqual("PASS_F02_LOCAL_MONITORING_RECONCILIATION_NO_RREO_PERIOD_MATCH", result["status"])
        self.assertTrue(result["exact_checks"]["fundeb_retained_local_reports"])
        self.assertFalse(result["authority_policy"]["official_mde_claim_authorized"])
        self.assertFalse(result["authority_policy"]["annual_compliance_claim_authorized"])
        self.assertEqual("LOCAL_MONITORING_ONLY_NOT_OFFICIAL_MDE_SUBSTITUTION", result["authority_policy"]["interpretation"])

    def test_reconciliation_retention_mismatch_stops(self):
        records = [parse_fundeb_local_monitoring(FUNDEB_TEXT), parse_mde_25_local(MDE25_TEXT)]
        records[1]["metrics"]["fundeb_retained"] = "1.00"
        with self.assertRaisesRegex(F02IngestStop, "RETENTION_MISMATCH"):
            reconcile_f02_local_monitoring(records)

    def test_reconciliation_period_mismatch_stops(self):
        records = [parse_fundeb_local_monitoring(FUNDEB_TEXT), parse_mde_25_local(MDE25_TEXT)]
        records[1]["period_end"] = "2026-04-30"
        with self.assertRaisesRegex(F02IngestStop, "PERIOD_MISMATCH"):
            reconcile_f02_local_monitoring(records)

    def test_normalizer_contract_family_mismatch_stops(self):
        with self.assertRaisesRegex(F02IngestStop, "CONTRACT_MISMATCH"):
            normalize_f02_local_monitoring_document(contract("MDE_25_LOCAL"), FUNDEB_TEXT)


if __name__ == "__main__":
    unittest.main()
