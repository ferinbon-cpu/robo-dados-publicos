from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_REVIEW"


class HistoricalGoldDriveReadbackReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalGoldDriveReadbackReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalGoldDriveReadbackReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324


def validate_config(config: dict) -> dict:
    expected = {'compliance_claims_authorized': False, 'evidence_blob_sha': 'e344a7d01e9226b13fd4169373cd2a5fc8aedcb8', 'evidence_path': 'docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json', 'expected_artifact_digest': 'sha256:e80a9bc76b31c2c4fa0a1dbfb6f759653b8cf7afe09b075aea2a556fa15bfee5', 'expected_artifact_id': 9643697931, 'expected_artifact_size_bytes': 683, 'expected_head_sha': 'dce9cffca1a85e9415dfa2daf1fc4e49ba57e985', 'expected_historical_tests': 109, 'expected_job_id': 98495812293, 'expected_metric_count': 8, 'expected_run_id': 33065919823, 'expected_unit_tests': 1035, 'gate_id': 'M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_REVIEW_0_8_0', 'gold_contract': 'SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1', 'gold_payload_bytes': 1623, 'gold_payload_sha256': 'a4da994fd2a04ef0b3133d9a20855e6809922f19366075d48aab3296ca488272', 'historical_collection_authorized': False, 'historical_next_single_period_validation_design_authorized': True, 'imputation_authorized': False, 'mode': 'OFFLINE_PINNED_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_REVIEW', 'network_authorized': False, 'next_gate': 'M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_0_8_0', 'processing_authorized': False, 'recurrence_authorized': False, 'remote_name': 'FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2023_P6__352690__a4da994fd2a0__gold_v1.json', 'schedule_enabled': False, 'semantic_scope': 'DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS', 'software_version': '0.8.0', 'source_id': 'FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA'}
    _require(config, expected, "CONFIG_DRIFT")
    return config


def review(config: dict, *, root: str | Path) -> dict:
    validate_config(config)
    evidence_path = Path(root) / config["evidence_path"]
    raw = evidence_path.read_bytes()
    _require(_git_blob_sha(raw), config["evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    evidence = load_json(evidence_path)

    expected_evidence = {
        "artifact_digest": config["expected_artifact_digest"],
        "artifact_id": config["expected_artifact_id"],
        "artifact_name": f"siope-client-limeira-historical-2023-p6-gold-drive-readback-verification-{config['expected_run_id']}",
        "artifact_size_bytes": config["expected_artifact_size_bytes"],
        "byte_identity_verified": True,
        "compliance_claims_authorized": False,
        "drive_file_download_count": 1,
        "drive_network_called": True,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_contract": config["gold_contract"],
        "gold_payload_bytes": config["gold_payload_bytes"],
        "gold_payload_md5_verified": True,
        "gold_payload_sha256": config["gold_payload_sha256"],
        "head_sha": config["expected_head_sha"],
        "historical_failures": 0,
        "historical_passes": config["expected_historical_tests"],
        "historical_tests": config["expected_historical_tests"],
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
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_VERIFICATION",
        "unit_failures": 0,
        "unit_passes": config["expected_unit_tests"],
        "unit_tests": config["expected_unit_tests"],
        "workflow_event": "workflow_dispatch",
        "workflow_head_branch": "main",
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_run_id": config["expected_run_id"],
        "gold_contract": config["gold_contract"],
        "gold_payload_bytes": config["gold_payload_bytes"],
        "gold_payload_sha256": config["gold_payload_sha256"],
        "metric_count": config["expected_metric_count"],
        "byte_identity_verified": True,
        "historical_next_single_period_validation_design_authorized": True,
        "historical_collection_authorized": False,
        "processing_authorized": False,
        "compliance_claims_authorized": False,
        "imputation_performed": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
