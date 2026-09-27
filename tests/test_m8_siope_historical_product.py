import unittest

from robo_dados_publicos.product.siope_historical import (
    EXPECTED_METRIC_IDS,
    SiopeHistoricalProductError,
    build_siope_historical_answers,
    validate_gold_series,
)


class TestM8SiopeHistoricalProduct(unittest.TestCase):
    def gold(self, year, **overrides):
        metrics = {
            metric_id: (f"{year % 100}.{index:04d}" if metric_id.endswith("_pct") else f"{year}.{index:02d}")
            for index, metric_id in enumerate(reversed(EXPECTED_METRIC_IDS), start=1)
        }
        payload = {
            "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
            "identity": {
                "municipality_code": 352690,
                "municipality_name": "Limeira",
                "period": 1 if year == 2016 else 6,
                "resource": "Dados_Gerais_Siope",
                "state": "SP",
                "year": year,
            },
            "metrics": metrics,
            "provenance": {
                "record_sha256": f"{year:064x}",
                "silver_payload_sha256": f"{year + 1:064x}",
                "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
            },
            "semantic_scope": {
                "fiscal_audit_conclusion": False,
                "fundeb_compliance_conclusion": False,
                "imputation_performed": False,
                "mde_compliance_conclusion": False,
            },
            "software_version": "0.8.0",
        }
        for key, value in overrides.items():
            if key in {"identity", "metrics", "provenance", "semantic_scope"}:
                payload[key] = value
            else:
                payload[key] = value
        return payload

    def series(self):
        return [self.gold(year) for year in range(2024, 2015, -1)]

    def test_accepts_complete_series_and_normalizes_year_order(self):
        rows = validate_gold_series(self.series())
        self.assertEqual(tuple(range(2016, 2025)), tuple(row["year"] for row in rows))
        self.assertEqual(1, rows[0]["period"])
        self.assertTrue(all(row["period"] == 6 for row in rows[1:]))

    def test_builds_exactly_eight_answer_contract_rows(self):
        answers = build_siope_historical_answers(self.series())
        self.assertEqual(8, len(answers))
        self.assertTrue(all(answer.status == "ANSWERED" for answer in answers))
        self.assertTrue(all(len(answer.fontes) == 9 for answer in answers))
        self.assertIn("2016:", answers[0].dado)
        self.assertIn("2024:", answers[0].dado)
        self.assertIn("não constitui auditoria fiscal", answers[0].cautela)

    def test_rejects_missing_year(self):
        with self.assertRaisesRegex(SiopeHistoricalProductError, "COVERAGE_YEARS"):
            validate_gold_series(self.series()[:-1])

    def test_rejects_duplicate_year(self):
        payloads = self.series()
        payloads[-1] = self.gold(2017)
        with self.assertRaisesRegex(SiopeHistoricalProductError, "DUPLICATE_YEAR"):
            validate_gold_series(payloads)

    def test_rejects_wrong_2016_period(self):
        payloads = self.series()
        payloads[-1]["identity"]["period"] = 6
        with self.assertRaisesRegex(SiopeHistoricalProductError, "PERIOD_2016"):
            validate_gold_series(payloads)

    def test_rejects_metric_drift(self):
        payloads = self.series()
        payloads[0]["metrics"].pop(EXPECTED_METRIC_IDS[0])
        payloads[0]["metrics"]["invented_metric"] = "1"
        with self.assertRaisesRegex(SiopeHistoricalProductError, "METRIC_IDS"):
            validate_gold_series(payloads)

    def test_rejects_automatic_compliance_claim(self):
        payloads = self.series()
        payloads[0]["semantic_scope"]["mde_compliance_conclusion"] = True
        with self.assertRaisesRegex(SiopeHistoricalProductError, "MDE_COMPLIANCE_CONCLUSION"):
            validate_gold_series(payloads)

    def test_rejects_wrong_source_provenance(self):
        payloads = self.series()
        payloads[0]["provenance"]["source_id"] = "OTHER_SOURCE"
        with self.assertRaisesRegex(SiopeHistoricalProductError, "PROVENANCE_SOURCE"):
            validate_gold_series(payloads)


if __name__ == "__main__":
    unittest.main()
