from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_gold_transform_preview import (
    HistoricalGoldTransformPreviewError,
    _decimal_field,
    _pct,
    build_preview,
    load_json,
    validate_config,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_silver_drive_readback_review import (
    HistoricalSilverDriveReadbackReviewError,
    load_json as load_review_json,
    review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_silver_drive_readback_review.json"
GOLD_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_gold_transform_preview.json"
SILVER_PERSISTENCE_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_silver_drive_persistence.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2022-p6-gold-transform-preview-gate.yml"


class Historical2022GoldTransformPreviewTests(unittest.TestCase):
    def test_readback_review_accepts_exact_pinned_success_and_blob(self):
        config = load_review_json(REVIEW_CONFIG)
        evidence = ROOT / config["pinned_evidence_path"]
        raw = evidence.read_bytes()
        actual_blob = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324
        self.assertEqual(actual_blob, config["pinned_evidence_blob_sha"])
        result = review(config, root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_DRIVE_READBACK_REVIEW")
        self.assertTrue(result["gold_transform_preview_design_authorized"])
        self.assertFalse(result["gold_authorized"])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["schema_key_count"], 52)

    def test_readback_review_rejects_tampered_evidence(self):
        config = load_review_json(REVIEW_CONFIG)
        source = ROOT / config["pinned_evidence_path"]
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            target = tmp / config["pinned_evidence_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            evidence = json.loads(source.read_text(encoding="utf-8"))
            evidence["byte_identity_verified"] = False
            target.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaises(HistoricalSilverDriveReadbackReviewError):
                review(config, root=tmp)

    def test_readback_review_config_cannot_enable_gold_processing_or_recurrence(self):
        for field, value in (
            ("gold_authorized", True),
            ("processing_authorized", True),
            ("recurrence_authorized", True),
            ("schedule_enabled", True),
            ("network_called", True),
        ):
            config = load_review_json(REVIEW_CONFIG)
            config[field] = value
            with self.assertRaises(HistoricalSilverDriveReadbackReviewError, msg=field):
                review(config, root=ROOT)

    def test_gold_design_is_offline_write_closed_and_no_compliance_claims(self):
        result = validate_config(load_json(GOLD_CONFIG))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_PREVIEW_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["drive_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["gold_persistence_authorized"])
        self.assertFalse(result["gold_remote_write_authorized"])
        self.assertFalse(result["compliance_claims_authorized"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertFalse(result["schedule_enabled"])

    def test_exact_verified_historical_silver_builds_expected_gold(self):
        payload, result = build_preview(load_json(GOLD_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_PREVIEW")
        self.assertEqual(result["metric_count"], 8)
        self.assertEqual(result["metrics"], {
            "receita_realizada_sobre_previsao_atualizada_pct": "91.5806",
            "despesa_paga_sobre_dotacao_atualizada_pct": "77.9658",
            "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct": "87.6322",
            "participacao_educacao_na_despesa_empenhada_pct": "25.0061",
            "participacao_educacao_na_despesa_liquidada_pct": "25.6356",
            "participacao_educacao_na_despesa_paga_pct": "24.6290",
            "despesa_total_paga_por_habitante": "4360.34",
            "despesa_educacao_paga_por_habitante": "1073.91",
        })
        self.assertEqual(payload["identity"]["municipality_code"], 352690)
        self.assertEqual(payload["identity"]["year"], 2022)
        self.assertEqual(payload["identity"]["period"], 6)
        self.assertEqual(payload["semantic_scope"]["kind"], "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS")
        self.assertFalse(payload["semantic_scope"]["mde_compliance_conclusion"])
        self.assertFalse(payload["semantic_scope"]["fundeb_compliance_conclusion"])
        self.assertFalse(payload["semantic_scope"]["fiscal_audit_conclusion"])
        self.assertFalse(payload["semantic_scope"]["imputation_performed"])
        self.assertFalse(result["gold_payload_persisted"])
        self.assertFalse(result["gold_remote_write_authorized"])
        self.assertEqual(result["gold_payload_bytes"], 1623)
        self.assertEqual(result["gold_payload_sha256"], "4057aac2b18dc7184db992ee989d64c8732c4ad858cc6e8b7520cd50c4d37f68")

    def test_gold_config_drift_cannot_enable_network_write_compliance_or_recurrence(self):
        for field, value in (
            ("source_network_authorized", True),
            ("drive_network_authorized", True),
            ("drive_write_count", 1),
            ("gold_persistence_authorized", True),
            ("gold_remote_write_authorized", True),
            ("compliance_claims_authorized", True),
            ("historical_collection_authorized", True),
            ("imputation_authorized", True),
            ("processing_authorized", True),
            ("recurrence_authorized", True),
            ("schedule_enabled", True),
        ):
            config = load_json(GOLD_CONFIG)
            config[field] = value
            with self.assertRaises(HistoricalGoldTransformPreviewError, msg=field):
                validate_config(config)

    def test_invalid_arithmetic_inputs_fail_closed(self):
        with self.assertRaises(HistoricalGoldTransformPreviewError):
            _decimal_field({"X": None}, "X")
        with self.assertRaises(HistoricalGoldTransformPreviewError):
            _decimal_field({"X": "not-a-number"}, "X")
        with self.assertRaises(HistoricalGoldTransformPreviewError):
            _decimal_field({"X": "-1"}, "X")
        with self.assertRaises(HistoricalGoldTransformPreviewError):
            _pct(Decimal("1"), Decimal("0"))

    def test_tampered_historical_silver_source_record_fails_as_prerequisite(self):
        config = load_json(GOLD_CONFIG)
        silver_config = json.loads(SILVER_PERSISTENCE_CONFIG.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg_target = tmp / config["silver_persistence_config_path"]
            cfg_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SILVER_PERSISTENCE_CONFIG, cfg_target)
            for key in ("record_payload_path", "manifest_payload_path"):
                source = ROOT / silver_config[key]
                target = tmp / silver_config[key]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            record_path = tmp / silver_config["record_payload_path"]
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["VAL_DESP_PAGA"] = "1"
            record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(HistoricalGoldTransformPreviewError):
                build_preview(config, root=tmp)

    def test_gate_scripts_run_directly_without_network(self):
        review_cp = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_silver_drive_readback_review_gate.py"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(review_cp.returncode, 0, review_cp.stderr or review_cp.stdout)
        dry_cp = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_gold_transform_preview_gate.py", "--dry-run"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(dry_cp.returncode, 0, dry_cp.stderr or dry_cp.stdout)
        preview_cp = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_gold_transform_preview_gate.py"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(preview_cp.returncode, 0, preview_cp.stderr or preview_cp.stdout)
        payload = json.loads(preview_cp.stdout)
        self.assertFalse(payload["network_called"])
        self.assertEqual(payload["drive_write_count"], 0)

    def test_workflow_is_manual_offline_full_qa_and_has_no_remote_write(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2022_p6_gold_transform_preview", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_silver_drive_readback_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_gold_transform_preview_gate.py --dry-run", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT", text)
        self.assertNotIn("https://www.fnde.gov.br", text)
        self.assertNotIn("drive.put", text)
        self.assertNotIn("drive.delete", text)
        self.assertNotIn("replace_content", text)
        self.assertNotIn("03_GOLD", text)


if __name__ == "__main__":
    unittest.main()
