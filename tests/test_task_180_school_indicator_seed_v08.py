import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.school_indicator_library_seed import (
    load_contract,
    materialize_seed,
    read_wide_fixture,
    school_indicator_values,
    to_long_rows,
    validate_seed,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/school_indicator_library_seed.v1.json"
FIXTURE = ROOT / "docs/evidence/fixtures/TASK_180_CAMADA_V08_ESCOLAS40_2025_SANITIZED.csv"
GENERATED_AT = "2026-09-06T02:55:00Z"
SOFTWARE_VERSION = "0.8.0"


class TestTask180SchoolIndicatorSeedV08(unittest.TestCase):
    def test_contract_pins_exact_v08_and_base_hashes(self):
        obj = load_contract()
        self.assertEqual(
            obj["source"]["sha256"],
            "0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865",
        )
        self.assertEqual(
            obj["source"]["base_canonical_sha256"],
            "4d352dc55537240a4c1ffb3c37337e9c029577ab611f851f2ec925d0178b9eda",
        )
        self.assertEqual(obj["source"]["sheet"], "01 Escolas 40")
        self.assertFalse(obj["source"]["binary_import_complete"])
        self.assertFalse(obj["quality"]["missing_is_zero"])

    def test_fixture_has_40_unique_schools_and_20_metrics(self):
        rows = read_wide_fixture()
        contract = load_contract()
        self.assertEqual(len(rows), 40)
        self.assertEqual(len(contract["metric_map"]), 20)
        codes = [row["codigo_inep"] for row in rows]
        self.assertEqual(len(set(codes)), 40)
        self.assertTrue(all(len(code) == 8 and code.isdigit() for code in codes))

    def test_seed_validation_has_798_non_null_rows_and_two_missing_ideb(self):
        got = validate_seed()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["school_count"], 40)
        self.assertEqual(got["metric_count"], 20)
        self.assertEqual(got["non_null_long_rows"], 798)
        self.assertEqual(got["missing_count"], 2)
        self.assertEqual(
            {(x["codigo_inep"], x["source_column"]) for x in got["missing"]},
            {("35276224", "Ideb_2025"), ("35217864", "Ideb_2025")},
        )

    def test_long_rows_preserve_missing_in_separate_ledger_not_zero(self):
        rows, missing = to_long_rows()
        self.assertEqual(len(rows), 798)
        self.assertEqual(len(missing), 2)
        self.assertFalse(
            any(
                row["indicator_id"] == "IDEB"
                and row["school_code"] in {"35276224", "35217864"}
                for row in rows
            )
        )
        self.assertTrue(all(x["status"] == "MISSING_SOURCE_CELL_NOT_ZERO" for x in missing))

    def test_all_rows_have_pinned_v08_provenance_and_ready_with_caution(self):
        rows, _ = to_long_rows()
        self.assertTrue(
            all(
                row["source_sha256"]
                == "0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865"
                for row in rows
            )
        )
        self.assertTrue(all(row["quality_status"] == "READY_WITH_CAUTION" for row in rows))
        self.assertTrue(
            all(
                row["provenance_ref"].startswith(
                    "FILE_LIBRARY:CAMADA_ANALITICA_V06_40_ESCOLAS_V08.xlsx#01 Escolas 40:"
                )
                for row in rows
            )
        )
        self.assertTrue(all(row["scope_id"] == row["school_code"] for row in rows))

    def test_metric_families_are_task176_compatible(self):
        contract = load_contract()
        allowed = {"CENSO_ESCOLAR", "IDEB", "SAEB", "SARESP", "MUNICIPAL_REPORTS"}
        families = {meta["source_family"] for meta in contract["metric_map"].values()}
        self.assertTrue(families <= allowed)
        self.assertEqual(contract["metric_map"]["INSE_2023"]["source_family"], "SAEB")
        self.assertEqual(contract["metric_map"]["Ideb_2025"]["source_family"], "IDEB")
        self.assertEqual(contract["metric_map"]["part_SARESP_2025"]["source_family"], "SARESP")

    def test_rafael_affonso_leite_seed_values_are_exact(self):
        rows = school_indicator_values("35470600")
        by_id_period = {(row["indicator_id"], row["period"]): row["value"] for row in rows}
        self.assertEqual(len(rows), 20)
        self.assertEqual(by_id_period[("INSE", "2023")], 5.51)
        self.assertEqual(by_id_period[("PPI_SHARE", "2025")], 29.7)
        self.assertEqual(by_id_period[("AFD", "2025")], 86.4)
        self.assertEqual(by_id_period[("ATU", "2025")], 26.3)
        self.assertEqual(by_id_period[("SPECIAL_EDUCATION_ENROLLMENT", "2025")], 43)
        self.assertEqual(by_id_period[("IDEB", "2025")], 7.9)
        self.assertEqual(by_id_period[("IEE", "2025")], 7.74)
        self.assertEqual(by_id_period[("SARESP_PARTICIPATION_RATE", "2025")], 96.1)

    def test_materialized_task176_product_is_deterministic_for_same_generation_metadata(self):
        a = materialize_seed(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        b = materialize_seed(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        self.assertEqual(a["product"]["product_name"], "SCHOOL_INDICATOR_SERIES")
        self.assertEqual(a["product"]["row_count"], 798)
        self.assertEqual(a["product"]["snapshot_id"], b["product"]["snapshot_id"])
        self.assertEqual(a["product"]["content_sha256"], b["product"]["content_sha256"])
        self.assertFalse(a["binary_import_complete"])
        self.assertFalse(a["source_layers_replaced"])

    def test_fixture_header_matches_contract_exactly(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        with FIXTURE.open("r", encoding="utf-8-sig") as handle:
            header = handle.readline().strip()
        columns = header.split(",")
        self.assertEqual(columns[0:2], ["codigo_inep", "unidade"])
        self.assertEqual(set(columns[2:]), set(contract["metric_map"]))
        self.assertEqual(len(columns[2:]), 20)


if __name__ == "__main__":
    unittest.main()
