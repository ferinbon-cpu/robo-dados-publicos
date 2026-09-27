from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.sources.siope_client_limeira_historical_2021_p6_full_schema_readonly_validation import (
    SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError,
    run_validation,
    validate_config as validate_2021_config,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_gold_drive_readback_review import (
    HistoricalGoldDriveReadbackReviewError,
    review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_gold_drive_readback_review.json"
VALIDATION_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2021_p6_full_schema_readonly_validation.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2021-p6-full-schema-readonly-validation-gate.yml"


class FakeResponse:
    def __init__(self, payload: dict, *, url: str, content_type: str = "application/json", status: int = 200):
        self._raw = json.dumps(payload).encode("utf-8")
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def read(self, n: int = -1):
        return self._raw if n < 0 else self._raw[:n]


def full_record_2021() -> dict:
    record = {field: None for field in PROVEN_DADOS_GERAIS_FIELDS}
    record.update({
        "COD_MUNI": 352690,
        "NOM_MUNI": "Limeira",
        "NUM_ANO": 2021,
        "NUM_PERI": 6,
        "SIG_UF": "SP",
    })
    return record


def opener_for(payload: dict):
    return lambda req, timeout: FakeResponse(payload, url=req.full_url)


class Historical2022GoldReadbackReviewAnd2021P6ValidationTests(unittest.TestCase):
    def test_pinned_2022_gold_readback_review_passes_offline(self):
        config = json.loads(REVIEW_CONFIG.read_text(encoding="utf-8"))
        result = review(config, root=ROOT)
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_READBACK_REVIEW",
        )
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["historical_next_single_period_validation_design_authorized"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertEqual(
            result["next_gate"],
            "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_0_8_0",
        )

    def test_readback_review_rejects_config_drift(self):
        config = json.loads(REVIEW_CONFIG.read_text(encoding="utf-8"))
        config["expected_run_id"] += 1
        with self.assertRaisesRegex(HistoricalGoldDriveReadbackReviewError, "CONFIG_DRIFT"):
            review(config, root=ROOT)

    def test_2021_design_is_one_request_closed_and_exact(self):
        config = json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8"))
        result = validate_2021_config(config)
        self.assertEqual(result["target_year"], 2021)
        self.assertEqual(result["target_period"], 6)
        self.assertEqual(result["proven_schema_allowlist_count"], 52)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["collection_authorized"])
        self.assertFalse(result["persistence_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertFalse(result["schedule_enabled"])

    def test_2021_config_cannot_enable_collection_retry_or_pagination(self):
        config = json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8"))
        for key in ("historical_collection_authorized", "collection_authorized", "persistence_authorized"):
            bad = copy.deepcopy(config)
            bad[key] = True
            with self.assertRaises(SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError):
                validate_2021_config(bad)
        bad = copy.deepcopy(config)
        bad["policy"]["max_attempts"] = 2
        with self.assertRaises(SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError):
            validate_2021_config(bad)
        bad = copy.deepcopy(config)
        bad["policy"]["follow_nextlink"] = True
        with self.assertRaises(SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError):
            validate_2021_config(bad)

    def test_mocked_2021_success_is_one_get_sanitized_and_exact_52(self):
        config = json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8"))
        result = run_validation(
            config,
            opener=opener_for({"@odata.context": "sanitized-test-context", "value": [full_record_2021()]}),
        )
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION",
        )
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["selected_schema_key_count"], 52)
        self.assertTrue(result["selected_schema_exact"])
        self.assertTrue(result["all_records_match_year"])
        self.assertFalse(result["record_values_persisted"])
        self.assertFalse(result["response_body_persisted"])
        self.assertFalse(result["retry_performed"])
        self.assertFalse(result["odata_nextlink_followed"])
        self.assertFalse(result["historical_collection_authorized"])

    def test_2021_missing_schema_field_fails_closed(self):
        config = json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8"))
        record = full_record_2021()
        record.pop("VAL_PIB")
        with self.assertRaisesRegex(
            SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError,
            "FULL_SCHEMA_DRIFT",
        ):
            run_validation(config, opener=opener_for({"value": [record]}))

    def test_2021_identity_drift_fails_closed(self):
        config = json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8"))
        for key, wrong in (("COD_MUNI", 1), ("NUM_ANO", 2022), ("NUM_PERI", 5), ("SIG_UF", "RJ")):
            record = full_record_2021()
            record[key] = wrong
            with self.subTest(key=key), self.assertRaisesRegex(
                SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError,
                "IDENTITY_MISMATCH",
            ):
                run_validation(config, opener=opener_for({"value": [record]}))

    def test_scripts_run_directly_without_live_network(self):
        commands = [
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_gold_drive_readback_review_gate.py"],
            [sys.executable, "scripts/github_siope_client_limeira_historical_2021_p6_full_schema_readonly_validation_gate.py", "--dry-run"],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_workflow_manual_readonly_full_qa_and_no_persistence(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2021_p6_full_schema_readonly_validation", text)
        self.assertIn("contents: read", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_gold_drive_readback_review_gate.py", text)
        self.assertIn("--dry-run", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("continue-on-error: true", text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertNotIn("GOOGLE_DRIVE_", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("upload_file", text)

    def test_workflow_orders_review_qa_before_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        review_at = text.index("github_siope_client_limeira_historical_2022_p6_gold_drive_readback_review_gate.py")
        tests_at = text.index("python -m unittest discover -s tests -v")
        selftest_at = text.index("python main.py selftest")
        live_at = text.index("--output siope-client-limeira-historical-2021-p6-full-schema-readonly-validation-evidence/result.json")
        self.assertLess(review_at, tests_at)
        self.assertLess(tests_at, selftest_at)
        self.assertLess(selftest_at, live_at)


if __name__ == "__main__":
    unittest.main()
