import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.product.siope_historical import EXPECTED_METRIC_IDS
from robo_dados_publicos.product.siope_historical_drive_readonly import (
    GOLD_FOLDER_ID,
    SOURCE_ID,
    SiopeHistoricalDriveReadonlyError,
    describe_gate,
    run_readonly_gate,
)


ROOT = Path(__file__).resolve().parents[1]


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def valid_payload(year: int) -> dict:
    period = 1 if year == 2016 else 6
    return {
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "identity": {
            "municipality_code": 352690,
            "municipality_name": "Limeira",
            "period": period,
            "resource": "Dados_Gerais_Siope",
            "state": "SP",
            "year": year,
        },
        "input_facts": {},
        "metrics": {metric_id: f"{year}.{index:04d}" for index, metric_id in enumerate(EXPECTED_METRIC_IDS, 1)},
        "provenance": {
            "record_sha256": f"{year:064x}",
            "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1",
            "silver_payload_sha256": f"{year + 1:064x}",
            "source_id": SOURCE_ID,
        },
        "semantic_scope": {
            "fiscal_audit_conclusion": False,
            "fundeb_compliance_conclusion": False,
            "imputation_performed": False,
            "kind": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
            "mde_compliance_conclusion": False,
        },
        "software_version": "0.8.0",
    }


def fixture_specs_and_files():
    specs = []
    files = {}
    for year in range(2016, 2025):
        period = 1 if year == 2016 else 6
        raw = canonical(valid_payload(year))
        sha256 = hashlib.sha256(raw).hexdigest()
        name = (
            f"{SOURCE_ID}__Dados_Gerais_Siope__Limeira_SP__{year}_P{period}__352690__"
            f"{sha256[:12]}__gold_v1.json"
        )
        file_id = f"id-{year}"
        specs.append({"year": year, "period": period, "bytes": len(raw), "sha256": sha256, "name": name})
        files[name] = {
            "metadata": {
                "id": file_id,
                "name": name,
                "mimeType": "application/json",
                "size": str(len(raw)),
                "parents": [GOLD_FOLDER_ID],
            },
            "raw": raw,
        }
    return tuple(specs), files


class FakeDrive:
    def __init__(self, files, *, duplicate_name=None, missing_name=None, corrupt_id=None):
        self.files = files
        self.duplicate_name = duplicate_name
        self.missing_name = missing_name
        self.corrupt_id = corrupt_id
        self.lookup_count = 0
        self.download_count = 0

    def find_by_name(self, folder_id, name):
        self.lookup_count += 1
        if folder_id != GOLD_FOLDER_ID or name == self.missing_name:
            return []
        item = self.files[name]
        rows = [dict(item["metadata"])]
        if name == self.duplicate_name:
            rows.append(dict(item["metadata"], id=item["metadata"]["id"] + "-duplicate"))
        return rows

    def get(self, file_id, destination):
        self.download_count += 1
        for item in self.files.values():
            if item["metadata"]["id"] == file_id:
                raw = item["raw"] + (b"x" if file_id == self.corrupt_id else b"")
                Path(destination).write_bytes(raw)
                return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        raise AssertionError(f"unknown file id {file_id}")


class TestM8SiopeHistoricalProductReadonlyGate(unittest.TestCase):
    def setUp(self):
        self.specs, self.files = fixture_specs_and_files()

    def test_design_is_readonly_and_bounded_to_nine_existing_gold_objects(self):
        design = describe_gate(root=ROOT, specs=self.specs)
        self.assertEqual(9, design["year_count"])
        self.assertEqual(9, design["drive_lookup_count"])
        self.assertEqual(9, design["drive_download_count"])
        self.assertEqual(0, design["drive_write_count"])
        self.assertEqual(0, design["source_get_count"])
        self.assertFalse(design["publication_authorized"])
        self.assertFalse(design["future_batch_execution_authorized"])

    def test_live_readonly_builds_local_product_bundle(self):
        drive = FakeDrive(self.files)
        with tempfile.TemporaryDirectory() as td:
            result = run_readonly_gate(
                root=ROOT,
                output_dir=td,
                generated_at="2026-08-27T23:59:00+00:00",
                drive=drive,
                specs=self.specs,
            )
            self.assertEqual("PASS_M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY", result["status"])
            self.assertEqual(9, drive.lookup_count)
            self.assertEqual(9, drive.download_count)
            self.assertEqual(0, result["drive_write_count"])
            self.assertEqual(8, result["metric_row_count"])
            self.assertEqual(72, result["gold_metric_observations"])
            self.assertEqual("LOCAL_ONLY_NOT_PUBLISHED", result["publication_status"])
            self.assertFalse(result["publication_authorized"])
            self.assertFalse(result["remote_file_id_persisted"])
            self.assertNotIn("id-", json.dumps(result))
            for name in (
                "report.json",
                "report_card.json",
                "table.csv",
                "report.md",
                "report.html",
                "report.pdf",
                "manifest.json",
            ):
                self.assertTrue((Path(td) / name).is_file(), name)

    def test_missing_remote_name_stops_before_first_download(self):
        drive = FakeDrive(self.files, missing_name=self.specs[4]["name"])
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(SiopeHistoricalDriveReadonlyError, "REMOTE_NAME_MATCH_COUNT_2020"):
                run_readonly_gate(
                    root=ROOT,
                    output_dir=td,
                    generated_at="2026-08-27T23:59:00+00:00",
                    drive=drive,
                    specs=self.specs,
                )
        self.assertEqual(0, drive.download_count)

    def test_duplicate_remote_name_stops_before_first_download(self):
        drive = FakeDrive(self.files, duplicate_name=self.specs[2]["name"])
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(SiopeHistoricalDriveReadonlyError, "REMOTE_NAME_MATCH_COUNT_2018"):
                run_readonly_gate(
                    root=ROOT,
                    output_dir=td,
                    generated_at="2026-08-27T23:59:00+00:00",
                    drive=drive,
                    specs=self.specs,
                )
        self.assertEqual(0, drive.download_count)

    def test_metadata_size_drift_stops_before_first_download(self):
        bad = {name: {"metadata": dict(item["metadata"]), "raw": item["raw"]} for name, item in self.files.items()}
        bad[self.specs[0]["name"]]["metadata"]["size"] = "1"
        drive = FakeDrive(bad)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(SiopeHistoricalDriveReadonlyError, "REMOTE_SIZE_2016"):
                run_readonly_gate(
                    root=ROOT,
                    output_dir=td,
                    generated_at="2026-08-27T23:59:00+00:00",
                    drive=drive,
                    specs=self.specs,
                )
        self.assertEqual(0, drive.download_count)

    def test_hash_drift_stops(self):
        drive = FakeDrive(self.files, corrupt_id=self.files[self.specs[8]["name"]]["metadata"]["id"])
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(SiopeHistoricalDriveReadonlyError, "DOWNLOADED_BYTES_2024|DOWNLOADED_SHA_2024"):
                run_readonly_gate(
                    root=ROOT,
                    output_dir=td,
                    generated_at="2026-08-27T23:59:00+00:00",
                    drive=drive,
                    specs=self.specs,
                )
        self.assertEqual(9, drive.download_count)


if __name__ == "__main__":
    unittest.main()
