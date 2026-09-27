from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_PERSISTENCE"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_PERSISTENCE"


class HistoricalSilverDrivePersistenceError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalSilverDrivePersistenceError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalSilverDrivePersistenceError(f"{ERROR}_{code}")


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _build_silver_payload(config: dict, *, root: str | Path) -> dict:
    root_path = Path(root)
    record = load_json(root_path / config["record_payload_path"])
    manifest = load_json(root_path / config["manifest_payload_path"])

    _require(set(record), set(PROVEN_DADOS_GERAIS_FIELDS), "SCHEMA")
    _require(len(record), 52, "SCHEMA_COUNT")
    record_sha256 = hashlib.sha256(_canonical_bytes(record)).hexdigest()
    _require(record_sha256, config["record_sha256"], "RECORD_SHA256")
    _require(record.get("COD_MUNI"), 352690, "MUNICIPALITY")
    _require(record.get("NOM_MUNI"), "Limeira", "MUNICIPALITY_NAME")
    _require(record.get("SIG_UF"), "SP", "STATE")
    _require(record.get("NUM_ANO"), 2023, "YEAR")
    _require(record.get("NUM_PERI"), 6, "PERIOD")

    _require(manifest.get("bronze_contract"), "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_V1", "BRONZE_CONTRACT")
    _require(manifest.get("record_sha256"), record_sha256, "MANIFEST_RECORD_SHA")
    _require(manifest.get("record_count"), 1, "MANIFEST_RECORD_COUNT")
    _require(manifest.get("schema_key_count"), 52, "MANIFEST_SCHEMA_COUNT")
    _require(manifest.get("municipality_code"), 352690, "MANIFEST_MUNICIPALITY")
    _require(manifest.get("state"), "SP", "MANIFEST_STATE")
    _require(manifest.get("year"), 2023, "MANIFEST_YEAR")
    _require(manifest.get("period"), 6, "MANIFEST_PERIOD")
    _require(manifest.get("historical_collection_authorized"), False, "MANIFEST_HISTORICAL_COLLECTION")
    _require(manifest.get("drive_persistence_authorized"), False, "MANIFEST_DRIVE_PERSISTENCE")
    _require(manifest.get("processing_authorized"), False, "MANIFEST_PROCESSING")
    _require(manifest.get("recurrence_authorized"), False, "MANIFEST_RECURRENCE")

    return {
        "data": record,
        "identity": {
            "municipality_code": 352690,
            "municipality_name": "Limeira",
            "period": 6,
            "resource": "Dados_Gerais_Siope",
            "state": "SP",
            "year": 2023,
        },
        "provenance": {
            "bronze_contract": manifest["bronze_contract"],
            "record_sha256": record_sha256,
            "source_bundle_sha256": config["source_bundle_sha256"],
            "source_id": config["source_id"],
        },
        "schema_key_count": 52,
        "silver_contract": config["silver_contract"],
        "software_version": config["software_version"],
    }


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "create_only": True,
        "delete_authorized": False,
        "drive_network_authorized": True,
        "drive_write_count": 1,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_PERSISTENCE_0_8_0",
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "manifest_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "manual_confirmation_required": True,
        "mime_type": "application/json",
        "mode": "ONE_VALIDATED_HISTORICAL_SILVER_CREATE_ONLY",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "overwrite_authorized": False,
        "processing_authorized": False,
        "record_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "record_sha256": "8b63fd15413c3ab9ca5f82749ea5d89e5a1c92b06e7b80cb6def7af60b769919",
        "recurrence_authorized": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2023_P6__352690__6d5c6a96f7a0__silver_v1.json",
        "replace_authorized": False,
        "review_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW_0_8_0",
        "schedule_enabled": False,
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1",
        "silver_folder_id": "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo",
        "silver_payload_bytes": 1830,
        "silver_payload_sha256": "6d5c6a96f7a0b57b06ad6a6b7078a46ba58ef5fd1242f08c3de8c7aa5f2c87fb",
        "software_version": "0.8.0",
        "source_bundle_sha256": "929a999672343b0e423283dcbd8f1ba797f9f924cecaee00b70b37b312ec2dfc",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "source_network_authorized": False,
    }
    _require(config, expected, "CONFIG_DRIFT")
    payload = _build_silver_payload(config, root=root)
    payload_bytes = _canonical_bytes(payload)
    _require(len(payload_bytes), config["silver_payload_bytes"], "PAYLOAD_BYTES")
    _require(hashlib.sha256(payload_bytes).hexdigest(), config["silver_payload_sha256"], "PAYLOAD_SHA256")
    return {
        "drive_network_called": False,
        "drive_write_count": 0,
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "network_called": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_payload_bytes": len(payload_bytes),
        "silver_payload_persisted": False,
        "silver_payload_sha256": config["silver_payload_sha256"],
        "source_network_called": False,
        "status": f"{PASS}_DESIGN",
    }


def persist(config: dict, *, root: str | Path, drive=None) -> dict:
    validate_config(config, root=root)
    payload = _build_silver_payload(config, root=root)
    payload_bytes = _canonical_bytes(payload)
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    payload_md5 = hashlib.md5(payload_bytes).hexdigest()  # noqa: S324
    _require(payload_sha256, config["silver_payload_sha256"], "LIVE_PAYLOAD_SHA256")
    _require(len(payload_bytes), config["silver_payload_bytes"], "LIVE_PAYLOAD_BYTES")

    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))

    existing = drive.find_by_name(config["silver_folder_id"], config["remote_name"])
    if existing:
        raise HistoricalSilverDrivePersistenceError(f"{ERROR}_REMOTE_NAME_COLLISION")

    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "historical_silver_payload.json"
        local.write_bytes(payload_bytes)
        uploaded = drive.put(local, config["remote_name"], config["silver_folder_id"], config["mime_type"])

    _require(uploaded.get("name"), config["remote_name"], "REMOTE_NAME")
    _require(uploaded.get("mimeType"), config["mime_type"], "REMOTE_MIME")
    _require(str(uploaded.get("size")), str(config["silver_payload_bytes"]), "REMOTE_SIZE")
    _require(uploaded.get("md5Checksum"), payload_md5, "REMOTE_MD5")

    return {
        "drive_create_only": True,
        "drive_network_called": True,
        "drive_write_count": 1,
        "gate_id": config["gate_id"],
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "network_called": True,
        "next_gate": config["next_gate"],
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["record_sha256"],
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": config["remote_name"],
        "schedule_enabled": False,
        "schema_key_count": 52,
        "silver_contract": config["silver_contract"],
        "silver_payload_bytes": len(payload_bytes),
        "silver_payload_md5_verified": True,
        "silver_payload_persisted": True,
        "silver_payload_sha256": payload_sha256,
        "source_network_called": False,
        "status": PASS,
    }
