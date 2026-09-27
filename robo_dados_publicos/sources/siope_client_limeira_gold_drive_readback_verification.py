from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_gold_drive_persistence import (
    _canonical_bytes,
    _validated_gold_payload,
    load_json as load_persistence_json,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION"


class GoldDriveReadbackVerificationError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GoldDriveReadbackVerificationError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise GoldDriveReadbackVerificationError(f"{ERROR}_{code}")


def _expected_payload(config: dict, *, root: str | Path) -> tuple[dict, bytes]:
    root_path = Path(root)
    try:
        persistence_config = load_persistence_json(root_path / config["persistence_config_path"])
        payload = _validated_gold_payload(persistence_config, root=root_path)
    except Exception as exc:
        raise GoldDriveReadbackVerificationError(f"{ERROR}_EXPECTED_PAYLOAD_PREREQUISITE") from exc

    payload_bytes = _canonical_bytes(payload)
    _require(len(payload_bytes), config["gold_payload_bytes"], "EXPECTED_PAYLOAD_BYTES")
    _require(hashlib.sha256(payload_bytes).hexdigest(), config["gold_payload_sha256"], "EXPECTED_PAYLOAD_SHA256")
    _require(payload.get("gold_contract"), config["gold_contract"], "GOLD_CONTRACT")
    semantic_scope = payload.get("semantic_scope") or {}
    _require(semantic_scope.get("kind"), config["semantic_scope"], "SEMANTIC_SCOPE")
    _require(semantic_scope.get("mde_compliance_conclusion"), False, "MDE_CLAIM")
    _require(semantic_scope.get("fundeb_compliance_conclusion"), False, "FUNDEB_CLAIM")
    _require(semantic_scope.get("fiscal_audit_conclusion"), False, "AUDIT_CLAIM")
    _require(semantic_scope.get("imputation_performed"), False, "IMPUTATION")
    _require(len(payload.get("metrics", {})), 8, "METRIC_COUNT")
    return payload, payload_bytes


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "compliance_claims_authorized": False,
        "delete_authorized": False,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1",
        "gold_folder_id": "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4",
        "gold_payload_bytes": 1612,
        "gold_payload_sha256": "d6a35db7c42129569c73f19de789d871d0d285929d8eb3fe2a04d5ef03fdd6e0",
        "imputation_authorized": False,
        "manual_confirmation_required": True,
        "mime_type": "application/json",
        "mode": "ONE_EXISTING_DRIVE_GOLD_PAYLOAD_READBACK_VERIFY",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_READBACK_REVIEW_0_8_0",
        "overwrite_authorized": False,
        "persistence_config_path": "config/source_expansion.siope_client_limeira_gold_drive_persistence.json",
        "processing_authorized": False,
        "recurrence_authorized": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__d6a35db7c421__gold_v1.json",
        "replace_authorized": False,
        "review_gate": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "schedule_enabled": False,
        "semantic_scope": "DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS",
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "source_network_authorized": False,
    }
    _require(config, expected, "CONFIG")
    _expected_payload(config, root=root)
    return {
        "status": f"{PASS}_DESIGN",
        "network_called": False,
        "source_network_called": False,
        "drive_network_called": False,
        "drive_write_count": 0,
        "gold_payload_sha256": config["gold_payload_sha256"],
        "gold_payload_bytes": config["gold_payload_bytes"],
        "metric_count": 8,
        "compliance_claims_authorized": False,
        "imputation_performed": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def verify_readback(config: dict, *, root: str | Path, drive=None) -> dict:
    validate_config(config, root=root)
    expected_payload, expected_bytes = _expected_payload(config, root=root)
    expected_md5 = hashlib.md5(expected_bytes).hexdigest()  # noqa: S324

    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))

    matches = drive.find_by_name(config["gold_folder_id"], config["remote_name"])
    _require(len(matches), 1, "REMOTE_NAME_MATCH_COUNT")
    metadata = matches[0]
    _require(metadata.get("name"), config["remote_name"], "REMOTE_NAME")
    _require(metadata.get("mimeType"), config["mime_type"], "REMOTE_MIME")
    _require(str(metadata.get("size")), str(config["gold_payload_bytes"]), "REMOTE_SIZE")
    _require(metadata.get("md5Checksum"), expected_md5, "REMOTE_MD5")
    parents = metadata.get("parents") or []
    _require(config["gold_folder_id"] in parents, True, "REMOTE_PARENT")
    file_id = metadata.get("id")
    if not isinstance(file_id, str) or not file_id:
        raise GoldDriveReadbackVerificationError(f"{ERROR}_REMOTE_ID_MISSING")

    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "gold_readback.json"
        downloaded = drive.get(file_id, local)
        actual_bytes = local.read_bytes()

    _require(downloaded.get("bytes"), config["gold_payload_bytes"], "DOWNLOADED_BYTES")
    _require(downloaded.get("sha256"), config["gold_payload_sha256"], "DOWNLOADED_SHA256")
    _require(len(actual_bytes), config["gold_payload_bytes"], "READBACK_BYTES")
    _require(hashlib.sha256(actual_bytes).hexdigest(), config["gold_payload_sha256"], "READBACK_SHA256")
    _require(hashlib.md5(actual_bytes).hexdigest(), expected_md5, "READBACK_MD5")  # noqa: S324
    _require(actual_bytes, expected_bytes, "READBACK_BYTE_IDENTITY")

    try:
        parsed = json.loads(actual_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoldDriveReadbackVerificationError(f"{ERROR}_READBACK_JSON") from exc
    _require(parsed, expected_payload, "READBACK_PAYLOAD_IDENTITY")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": True,
        "source_network_called": False,
        "drive_network_called": True,
        "drive_file_download_count": 1,
        "drive_write_count": 0,
        "remote_file_id_persisted": False,
        "remote_name": config["remote_name"],
        "gold_payload_bytes": config["gold_payload_bytes"],
        "gold_payload_sha256": config["gold_payload_sha256"],
        "gold_payload_md5_verified": True,
        "byte_identity_verified": True,
        "metric_count": 8,
        "gold_contract": config["gold_contract"],
        "semantic_scope": config["semantic_scope"],
        "compliance_claims_authorized": False,
        "imputation_performed": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
