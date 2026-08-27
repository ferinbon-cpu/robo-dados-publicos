from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_VERIFICATION"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_VERIFICATION"


class Historical2022P6DriveReadbackVerificationError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2022P6DriveReadbackVerificationError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2022P6DriveReadbackVerificationError(f"{ERROR}_{code}")


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _expected_bundle(config: dict, *, root: str | Path) -> tuple[dict, bytes]:
    root_path = Path(root)
    record = load_json(root_path / config["record_payload_path"])
    manifest = load_json(root_path / config["manifest_payload_path"])
    _require(len(record), 52, "RECORD_SCHEMA_COUNT")
    _require(record.get("COD_MUNI"), 352690, "RECORD_MUNICIPALITY")
    _require(record.get("NOM_MUNI"), "Limeira", "RECORD_MUNICIPALITY_NAME")
    _require(record.get("SIG_UF"), "SP", "RECORD_STATE")
    _require(record.get("NUM_ANO"), 2022, "RECORD_YEAR")
    _require(record.get("NUM_PERI"), 6, "RECORD_PERIOD")
    record_sha256 = hashlib.sha256(_canonical_bytes(record)).hexdigest()
    _require(record_sha256, config["record_sha256"], "RECORD_SHA256")
    _require(manifest.get("record_sha256"), config["record_sha256"], "MANIFEST_RECORD_SHA256")
    _require(manifest.get("record_count"), 1, "MANIFEST_RECORD_COUNT")
    _require(manifest.get("schema_key_count"), 52, "MANIFEST_SCHEMA_COUNT")
    _require(manifest.get("year"), 2022, "MANIFEST_YEAR")
    _require(manifest.get("period"), 6, "MANIFEST_PERIOD")
    _require(manifest.get("historical_collection_authorized"), False, "MANIFEST_HISTORICAL_COLLECTION")
    _require(manifest.get("processing_authorized"), False, "MANIFEST_PROCESSING")
    _require(manifest.get("recurrence_authorized"), False, "MANIFEST_RECURRENCE")
    bundle = {
        "bronze_bundle_contract": config["bundle_contract"],
        "manifest": manifest,
        "record": record,
    }
    bundle_bytes = _canonical_bytes(bundle)
    _require(len(bundle_bytes), config["bundle_bytes"], "EXPECTED_BUNDLE_BYTES")
    _require(hashlib.sha256(bundle_bytes).hexdigest(), config["bundle_sha256"], "EXPECTED_BUNDLE_SHA256")
    _require(hashlib.md5(bundle_bytes).hexdigest(), config["bundle_md5"], "EXPECTED_BUNDLE_MD5")  # noqa: S324
    return bundle, bundle_bytes


def validate_config(config: dict, *, root: str | Path) -> dict:
    expected = {
        "bronze_folder_id": "18yR-e6I1VCiy7XqG7Zhr0vUIJF0qA_MG",
        "bundle_bytes": 2081,
        "bundle_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_DRIVE_BUNDLE_V1",
        "bundle_md5": "a018b0749a66fe1d06d926ab2256b6a2",
        "bundle_sha256": "68b659026fe5af968864d24fba10a6883058db4a9aa700d7f65a5a09c47ab54f",
        "delete_authorized": False,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "manifest_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "manual_confirmation_required": True,
        "mime_type": "application/json",
        "mode": "ONE_EXISTING_DRIVE_HISTORICAL_BRONZE_BUNDLE_READBACK_VERIFY",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW_0_8_0",
        "overwrite_authorized": False,
        "processing_authorized": False,
        "record_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "record_sha256": "79b786f438d29803fe15d513f4ff17d4ab55fde1dd631f503b6752370e21b68a",
        "recurrence_authorized": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2022_P6__352690__79b786f438d2__bundle.json",
        "replace_authorized": False,
        "review_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "schedule_enabled": False,
        "silver_authorized": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "source_network_authorized": False,
    }
    _require(config, expected, "CONFIG")
    _expected_bundle(config, root=root)
    return {
        "status": f"{PASS}_DESIGN",
        "network_called": False,
        "source_network_called": False,
        "drive_network_called": False,
        "drive_write_count": 0,
        "bundle_sha256": config["bundle_sha256"],
        "bundle_bytes": config["bundle_bytes"],
        "historical_collection_authorized": False,
        "silver_authorized": False,
        "gold_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def verify_readback(config: dict, *, root: str | Path, drive=None) -> dict:
    validate_config(config, root=root)
    expected_bundle, expected_bytes = _expected_bundle(config, root=root)
    expected_md5 = hashlib.md5(expected_bytes).hexdigest()  # noqa: S324

    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))

    matches = drive.find_by_name(config["bronze_folder_id"], config["remote_name"])
    _require(len(matches), 1, "REMOTE_NAME_MATCH_COUNT")
    metadata = matches[0]
    _require(metadata.get("name"), config["remote_name"], "REMOTE_NAME")
    _require(metadata.get("mimeType"), config["mime_type"], "REMOTE_MIME")
    _require(str(metadata.get("size")), str(config["bundle_bytes"]), "REMOTE_SIZE")
    _require(metadata.get("md5Checksum"), expected_md5, "REMOTE_MD5")
    parents = metadata.get("parents") or []
    _require(config["bronze_folder_id"] in parents, True, "REMOTE_PARENT")
    file_id = metadata.get("id")
    if not isinstance(file_id, str) or not file_id:
        raise Historical2022P6DriveReadbackVerificationError(f"{ERROR}_REMOTE_ID_MISSING")

    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "historical_2022_p6_bronze_readback.json"
        downloaded = drive.get(file_id, local)
        actual_bytes = local.read_bytes()

    _require(downloaded.get("bytes"), config["bundle_bytes"], "DOWNLOADED_BYTES")
    _require(downloaded.get("sha256"), config["bundle_sha256"], "DOWNLOADED_SHA256")
    _require(len(actual_bytes), config["bundle_bytes"], "READBACK_BYTES")
    _require(hashlib.sha256(actual_bytes).hexdigest(), config["bundle_sha256"], "READBACK_SHA256")
    _require(hashlib.md5(actual_bytes).hexdigest(), config["bundle_md5"], "READBACK_MD5")  # noqa: S324
    _require(actual_bytes, expected_bytes, "READBACK_BYTE_IDENTITY")

    try:
        parsed = json.loads(actual_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Historical2022P6DriveReadbackVerificationError(f"{ERROR}_READBACK_JSON") from exc
    _require(parsed, expected_bundle, "READBACK_BUNDLE_IDENTITY")

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
        "bundle_bytes": config["bundle_bytes"],
        "bundle_sha256": config["bundle_sha256"],
        "bundle_md5_verified": True,
        "byte_identity_verified": True,
        "record_count": 1,
        "record_sha256": config["record_sha256"],
        "schema_key_count": 52,
        "historical_collection_authorized": False,
        "silver_authorized": False,
        "gold_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
