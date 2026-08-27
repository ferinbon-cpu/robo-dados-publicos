from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_REVIEW"


class GoldDrivePersistenceReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GoldDrivePersistenceReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise GoldDrivePersistenceReviewError(f"{ERROR}_{code}")


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "compliance_claims_authorized": False,
        "drive_readback_design_authorized": True,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION_0_8_0",
        "pinned_artifact_digest": "sha256:8eb43f91bf3b771db92630dadd3b3c38135a7894ff07c97373a012ed81b5078b",
        "pinned_artifact_id": 9628143828,
        "pinned_evidence_blob_sha": "e4ebb167cf3b4fed0c12fe42981f4a7bea9fbcc6",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_RUN_1_0.8.0.json",
        "pinned_gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "pinned_gold_payload_bytes": 1612,
        "pinned_gold_payload_sha256": "d6a35db7c42129569c73f19de789d871d0d285929d8eb3fe2a04d5ef03fdd6e0",
        "pinned_head_sha": "4abe2f8d5e8506ed448f7419a1c7f109b27879d1",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98365055746,
        "pinned_metric_count": 8,
        "pinned_remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__d6a35db7c421__gold_v1.json",
        "pinned_run_id": 33025297262,
        "pinned_run_number": 1,
        "pinned_semantic_scope": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
        "pinned_unit_tests": 931,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG")

    evidence = load_json(Path(root) / config["pinned_evidence_path"])
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-gold-drive-persistence-33025297262",
        "compliance_claims_authorized": False,
        "drive_create_only": True,
        "drive_network_called": True,
        "drive_write_count": 1,
        "event": "workflow_dispatch",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_0_8_0",
        "gold_contract": config["pinned_gold_contract"],
        "gold_payload_bytes": config["pinned_gold_payload_bytes"],
        "gold_payload_md5_verified": True,
        "gold_payload_persisted": True,
        "gold_payload_sha256": config["pinned_gold_payload_sha256"],
        "head_branch": "main",
        "head_sha": config["pinned_head_sha"],
        "historical_regressions": config["pinned_historical_regressions"],
        "historical_regressions_passed": config["pinned_historical_regressions"],
        "imputation_performed": False,
        "job_id": config["pinned_job_id"],
        "metric_count": config["pinned_metric_count"],
        "network_called": True,
        "next_gate": config["gate_id"],
        "processing_authorized": False,
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": config["pinned_remote_name"],
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "schedule_enabled": False,
        "semantic_scope": config["pinned_semantic_scope"],
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE",
        "unit_tests": config["pinned_unit_tests"],
        "unit_tests_passed": config["pinned_unit_tests"],
    }
    _require(evidence, expected_evidence, "EVIDENCE")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_run_id": config["pinned_run_id"],
        "gold_payload_sha256": config["pinned_gold_payload_sha256"],
        "gold_payload_bytes": config["pinned_gold_payload_bytes"],
        "metric_count": config["pinned_metric_count"],
        "gold_contract": config["pinned_gold_contract"],
        "semantic_scope": config["pinned_semantic_scope"],
        "drive_readback_design_authorized": True,
        "compliance_claims_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
