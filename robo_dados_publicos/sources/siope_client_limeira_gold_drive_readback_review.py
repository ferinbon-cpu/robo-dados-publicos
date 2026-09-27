from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_REVIEW"


class GoldDriveReadbackReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GoldDriveReadbackReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise GoldDriveReadbackReviewError(f"{ERROR}_{code}")


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "compliance_claims_authorized": False,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_REVIEW_0_8_0",
        "historical_collection_authorized": False,
        "historical_single_period_validation_design_authorized": True,
        "mode": "OFFLINE_PINNED_GOLD_DRIVE_READBACK_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_0_8_0",
        "pinned_artifact_digest": "sha256:fd178f8f4f36dd4f5438f2366c9d9032bf147f59669bf4d81a66bbc9bc40c27d",
        "pinned_artifact_id": 9628606455,
        "pinned_evidence_blob_sha": "291dbd782e89552d8958eebcca69f04fb773d73a",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
        "pinned_gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "pinned_gold_payload_bytes": 1612,
        "pinned_gold_payload_sha256": "d6a35db7c42129569c73f19de789d871d0d285929d8eb3fe2a04d5ef03fdd6e0",
        "pinned_head_sha": "addd05d6d8c1a771f4594283aacce504295dec0b",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98369076525,
        "pinned_metric_count": 8,
        "pinned_run_id": 33026528414,
        "pinned_unit_tests": 940,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence_path = Path(root) / config["pinned_evidence_path"]
    evidence = load_json(evidence_path)
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-gold-drive-readback-verification-33026528414",
        "artifact_size_bytes": 657,
        "byte_identity_verified": True,
        "compliance_claims_authorized": False,
        "drive_file_download_count": 1,
        "drive_network_called": True,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_contract": config["pinned_gold_contract"],
        "gold_payload_bytes": config["pinned_gold_payload_bytes"],
        "gold_payload_md5_verified": True,
        "gold_payload_sha256": config["pinned_gold_payload_sha256"],
        "head_sha": config["pinned_head_sha"],
        "historical_failures": 0,
        "historical_passes": config["pinned_historical_regressions"],
        "historical_tests": config["pinned_historical_regressions"],
        "imputation_performed": False,
        "job_id": config["pinned_job_id"],
        "metric_count": config["pinned_metric_count"],
        "network_called": True,
        "next_gate": config["gate_id"],
        "processing_authorized": False,
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__d6a35db7c421__gold_v1.json",
        "run_id": config["pinned_run_id"],
        "run_number": 1,
        "schedule_enabled": False,
        "semantic_scope": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION",
        "unit_failures": 0,
        "unit_passes": config["pinned_unit_tests"],
        "unit_tests": config["pinned_unit_tests"],
        "workflow_event": "workflow_dispatch",
        "workflow_head_branch": "main",
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "gold_contract": config["pinned_gold_contract"],
        "gold_payload_bytes": config["pinned_gold_payload_bytes"],
        "gold_payload_sha256": config["pinned_gold_payload_sha256"],
        "metric_count": config["pinned_metric_count"],
        "byte_identity_verified": True,
        "historical_single_period_validation_design_authorized": True,
        "historical_collection_authorized": False,
        "processing_authorized": False,
        "compliance_claims_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
