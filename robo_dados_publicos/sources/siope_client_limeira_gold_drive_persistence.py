from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_gold_transform_preview import (
    GoldTransformPreviewError,
    build_preview,
    load_json as load_preview_json,
)
from robo_dados_publicos.sources.siope_client_limeira_gold_transform_review import (
    GoldTransformReviewError,
    load_json as load_review_json,
    review,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE"


class GoldDrivePersistenceError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GoldDrivePersistenceError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise GoldDrivePersistenceError(f"{ERROR}_{code}")


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _validated_gold_payload(config: dict, *, root: str | Path) -> dict:
    root_path = Path(root)
    try:
        review_result = review(load_review_json(root_path / config["review_config_path"]), root=root_path)
        _require(review_result.get("status"), "PASS_M7_SIOPE_CLIENT_LIMEIRA_GOLD_TRANSFORM_REVIEW", "REVIEW_STATUS")
        _require(review_result.get("gold_drive_persistence_design_authorized"), True, "REVIEW_DESIGN_AUTH")
        _require(review_result.get("gold_remote_write_authorized"), False, "REVIEW_REMOTE_WRITE")
        preview_config = load_preview_json(root_path / config["preview_config_path"])
        gold_payload, preview_result = build_preview(preview_config, root=root_path)
    except (GoldTransformReviewError, GoldTransformPreviewError, OSError, json.JSONDecodeError) as exc:
        raise GoldDrivePersistenceError(f"{ERROR}_PREREQUISITE") from exc

    payload_bytes = _canonical_bytes(gold_payload)
    _require(len(payload_bytes), config["gold_payload_bytes"], "PAYLOAD_BYTES")
    _require(hashlib.sha256(payload_bytes).hexdigest(), config["gold_payload_sha256"], "PAYLOAD_SHA256")
    _require(gold_payload.get("gold_contract"), config["gold_contract"], "GOLD_CONTRACT")
    _require(gold_payload.get("semantic_scope", {}).get("kind"), config["semantic_scope"], "SEMANTIC_SCOPE")
    _require(gold_payload.get("semantic_scope", {}).get("mde_compliance_conclusion"), False, "MDE_CLAIM")
    _require(gold_payload.get("semantic_scope", {}).get("fundeb_compliance_conclusion"), False, "FUNDEB_CLAIM")
    _require(gold_payload.get("semantic_scope", {}).get("fiscal_audit_conclusion"), False, "AUDIT_CLAIM")
    _require(gold_payload.get("semantic_scope", {}).get("imputation_performed"), False, "IMPUTATION")
    _require(len(gold_payload.get("metrics", {})), 8, "METRIC_COUNT")
    _require(preview_result.get("gold_payload_sha256"), config["gold_payload_sha256"], "PREVIEW_SHA")
    return gold_payload


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "compliance_claims_authorized": False,
        "create_only": True,
        "delete_authorized": False,
        "drive_network_authorized": True,
        "drive_write_count": 1,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_0_8_0",
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "gold_folder_id": "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4",
        "gold_payload_bytes": 1612,
        "gold_payload_sha256": "d6a35db7c42129569c73f19de789d871d0d285929d8eb3fe2a04d5ef03fdd6e0",
        "gold_persistence_authorized": True,
        "gold_remote_write_authorized": True,
        "imputation_authorized": False,
        "manual_confirmation_required": True,
        "mime_type": "application/json",
        "mode": "ONE_VALIDATED_GOLD_CREATE_ONLY",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "overwrite_authorized": False,
        "preview_config_path": "config/source_expansion.siope_client_limeira_gold_transform_preview.json",
        "processing_authorized": False,
        "recurrence_authorized": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__d6a35db7c421__gold_v1.json",
        "replace_authorized": False,
        "review_config_path": "config/source_expansion.siope_client_limeira_gold_transform_review.json",
        "review_gate": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_TRANSFORM_REVIEW_0_8_0",
        "schedule_enabled": False,
        "semantic_scope": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "source_network_authorized": False,
    }
    _require(config, expected, "CONFIG_DRIFT")
    payload = _validated_gold_payload(config, root=root)
    payload_bytes = _canonical_bytes(payload)
    return {
        "compliance_claims_authorized": False,
        "drive_network_called": False,
        "drive_write_count": 0,
        "gold_payload_bytes": len(payload_bytes),
        "gold_payload_persisted": False,
        "gold_payload_sha256": config["gold_payload_sha256"],
        "gold_remote_write_authorized": True,
        "imputation_performed": False,
        "metric_count": 8,
        "network_called": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "source_network_called": False,
        "status": f"{PASS}_DESIGN",
    }


def persist(config: dict, *, root: str | Path, drive=None) -> dict:
    validate_config(config, root=root)
    payload = _validated_gold_payload(config, root=root)
    payload_bytes = _canonical_bytes(payload)
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    payload_md5 = hashlib.md5(payload_bytes).hexdigest()  # noqa: S324
    _require(payload_sha256, config["gold_payload_sha256"], "LIVE_PAYLOAD_SHA256")
    _require(len(payload_bytes), config["gold_payload_bytes"], "LIVE_PAYLOAD_BYTES")

    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))

    existing = drive.find_by_name(config["gold_folder_id"], config["remote_name"])
    if existing:
        raise GoldDrivePersistenceError(f"{ERROR}_REMOTE_NAME_COLLISION")

    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "gold_payload.json"
        local.write_bytes(payload_bytes)
        uploaded = drive.put(local, config["remote_name"], config["gold_folder_id"], config["mime_type"])

    _require(uploaded.get("name"), config["remote_name"], "REMOTE_NAME")
    _require(uploaded.get("mimeType"), config["mime_type"], "REMOTE_MIME")
    _require(str(uploaded.get("size")), str(config["gold_payload_bytes"]), "REMOTE_SIZE")
    _require(uploaded.get("md5Checksum"), payload_md5, "REMOTE_MD5")

    return {
        "compliance_claims_authorized": False,
        "drive_create_only": True,
        "drive_network_called": True,
        "drive_write_count": 1,
        "gate_id": config["gate_id"],
        "gold_contract": config["gold_contract"],
        "gold_payload_bytes": len(payload_bytes),
        "gold_payload_md5_verified": True,
        "gold_payload_persisted": True,
        "gold_payload_sha256": payload_sha256,
        "imputation_performed": False,
        "metric_count": 8,
        "network_called": True,
        "next_gate": config["next_gate"],
        "processing_authorized": False,
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": config["remote_name"],
        "schedule_enabled": False,
        "semantic_scope": config["semantic_scope"],
        "source_network_called": False,
        "status": PASS,
    }
