from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_single_year_pilot import (
    EXPECTED_STAGES,
    HistoricalParameterizedSingleYearPilotError,
    run_pilot,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/source_expansion.siope_client_limeira_historical_parameterized_single_year_pilot.json"
SCRIPT_PATH = ROOT / "scripts/github_siope_client_limeira_historical_parameterized_single_year_pilot_gate.py"


def config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def record():
    item = {field: 0 for field in PROVEN_DADOS_GERAIS_FIELDS}
    item.update({
        "COD_MUNI": 352690, "NOM_MUNI": "Limeira", "SIG_UF": "SP", "NUM_ANO": 2021, "NUM_PERI": 6,
        "VAL_RECE_PREV_ATUA": "1000", "VAL_RECE_REAL": "900", "VAL_DESP_DOTA_ATUA": "800",
        "VAL_DESP_EMPE": "700", "VAL_DESP_LIQU": "650", "VAL_DESP_PAGA": "600",
        "VL_DESP_DOTA_ATUA_EDU": "300", "VL_DESP_EMPE_EDU": "200", "VL_DESP_LIQU_EDU": "190",
        "VL_DESP_PAGA_EDU": "180", "NUM_POPU": "100",
    })
    return item


class FakeSiope:
    def __init__(self):
        self.calls = []

    def get_dados_gerais_page(self, **kwargs):
        self.calls.append(kwargs)
        raw = json.dumps({"value": [record()]}, sort_keys=True).encode()
        return SimpleNamespace(records=[record()], status=200, content_type="application/json",
            response_byte_count=len(raw), odata_context_present=True, nextlink_present=False, request_count=1,
            response_sha256=hashlib.sha256(raw).hexdigest())


class FakeDrive:
    def __init__(self, collision=False):
        self.collision = collision
        self.puts = []
        self.downloads = []
        self.files = {}

    def find_by_name(self, parent_id, name):
        if self.collision:
            return [{"id": "existing", "name": name}]
        return []

    def put(self, local_path, remote_name, parent_id, mime_type):
        raw = Path(local_path).read_bytes()
        file_id = f"id-{len(self.files)+1}"
        self.files[file_id] = raw
        self.puts.append((parent_id, remote_name))
        return {"id": file_id, "name": remote_name, "mimeType": mime_type, "size": str(len(raw)),
            "md5Checksum": hashlib.md5(raw).hexdigest(), "parents": [parent_id]}  # noqa: S324

    def get(self, file_id, destination):
        raw = self.files[file_id]
        Path(destination).write_bytes(raw)
        self.downloads.append(file_id)
        return {"file_id": file_id, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class TestHistoricalParameterizedSingleYearPilot(unittest.TestCase):
    def test_config_and_pinned_dry_run_evidence_pass(self):
        out = validate_config(config(), root=ROOT)
        self.assertEqual(out["pilot_year"], 2021)
        self.assertEqual(out["stage_count"], 9)

    def test_wrapper_bootstraps_repo_root_before_package_import(self):
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("import sys", text)
        bootstrap = 'sys.path.insert(0, str(ROOT))'
        package_import = "from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_single_year_pilot import"
        self.assertIn(bootstrap, text)
        self.assertIn(package_import, text)
        self.assertLess(text.index(bootstrap), text.index(package_import))

    def test_fake_end_to_end_executes_one_orchestrated_nine_stage_pilot(self):
        source, drive = FakeSiope(), FakeDrive()
        out = run_pilot(config(), root=ROOT, siope_client=source, drive=drive)
        self.assertEqual(out["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT")
        self.assertEqual(out["stages_completed"], list(EXPECTED_STAGES))
        self.assertEqual(out["source_get_count"], 1)
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(out["drive_write_count"], 3)
        self.assertEqual(out["drive_download_count"], 3)
        self.assertEqual(len(drive.puts), 3)
        self.assertEqual(len(drive.downloads), 3)
        self.assertEqual(out["metric_count"], 8)
        self.assertFalse(out["batch_live_authorized"])
        self.assertFalse(out["compliance_claims_authorized"])

    def test_collision_stops_before_first_write(self):
        drive = FakeDrive(collision=True)
        with self.assertRaises(HistoricalParameterizedSingleYearPilotError):
            run_pilot(config(), root=ROOT, siope_client=FakeSiope(), drive=drive)
        self.assertEqual(drive.puts, [])
        self.assertEqual(drive.downloads, [])

    def test_batch_live_cannot_be_enabled(self):
        cfg = config(); cfg["batch_live_authorized"] = True
        with self.assertRaises(HistoricalParameterizedSingleYearPilotError):
            validate_config(cfg, root=ROOT)

    def test_retry_cannot_be_enabled(self):
        cfg = config(); cfg["retry_authorized"] = True
        with self.assertRaises(HistoricalParameterizedSingleYearPilotError):
            validate_config(cfg, root=ROOT)

    def test_pagination_cannot_be_enabled(self):
        cfg = config(); cfg["pagination_authorized"] = True
        with self.assertRaises(HistoricalParameterizedSingleYearPilotError):
            validate_config(cfg, root=ROOT)

    def test_evidence_blob_drift_fails_closed(self):
        cfg = config(); cfg["dry_run_evidence"]["blob_sha"] = "0" * 40
        with self.assertRaises(HistoricalParameterizedSingleYearPilotError):
            validate_config(cfg, root=ROOT)

    def test_wrong_source_identity_stops_before_drive_write(self):
        bad = record(); bad["NUM_ANO"] = 2020
        class BadSource:
            def get_dados_gerais_page(self, **kwargs):
                raw = json.dumps({"value": [bad]}, sort_keys=True).encode()
                return SimpleNamespace(records=[bad], status=200, content_type="application/json",
                    response_byte_count=len(raw), odata_context_present=True, nextlink_present=False, request_count=1,
                    response_sha256=hashlib.sha256(raw).hexdigest())
        drive = FakeDrive()
        with self.assertRaises(HistoricalParameterizedSingleYearPilotError):
            run_pilot(config(), root=ROOT, siope_client=BadSource(), drive=drive)
        self.assertEqual(drive.puts, [])


if __name__ == "__main__":
    unittest.main()
