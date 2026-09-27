from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.sources.siope_client_limeira_historical_bounded_batch_source_probe import (
    ERROR,
    PASS,
    HistoricalBoundedBatchSourceProbeError,
    run_source_probe,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/source_expansion.siope_client_limeira_historical_bounded_batch_source_probe.json"
SCRIPT_PATH = ROOT / "scripts/github_siope_client_limeira_historical_bounded_batch_source_probe_gate.py"
WORKFLOW_PATH = ROOT / ".github/workflows/siope-client-limeira-historical-bounded-batch-source-probe-gate.yml"
MODULE_PATH = ROOT / "robo_dados_publicos/sources/siope_client_limeira_historical_bounded_batch_source_probe.py"


def config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def record(year: int):
    item = {field: 0 for field in PROVEN_DADOS_GERAIS_FIELDS}
    item.update(
        {
            "COD_MUNI": 352690,
            "NOM_MUNI": "Limeira",
            "SIG_UF": "SP",
            "NUM_ANO": year,
            "NUM_PERI": 6,
        }
    )
    return item


class FakeSiope:
    def __init__(self, counts=None, wrong_identity_year=None):
        self.calls = []
        self.counts = counts or {}
        self.wrong_identity_year = wrong_identity_year

    def get_dados_gerais_page(self, **kwargs):
        self.calls.append(kwargs)
        year = kwargs["ano"]
        count = self.counts.get(year, 1)
        rows = [record(year) for _ in range(count)]
        if rows and year == self.wrong_identity_year:
            rows[0]["NUM_ANO"] = 1999
        raw = json.dumps({"value": rows}, sort_keys=True).encode()
        return SimpleNamespace(
            records=rows,
            status=200,
            content_type="application/json",
            response_byte_count=len(raw),
            odata_context_present=True,
            nextlink_present=False,
            request_count=1,
            response_sha256=hashlib.sha256(raw).hexdigest(),
        )


class TestHistoricalBoundedBatchSourceProbe(unittest.TestCase):
    def test_config_and_prior_failure_evidence_pass(self):
        out = validate_config(config(), root=ROOT)
        self.assertEqual(out["batch_years"], [2020, 2019, 2018, 2017, 2016])
        self.assertEqual(out["source_get_count"], 5)
        self.assertFalse(out["drive_called"])
        self.assertEqual(out["drive_write_count"], 0)

    def test_probe_all_five_valid_is_readonly_pass(self):
        source = FakeSiope()
        out = run_source_probe(config(), root=ROOT, siope_client=source)
        self.assertEqual(out["status"], PASS)
        self.assertEqual(len(source.calls), 5)
        self.assertEqual(out["source_get_count"], 5)
        self.assertFalse(out["drive_called"])
        self.assertEqual(out["drive_write_count"], 0)
        self.assertTrue(all(item["record_count"] == 1 for item in out["years"]))
        self.assertTrue(all(item["schema_key_count"] == 52 for item in out["years"]))
        self.assertTrue(all(item["identity_validated"] for item in out["years"]))
        self.assertTrue(all(item["validation_code"] == "PASS" for item in out["years"]))
        self.assertTrue(all("record" not in item for item in out["years"]))

    def test_record_count_findings_are_reported_for_all_years_without_short_circuit(self):
        source = FakeSiope(counts={2019: 0, 2017: 2})
        out = run_source_probe(config(), root=ROOT, siope_client=source)
        self.assertEqual(out["status"], ERROR)
        self.assertEqual(len(source.calls), 5)
        by_year = {item["year"]: item for item in out["years"]}
        self.assertEqual(by_year[2019]["record_count"], 0)
        self.assertEqual(by_year[2019]["validation_code"], "SOURCE_RECORD_COUNT")
        self.assertEqual(by_year[2017]["record_count"], 2)
        self.assertEqual(by_year[2017]["validation_code"], "SOURCE_RECORD_COUNT")
        self.assertFalse(out["drive_called"])
        self.assertEqual(out["drive_write_count"], 0)
        self.assertIsNone(out["next_gate"])

    def test_identity_drift_is_sanitized_and_probe_continues(self):
        source = FakeSiope(wrong_identity_year=2018)
        out = run_source_probe(config(), root=ROOT, siope_client=source)
        self.assertEqual(out["status"], ERROR)
        self.assertEqual(len(source.calls), 5)
        item = next(row for row in out["years"] if row["year"] == 2018)
        self.assertEqual(item["validation_code"], "SOURCE_YEAR")
        self.assertFalse(item["identity_validated"])
        self.assertNotIn("record", item)

    def test_config_drift_cannot_enable_drive_retry_pagination_or_schedule(self):
        for key in (
            "drive_access_authorized",
            "retry_authorized",
            "pagination_authorized",
            "recurrence_authorized",
            "schedule_enabled",
        ):
            cfg = config()
            cfg[key] = True
            with self.assertRaises(HistoricalBoundedBatchSourceProbeError):
                validate_config(cfg, root=ROOT)

    def test_prior_failure_blob_drift_fails_closed(self):
        cfg = config()
        cfg["prior_failure_evidence"]["blob_sha"] = "0" * 40
        with self.assertRaises(HistoricalBoundedBatchSourceProbeError):
            validate_config(cfg, root=ROOT)

    def test_source_probe_module_has_no_drive_client_or_credentials(self):
        text = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("DriveRESTClient", text)
        self.assertNotIn("OAuthCredentials", text)
        self.assertNotIn("storage.drive", text)

    def test_script_bootstraps_repo_root_before_package_import(self):
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        bootstrap = 'sys.path.insert(0, str(ROOT))'
        package_import = "from robo_dados_publicos.sources.siope_client_limeira_historical_bounded_batch_source_probe import"
        self.assertIn("import sys", text)
        self.assertIn(bootstrap, text)
        self.assertIn(package_import, text)
        self.assertLess(text.index(bootstrap), text.index(package_import))

    def test_workflow_is_manual_readonly_no_drive_and_full_qa_precedes_live(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_bounded_batch_source_probe:", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_ID", text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_SECRET", text)
        self.assertNotIn("GOOGLE_DRIVE_REFRESH_TOKEN", text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        unit = text.index("python -m unittest discover -s tests -v")
        regression = text.index("python main.py selftest")
        live = text.index("--output siope-client-limeira-historical-bounded-batch-source-probe-evidence/result.json")
        self.assertLess(unit, live)
        self.assertLess(regression, live)
        self.assertIn("if: ${{ always() }}", text)
        self.assertIn("Propagar STOP da sonda", text)


if __name__ == "__main__":
    unittest.main()
