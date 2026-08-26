from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_silver_drive_persistence import (
    _build_silver_payload,
    _canonical_bytes,
)
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION"


class SilverDriveReadbackVerificationError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SilverDriveReadbackVerificationError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SilverDriveReadbackVerificationError(f"{ERROR}_{code}")


def _expected_payload(config: dict, *, root: str | Path) -> tuple[dict, bytes]:
    payload = _build_silver_payload(config, root=root)
    payload_bytes = _canonical_bytes(payload)
    _require(len(payload_bytes), config["silver_payload_bytes"], "EXPECTED_PAYLOAD_BYTES")
    _require(hashlib.sha256(payload_bytes).hexdigest(), config["silver_payload_sha256"], "EXPECTED_PAYLOAD_SHA256")
    _require(payload.get("silver_contract"), config["silver_contract"], "SILVER_CONTRACT")
    _require(payload.get("schema_key_count"), 52, "SCHEMA_COUNT")
    identity = payload.get("identity") or {}
    _require(identity.get("municipality_code"), 352690, "MUNICIPALITY")
    _require(identity.get("municipality_name"), "Limeira", "MUNICIPALITY_NAME")
    _require(identity.get("state"), "SP", "STATE")
    _require(identity.get("year"), 2024, "YEAR")
    _require(identity.get("period"), 6, "PERIOD")
    return payload, payload_bytes


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "delete_authorized": False,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_authorized": False,
        "manifest_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "manual_confirmation_required": True,
        "mime_type": "application/json",
        "mode": "ONE_EXISTING_DRIVE_SILVER_PAYLOAD_READBACK_VERIFY",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_REVIEW_0_8_0",
        "overwrite_authorized": False,
        "processing_authorized": False,
        "record_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "record_sha256": "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6",
        "recurrence_authorized": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__072283e3d9e5__silver_v1.json",
        "replace_authorized": False,
        "review_gate": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "schedule_enabled": False,
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_VALIDATED_RECORD_SILVER_V1",
        "silver_folder_id": "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo",
        "silver_payload_bytes": 2328,
        "silver_payload_sha256": "072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da",
        "software_version": "0.8.0",
        "source_bundle_sha256": "eb30b820c34a702a5850b1e246d7d29a8d86c0e84064b79b14c0308060950dbf",
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
        "silver_payload_sha256": config["silver_payload_sha256"],
        "silver_payload_bytes": config["silver_payload_bytes"],
        "gold_authorized": False,
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

    matches = drive.find_by_name(config["silver_folder_id"], config["remote_name"])
    _require(len(matches), 1, "REMOTE_NAME_MATCH_COUNT")
    metadata = matches[0]
    _require(metadata.get("name"), config["remote_name"], "REMOTE_NAME")
    _require(metadata.get("mimeType"), config["mime_type"], "REMOTE_MIME")
    _require(str(metadata.get("size")), str(config["silver_payload_bytes"]), "REMOTE_SIZE")
    _require(metadata.get("md5Checksum"), expected_md5, "REMOTE_MD5")
    parents = metadata.get("parents") or []
    _require(config["silver_folder_id"] in parents, True, "REMOTE_PARENT")
    file_id = metadata.get("id")
    if not isinstance(file_id, str) or not file_id:
        raise SilverDriveReadbackVerificationError(f"{ERROR}_REMOTE_ID_MISSING")

    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "silver_readback.json"
        downloaded = drive.get(file_id, local)
        actual_bytes = local.read_bytes()

    _require(downloaded.get("bytes"), config["silver_payload_bytes"], "DOWNLOADED_BYTES")
    _require(downloaded.get("sha256"), config["silver_payload_sha256"], "DOWNLOADED_SHA256")
    _require(len(actual_bytes), config["silver_payload_bytes"], "READBACK_BYTES")
    _require(hashlib.sha256(actual_bytes).hexdigest(), config["silver_payload_sha256"], "READBACK_SHA256")
    _require(hashlib.md5(actual_bytes).hexdigest(), expected_md5, "READBACK_MD5")  # noqa: S324
    _require(actual_bytes, expected_bytes, "READBACK_BYTE_IDENTITY")

    try:
        parsed = json.loads(actual_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SilverDriveReadbackVerificationError(f"{ERROR}_READBACK_JSON") from exc
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
        "silver_payload_bytes": config["silver_payload_bytes"],
        "silver_payload_sha256": config["silver_payload_sha256"],
        "silver_payload_md5_verified": True,
        "byte_identity_verified": True,
        "record_count": 1,
        "record_sha256": config["record_sha256"],
        "schema_key_count": 52,
        "silver_contract": config["silver_contract"],
        "gold_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
