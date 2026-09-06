import unittest

from robo_dados_publicos.analytics.v08_censo_panel import (
    aggregate_long_rows,
    full_panel_to_long_rows,
    load_contract,
    materialize_aggregate,
    validate_aggregate,
    validate_full_panel_rows,
)


GENERATED_AT = "2026-09-06T03:08:00Z"
SOFTWARE_VERSION = "0.8.0"


def synthetic_full_panel():
    c = load_contract()
    header = c["full_panel"]["header"]
    rows = []
    codes = [f"35{i:06d}" for i in range(1, 70)]
    for year in c["full_panel"]["years"]:
        for idx, code in enumerate(codes):
            group = "ANOS_INICIAIS" if idx < 40 else "EDUCACAO_INFANTIL"
            row = {key: "0" for key in header}
            row.update({
                "ano": str(year),
                "codigo_inep": code,
                "unidade": f"UNIDADE {idx+1}",
                "grupo_v06": group,
                "primeiro_ano_mesmo_codigo": "2007",
                "status": "VALOR" if year >= 2020 else "OBSERVADO",
                "mat_bas": str(100 + idx),
                "mat_esp": str(idx % 12),
                "sala_aee": str(idx % 2),
                "banheiro_acessivel": str((idx + 1) % 2),
                "salas_utilizadas_acessiveis": str(idx % 4),
                "banda_larga": "1",
                "internet": "1",
                "internet_alunos": str(idx % 2),
                "tp_aee": str(idx % 2),
                "acessibilidade_recursos_8": str(idx % 6),
                "corrimao": str(idx % 2),
                "elevador": "0",
                "pisos_tateis": str(idx % 2),
                "vao_livre": "1",
                "rampas": str(idx % 2),
                "sinal_sonoro": "0",
                "sinal_tatil": "0",
                "sinal_visual": str(idx % 2),
                "arquivo_fonte": f"microdados_censo_escolar_{year}.zip",
            })
            rows.append(row)
    return rows


class TestTask182V08CensoPanel(unittest.TestCase):
    def test_contract_pins_exact_source_and_panel_shape(self):
        c = load_contract()
        self.assertEqual(
            c["source"]["sha256"],
            "0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865",
        )
        self.assertEqual(
            c["source"]["panel_csv_sha256"],
            "b8edac61a559b0e745d09cdd9e66f8ffee0090552526386dd2bc77987fc293e4",
        )
        self.assertEqual(c["full_panel"]["expected_rows"], 552)
        self.assertEqual(c["full_panel"]["expected_columns"], 25)
        self.assertEqual(len(c["full_panel"]["header"]), 25)
        self.assertFalse(c["full_panel"]["runtime_row_transfer_complete"])

    def test_aggregate_seed_is_48_non_null_rows(self):
        got = validate_aggregate()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["row_count"], 48)
        self.assertEqual(got["year_count"], 8)
        self.assertEqual(got["metric_count"], 6)

    def test_aggregate_2025_values_are_exact(self):
        rows = aggregate_long_rows()
        y2025 = [x for x in rows if x["period"] == "2025"]
        self.assertEqual(len(y2025), 6)
        lookup = {(x["scope_id"], x["indicator_id"]): x["value"] for x in y2025}
        self.assertEqual(
            lookup[("LIMEIRA_AI40_STABLE_PANEL", "SPECIAL_EDUCATION_ENROLLMENT")],
            901,
        )
        self.assertEqual(
            lookup[("LIMEIRA_EI_CURRENT_UNITS_OBSERVED_YEARLY", "SPECIAL_EDUCATION_ENROLLMENT")],
            227,
        )
        self.assertEqual(
            lookup[("LIMEIRA_AI40_STABLE_PANEL", "AEE_ROOM_AVAILABILITY_RATE")],
            92.5,
        )
        self.assertEqual(
            lookup[("LIMEIRA_EI_CURRENT_UNITS_OBSERVED_YEARLY", "AEE_ROOM_AVAILABILITY_RATE")],
            55.172413793103445,
        )
        self.assertEqual(
            lookup[("LIMEIRA_AI40_STABLE_PANEL", "ACCESSIBLE_BATHROOM_RATE")],
            77.5,
        )
        self.assertEqual(
            lookup[("LIMEIRA_EI_CURRENT_UNITS_OBSERVED_YEARLY", "BROADBAND_AVAILABILITY_RATE")],
            96.55172413793103,
        )

    def test_aggregate_product_materializes_deterministically(self):
        a = materialize_aggregate(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        b = materialize_aggregate(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        self.assertEqual(a["product"]["row_count"], 48)
        self.assertEqual(a["product"]["snapshot_id"], b["product"]["snapshot_id"])
        self.assertFalse(a["full_panel_materialized"])
        self.assertFalse(a["full_panel_row_transfer_complete"])

    def test_full_panel_validator_accepts_exact_552x25_shape(self):
        rows = synthetic_full_panel()
        got = validate_full_panel_rows(rows)
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["row_count"], 552)
        self.assertEqual(got["year_count"], 8)
        self.assertEqual(got["units_2025"], 69)
        self.assertEqual(got["ai_2025"], 40)
        self.assertEqual(got["ei_2025"], 29)

    def test_full_panel_validator_fails_on_partial_snippet(self):
        rows = synthetic_full_panel()[:100]
        with self.assertRaisesRegex(Exception, "TASK182_PANEL_ROW_COUNT"):
            validate_full_panel_rows(rows)

    def test_full_panel_adapter_preserves_source_status_and_zero(self):
        rows = synthetic_full_panel()
        long_rows, missing = full_panel_to_long_rows(rows)
        self.assertEqual(len(long_rows), 552 * 18)
        self.assertEqual(missing, [])
        first = long_rows[0]
        self.assertIn(first["source_record_status"], {"OBSERVADO", "VALOR"})
        self.assertEqual(first["source_family"], "CENSO_ESCOLAR")
        self.assertEqual(
            first["source_sha256"],
            "0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865",
        )
        self.assertTrue(any(x["value"] == 0 for x in long_rows))
        self.assertTrue(all("source_file_declared" in x for x in long_rows))

    def test_cadastral_caution_is_present_on_every_aggregate_row(self):
        rows = aggregate_long_rows()
        self.assertTrue(
            all("CADASTRAL_PRESENCE_NE_QUALITY" in x["caution"] for x in rows)
        )


if __name__ == "__main__":
    unittest.main()
