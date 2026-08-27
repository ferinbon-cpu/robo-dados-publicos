from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.sources.siope_client_limeira_historical_bounded_batch_authorization import (
    HistoricalBoundedBatchAuthorizationError,
    run_bounded_batch,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/source_expansion.siope_client_limeira_historical_bounded_batch_authorization.json"
SCRIPT_PATH = ROOT / "scripts/github_siope_client_limeira_historical_bounded_batch_authorization_gate.py"


def config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def record(year: int):
    item = {field: 0 for field in PROVEN_DADOS_GERAIS_FIELDS}
    item.update({
        "COD_MUNI": 352690, "NOM_MUNI": "Limeira", "SIG_UF": "SP", "NUM_ANO": year, "NUM_PERI": 6,
        "VAL_RECE_PREV_ATUA": "1000", "VAL_RECE_REAL": "900", "VAL_DESP_DOTA_ATUA": "800",
        "VAL_DESP_EMPE": "700", "VAL_DESP_LIQU": "650", "VAL_DESP_PAGA": "600",
        "VL_DESP_DOTA_ATUA_EDU": "300", "VL_DESP_EMPE_EDU": "200", "VL_DESP_LIQU_EDU": "190",
        "VL_DESP_PAGA_EDU": "180", "NUM_POPU": "100",
    })
    return item


class FakeSiope:
    def __init__(self, bad_year=None):
        self.calls = []
        self.bad_year = bad_year

    def get_dados_gerais_page(self, **kwargs):
        self.calls.append(kwargs)
        year = kwargs["ano"]
        actual_year = 1999 if year == self.bad_year else year
        item = record(actual_year)
        raw = json.dumps({"value": [item]}, sort_keys=True).encode()
        return SimpleNamespace(
            records=[item], status=200, content_type="application/json",
            response_byte_count=len(raw), odata_context_present=True, nextlink_present=False, request_count=1,
            response_sha256=hashlib.sha256(raw).hexdigest(),
        )


class FakeDrive:
    def __init__(self, collision_token=None):
        self.collision_token = collision_token
        self.puts = []
        self.downloads = []
        self.files = {}

    def find_by_name(self, parent_id, name):
        if self.collision_token and self.collision_token in name:
            return [{"id": "existing", "name": name}]
        return []

    def put(self, local_path, remote_name, parent_id, mime_type):
        raw = Path(local_path).read_bytes()
        file_id = f"id-{len(self.files)+1}"
        self.files[file_id] = raw
        self.puts.append((parent_id, remote_name))
        return {
            "id": file_id, "name": remote_name, "mimeType": mime_type, "size": str(len(raw)),
            "md5Checksum": hashlib.md5(raw).hexdigest(), "parents": [parent_id],  # noqa: S324
        }

    def get(self, file_id, destination):
        raw = self.files[file_id]
        Path(destination).write_bytes(raw)
        self.downloads.append(file_id)
        return {"file_id": file_id, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class TestHistoricalBoundedBatchAuthorization(unittest.TestCase):
    def test_config_and_pinned_pilot_evidence_pass(self):
        out = validate_config(config(), root=ROOT)
        self.assertEqual(out["batch_years"], [2020, 2019, 2018, 2017, 2016])
        self.assertEqual(out["max_years_per_batch"], 5)
        self.assertEqual(out["total_stage_count"], 45)

    def test_wrapper_bootstraps_repo_root_before_package_import(self):
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        bootstrap = 'sys.path.insert(0, str(ROOT))'
        package_import = "from robo_dados_publicos.sources.siope_client_limeira_historical_bounded_batch_authorization import"
        self.assertIn("import sys", text)
        self.assertIn(bootstrap, text)
        self.assertIn(package_import, text)
        self.assertLess(text.index(bootstrap), text.index(package_import))

    def test_fake_five_year_batch_executes_bounded_pipeline(self):
        source, drive = FakeSiope(), FakeDrive()
        out = run_bounded_batch(config(), root=ROOT, siope_client=source, drive=drive)
        self.assertEqual(out["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION")
        self.assertEqual(out["batch_year_count"], 5)
        self.assertEqual(out["source_get_count"], 5)
        self.assertEqual(len(source.calls), 5)
        self.assertEqual(out["drive_preflight_collision_checks"], 15)
        self.assertEqual(out["drive_write_count"], 15)
        self.assertEqual(out["drive_download_count"], 15)
        self.assertEqual(len(drive.puts), 15)
        self.assertEqual(len(drive.downloads), 15)
        self.assertEqual(out["total_stage_count"], 45)
        self.assertTrue(out["batch_live_authorized"])
        self.assertTrue(out["bounded_batch_only"])
        self.assertFalse(out["future_batch_execution_authorized"])
        self.assertFalse(out["compliance_claims_authorized"])

    def test_bad_source_year_stops_before_any_drive_write(self):
        source, drive = FakeSiope(bad_year=2019), FakeDrive()
        with self.assertRaises(HistoricalBoundedBatchAuthorizationError):
            run_bounded_batch(config(), root=ROOT, siope_client=source, drive=drive)
        self.assertEqual(drive.puts, [])
        self.assertEqual(drive.downloads, [])

    def test_collision_anywhere_stops_before_first_write(self):
        source, drive = FakeSiope(), FakeDrive(collision_token="2018_P6")
        with self.assertRaises(HistoricalBoundedBatchAuthorizationError):
            run_bounded_batch(config(), root=ROOT, siope_client=source, drive=drive)
        self.assertEqual(len(source.calls), 5)
        self.assertEqual(drive.puts, [])
        self.assertEqual(drive.downloads, [])

    def test_more_than_five_years_fails_closed(self):
        cfg = config()
        cfg["batch_years"] = [2020, 2019, 2018, 2017, 2016, 2015]
        with self.assertRaises(HistoricalBoundedBatchAuthorizationError):
            validate_config(cfg, root=ROOT)

    def test_duplicate_or_unsorted_years_fail_closed(self):
        for years in ([2020, 2019, 2019, 2017, 2016], [2019, 2020, 2018, 2017, 2016]):
            cfg = config()
            cfg["batch_years"] = list(years)
            with self.assertRaises(HistoricalBoundedBatchAuthorizationError):
                validate_config(cfg, root=ROOT)

    def test_retry_pagination_recurrence_schedule_cannot_be_enabled(self):
        for key in ("retry_authorized", "pagination_authorized", "recurrence_authorized", "schedule_enabled"):
            cfg = config()
            cfg[key] = True
            with self.assertRaises(HistoricalBoundedBatchAuthorizationError):
                validate_config(cfg, root=ROOT)

    def test_pilot_evidence_blob_drift_fails_closed(self):
        cfg = config()
        cfg["pilot_evidence"]["blob_sha"] = "0" * 40
        with self.assertRaises(HistoricalBoundedBatchAuthorizationError):
            validate_config(cfg, root=ROOT)


if __name__ == "__main__":
    unittest.main()
