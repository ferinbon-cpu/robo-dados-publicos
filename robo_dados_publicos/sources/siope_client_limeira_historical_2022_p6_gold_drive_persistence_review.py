from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_REVIEW"


class HistoricalGoldDrivePersistenceReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalGoldDrivePersistenceReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalGoldDrivePersistenceReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324


def validate_config(config: dict) -> dict:
    expected = {
        "compliance_claims_authorized": False,
        "drive_readback_design_authorized": True,
        "evidence_blob_sha": "ddc0a4bdb48073cf9926a247be2cf11d18f8cea3",
        "evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_RUN_1_0.8.0.json",
        "expected_artifact_digest": "sha256:4f088bb2214f741a3df61e356ccffc40244d614afc9480bb0f29b281a3e6ba2e",
        "expected_artifact_id": 9657666972,
        "expected_head_sha": "8ebe5bab4cb28260dd06fd0a8dc122fd9cb5363f",
        "expected_historical_tests": 109,
        "expected_job_id": 98611888329,
        "expected_metric_count": 8,
        "expected_run_id": 33099147098,
        "expected_unit_tests": 1117,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "gold_payload_bytes": 1623,
        "gold_payload_sha256": "4057aac2b18dc7184db992ee989d64c8732c4ad858cc6e8b7520cd50c4d37f68",
        "historical_collection_authorized": False,
        "imputation_authorized": False,
        "mode": "OFFLINE_PINNED_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_REVIEW",
        "network_authorized": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_READBACK_VERIFICATION_0_8_0",
        "processing_authorized": False,
        "recurrence_authorized": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2022_P6__352690__4057aac2b18d__gold_v1.json",
        "schedule_enabled": False,
        "semantic_scope": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected, "CONFIG_DRIFT")
    return config


def review(config: dict, *, root: str | Path) -> dict:
    validate_config(config)
    root_path = Path(root)
    evidence_path = root_path / config["evidence_path"]
    raw = evidence_path.read_bytes()
    _require(_git_blob_sha(raw), config["evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    evidence = load_json(evidence_path)

    expected_evidence = {
        "artifact_digest": config["expected_artifact_digest"],
        "artifact_id": config["expected_artifact_id"],
        "artifact_name": f"siope-client-limeira-historical-2022-p6-gold-drive-persistence-{config['expected_run_id']}",
        "compliance_claims_authorized": False,
        "drive_create_only": True,
        "drive_network_called": True,
        "drive_write_count": 1,
        "event": "workflow_dispatch",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_0_8_0",
        "gold_contract": config["gold_contract"],
        "gold_payload_bytes": config["gold_payload_bytes"],
        "gold_payload_md5_verified": True,
        "gold_payload_persisted": True,
        "gold_payload_sha256": config["gold_payload_sha256"],
        "head_branch": "main",
        "head_sha": config["expected_head_sha"],
        "historical_collection_authorized": False,
        "historical_regressions": config["expected_historical_tests"],
        "historical_regressions_passed": config["expected_historical_tests"],
        "imputation_performed": False,
        "job_id": config["expected_job_id"],
        "metric_count": config["expected_metric_count"],
        "network_called": True,
        "next_gate": config["gate_id"],
        "processing_authorized": False,
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": config["remote_name"],
        "run_id": config["expected_run_id"],
        "run_number": 1,
        "schedule_enabled": False,
        "semantic_scope": config["semantic_scope"],
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE",
        "unit_tests": config["expected_unit_tests"],
        "unit_tests_passed": config["expected_unit_tests"],
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")
    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_run_id": config["expected_run_id"],
        "gold_payload_sha256": config["gold_payload_sha256"],
        "gold_payload_bytes": config["gold_payload_bytes"],
        "metric_count": config["expected_metric_count"],
        "gold_contract": config["gold_contract"],
        "semantic_scope": config["semantic_scope"],
        "drive_readback_design_authorized": True,
        "historical_collection_authorized": False,
        "compliance_claims_authorized": False,
        "imputation_performed": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
