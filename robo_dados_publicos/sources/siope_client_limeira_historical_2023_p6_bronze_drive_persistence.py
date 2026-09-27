from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE"


class Historical2023P6DrivePersistenceError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2023P6DrivePersistenceError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2023P6DrivePersistenceError(f"{ERROR}_{code}")


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _canonical_sha256(payload: dict) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "bronze_folder_id": "18yR-e6I1VCiy7XqG7Zhr0vUIJF0qA_MG",
        "bundle_bytes": 2086,
        "bundle_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_DRIVE_BUNDLE_V1",
        "bundle_sha256": "929a999672343b0e423283dcbd8f1ba797f9f924cecaee00b70b37b312ec2dfc",
        "delete_authorized": False,
        "drive_write_count": 1,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_0_8_0",
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "manifest_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "manual_confirmation_required": True,
        "mime_type": "application/json",
        "mode": "ONE_IMMUTABLE_DRIVE_HISTORICAL_BRONZE_BUNDLE_CREATE",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "overwrite_authorized": False,
        "processing_authorized": False,
        "record_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "record_sha256": "8b63fd15413c3ab9ca5f82749ea5d89e5a1c92b06e7b80cb6def7af60b769919",
        "recurrence_authorized": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2023_P6__352690__8b63fd15413c__bundle.json",
        "replace_authorized": False,
        "review_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW_0_8_0",
        "schedule_enabled": False,
        "silver_authorized": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "source_network_authorized": False,
    }
    _require(config, expected, "CONFIG")

    root_path = Path(root)
    record = load_json(root_path / config["record_payload_path"])
    manifest = load_json(root_path / config["manifest_payload_path"])

    _require(len(record), 52, "RECORD_SCHEMA_COUNT")
    _require(record.get("COD_MUNI"), 352690, "RECORD_MUNICIPALITY")
    _require(record.get("NOM_MUNI"), "Limeira", "RECORD_MUNICIPALITY_NAME")
    _require(record.get("SIG_UF"), "SP", "RECORD_STATE")
    _require(record.get("NUM_ANO"), 2023, "RECORD_YEAR")
    _require(record.get("NUM_PERI"), 6, "RECORD_PERIOD")
    _require(_canonical_sha256(record), config["record_sha256"], "RECORD_SHA256")

    _require(manifest.get("record_sha256"), config["record_sha256"], "MANIFEST_RECORD_SHA")
    _require(manifest.get("record_count"), 1, "MANIFEST_RECORD_COUNT")
    _require(manifest.get("schema_key_count"), 52, "MANIFEST_SCHEMA_COUNT")
    _require(manifest.get("municipality_code"), 352690, "MANIFEST_MUNICIPALITY")
    _require(manifest.get("state"), "SP", "MANIFEST_STATE")
    _require(manifest.get("year"), 2023, "MANIFEST_YEAR")
    _require(manifest.get("period"), 6, "MANIFEST_PERIOD")
    _require(manifest.get("drive_persistence_authorized"), False, "MANIFEST_DRIVE")
    _require(manifest.get("historical_collection_authorized"), False, "MANIFEST_HISTORICAL_COLLECTION")
    _require(manifest.get("processing_authorized"), False, "MANIFEST_PROCESSING")
    _require(manifest.get("recurrence_authorized"), False, "MANIFEST_RECURRENCE")

    bundle = {
        "bronze_bundle_contract": config["bundle_contract"],
        "manifest": manifest,
        "record": record,
    }
    bundle_bytes = _canonical_bytes(bundle)
    _require(len(bundle_bytes), config["bundle_bytes"], "BUNDLE_BYTES")
    _require(hashlib.sha256(bundle_bytes).hexdigest(), config["bundle_sha256"], "BUNDLE_SHA256")
    return {
        "status": f"{PASS}_DESIGN",
        "network_called": False,
        "source_network_called": False,
        "drive_write_count": 0,
        "bundle_sha256": config["bundle_sha256"],
        "bundle_bytes": config["bundle_bytes"],
        "historical_collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def persist_bundle(config: dict, *, root: str | Path, drive=None) -> dict:
    validate_config(config, root=root)
    root_path = Path(root)
    record = load_json(root_path / config["record_payload_path"])
    manifest = load_json(root_path / config["manifest_payload_path"])
    bundle = {
        "bronze_bundle_contract": config["bundle_contract"],
        "manifest": manifest,
        "record": record,
    }
    bundle_bytes = _canonical_bytes(bundle)
    bundle_sha256 = hashlib.sha256(bundle_bytes).hexdigest()
    bundle_md5 = hashlib.md5(bundle_bytes).hexdigest()  # noqa: S324
    _require(bundle_sha256, config["bundle_sha256"], "LIVE_BUNDLE_SHA256")
    _require(len(bundle_bytes), config["bundle_bytes"], "LIVE_BUNDLE_BYTES")

    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))

    existing = drive.find_by_name(config["bronze_folder_id"], config["remote_name"])
    if existing:
        raise Historical2023P6DrivePersistenceError(f"{ERROR}_REMOTE_NAME_COLLISION")

    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "historical_bronze_bundle.json"
        local.write_bytes(bundle_bytes)
        uploaded = drive.put(local, config["remote_name"], config["bronze_folder_id"], config["mime_type"])

    _require(uploaded.get("name"), config["remote_name"], "REMOTE_NAME")
    _require(uploaded.get("mimeType"), config["mime_type"], "REMOTE_MIME")
    _require(str(uploaded.get("size")), str(config["bundle_bytes"]), "REMOTE_SIZE")
    _require(uploaded.get("md5Checksum"), bundle_md5, "REMOTE_MD5")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": True,
        "source_network_called": False,
        "drive_network_called": True,
        "drive_write_count": 1,
        "drive_create_only": True,
        "remote_file_id_persisted": False,
        "remote_name": config["remote_name"],
        "bundle_sha256": bundle_sha256,
        "bundle_md5_verified": True,
        "bundle_bytes": len(bundle_bytes),
        "record_sha256": config["record_sha256"],
        "record_count": 1,
        "schema_key_count": 52,
        "historical_collection_authorized": False,
        "silver_authorized": False,
        "gold_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
