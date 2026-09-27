from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_gold_transform_preview import (
    HistoricalGoldTransformPreviewError,
    build_preview,
    load_json as load_preview_json,
)

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_REVIEW"


class HistoricalGoldTransformReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalGoldTransformReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalGoldTransformReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324


def validate_config(config: dict) -> dict:
    expected = {
        "compliance_claims_authorized": False,
        "evidence_blob_sha": "690b4bb23ff7b2e72e5bae4c4de95dc6dc408177",
        "evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_PREVIEW_RUN_1_0.8.0.json",
        "expected_artifact_digest": "sha256:b0a339e3d41a545f828a144e1570a458c58e9e6ca8551c425f0b41f3122e97a8",
        "expected_artifact_id": 9655242847,
        "expected_head_sha": "f8e63222ac0fc3152680a8c0c14a6beaf1a311aa",
        "expected_historical_tests": 109,
        "expected_job_id": 98591102247,
        "expected_metric_count": 8,
        "expected_run_id": 33093163233,
        "expected_unit_tests": 1108,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_REVIEW_0_8_0",
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "gold_drive_persistence_design_authorized": True,
        "gold_payload_bytes": 1623,
        "gold_payload_sha256": "4057aac2b18dc7184db992ee989d64c8732c4ad858cc6e8b7520cd50c4d37f68",
        "gold_remote_write_authorized": False,
        "historical_collection_authorized": False,
        "imputation_authorized": False,
        "mode": "OFFLINE_PINNED_HISTORICAL_2022_P6_GOLD_TRANSFORM_PREVIEW_REVIEW",
        "network_authorized": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_DESIGN_0_8_0",
        "preview_config_path": "config/source_expansion.siope_client_limeira_historical_2022_p6_gold_transform_preview.json",
        "preview_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_PREVIEW_0_8_0",
        "processing_authorized": False,
        "recurrence_authorized": False,
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

    _require(
        set(evidence),
        {"artifact_digest", "artifact_id", "artifact_name", "head_sha", "job_id", "qa", "result", "run_id", "status", "workflow"},
        "EVIDENCE_KEYS",
    )
    _require(evidence["run_id"], config["expected_run_id"], "RUN_ID")
    _require(evidence["job_id"], config["expected_job_id"], "JOB_ID")
    _require(evidence["artifact_id"], config["expected_artifact_id"], "ARTIFACT_ID")
    _require(evidence["artifact_digest"], config["expected_artifact_digest"], "ARTIFACT_DIGEST")
    _require(evidence["head_sha"], config["expected_head_sha"], "HEAD_SHA")
    _require(
        evidence["status"],
        "PINNED_SUCCESSFUL_MANUAL_HISTORICAL_2022_P6_GOLD_TRANSFORM_PREVIEW_EVIDENCE",
        "EVIDENCE_STATUS",
    )
    _require(
        evidence["workflow"],
        "M7 SIOPE CLIENT LIMEIRA HISTORICAL 2022 P6 GOLD TRANSFORM PREVIEW GATE",
        "WORKFLOW",
    )
    _require(
        evidence["artifact_name"],
        f"siope-client-limeira-historical-2022-p6-gold-transform-preview-{config['expected_run_id']}",
        "ARTIFACT_NAME",
    )
    _require(
        evidence["qa"],
        {
            "historical_failures": 0,
            "historical_passes": config["expected_historical_tests"],
            "historical_tests": config["expected_historical_tests"],
            "unit_passes": config["expected_unit_tests"],
            "unit_tests": config["expected_unit_tests"],
        },
        "QA",
    )

    try:
        preview_config = load_preview_json(root_path / config["preview_config_path"])
        gold_payload, local_result = build_preview(preview_config, root=root_path)
    except (HistoricalGoldTransformPreviewError, OSError, json.JSONDecodeError) as exc:
        raise HistoricalGoldTransformReviewError(f"{ERROR}_LOCAL_REBUILD") from exc

    result = evidence.get("result")
    _require(result, local_result, "RESULT_DRIFT")
    _require(result.get("status"), "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_PREVIEW", "PREVIEW_STATUS")
    _require(result.get("gold_payload_sha256"), config["gold_payload_sha256"], "GOLD_SHA256")
    _require(result.get("gold_payload_bytes"), config["gold_payload_bytes"], "GOLD_BYTES")
    _require(result.get("gold_contract"), config["gold_contract"], "GOLD_CONTRACT")
    _require(result.get("metric_count"), config["expected_metric_count"], "METRIC_COUNT")
    _require(result.get("semantic_scope"), config["semantic_scope"], "SEMANTIC_SCOPE")
    _require(result.get("network_called"), False, "NETWORK")
    _require(result.get("source_network_called"), False, "SOURCE_NETWORK")
    _require(result.get("drive_network_called"), False, "DRIVE_NETWORK")
    _require(result.get("drive_write_count"), 0, "DRIVE_WRITE_COUNT")
    _require(result.get("gold_payload_persisted"), False, "GOLD_PERSISTED")
    _require(result.get("gold_persistence_authorized"), False, "GOLD_PERSISTENCE_AUTH")
    _require(result.get("gold_remote_write_authorized"), False, "GOLD_WRITE_AUTH")
    _require(result.get("compliance_claims_authorized"), False, "COMPLIANCE")
    _require(result.get("imputation_performed"), False, "IMPUTATION")
    _require(result.get("historical_collection_authorized"), False, "HISTORICAL_COLLECTION")
    _require(result.get("processing_authorized"), False, "PROCESSING")
    _require(result.get("recurrence_authorized"), False, "RECURRENCE")
    _require(result.get("schedule_enabled"), False, "SCHEDULE")
    _require(len(gold_payload.get("metrics", {})), config["expected_metric_count"], "LOCAL_METRICS")

    return {
        "compliance_claims_authorized": False,
        "gate_id": config["gate_id"],
        "gold_contract": config["gold_contract"],
        "gold_drive_persistence_design_authorized": True,
        "gold_payload_bytes": config["gold_payload_bytes"],
        "gold_payload_sha256": config["gold_payload_sha256"],
        "gold_remote_write_authorized": False,
        "historical_collection_authorized": False,
        "imputation_performed": False,
        "metric_count": config["expected_metric_count"],
        "network_called": False,
        "next_gate": config["next_gate"],
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "semantic_scope": config["semantic_scope"],
        "status": PASS,
    }
