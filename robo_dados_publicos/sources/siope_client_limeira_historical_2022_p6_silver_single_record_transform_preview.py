from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW"


class Historical2022P6SilverTransformPreviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2022P6SilverTransformPreviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2022P6SilverTransformPreviewError(f"{ERROR}_{code}")


def _normalize_name(value) -> str:  # noqa: ANN001
    text = unicodedata.normalize("NFKD", str(value).strip())
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate_config(config: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_0_8_0", "GATE")
    _require(config.get("source_id"), "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA", "SOURCE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_HISTORICAL_BRONZE_SINGLE_RECORD_SILVER_LOSSLESS_PREVIEW", "MODE")
    _require(config.get("manual_confirmation_required"), True, "MANUAL")
    _require(config.get("readback_review_gate"), "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW_0_8_0", "REVIEW_GATE")
    _require(config.get("record_embedding"), "EXACT_LOSSLESS", "EMBEDDING")
    _require(config.get("canonical_json"), True, "CANONICAL")
    _require(config.get("expected_record_count"), 1, "RECORD_COUNT")
    _require(config.get("expected_schema_key_count"), 52, "SCHEMA_COUNT")
    _require(config.get("expected_silver_payload_bytes"), 1825, "SILVER_BYTES")
    _require(config.get("expected_silver_payload_sha256"), "d8f14e5fa52cf214c837cb6a3d702f8b5a12310252045695547b289f88a03632", "SILVER_SHA")
    _require(
        config.get("record_payload_path"),
        "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "RECORD_PATH",
    )
    _require(
        config.get("manifest_payload_path"),
        "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "MANIFEST_PATH",
    )
    _require(
        config.get("expected_identity"),
        {
            "municipality_code": 352690,
            "municipality_name": "Limeira",
            "period": 6,
            "resource": "Dados_Gerais_Siope",
            "state": "SP",
            "year": 2022,
        },
        "IDENTITY_CONFIG",
    )
    _require(config.get("record_sha256"), "79b786f438d29803fe15d513f4ff17d4ab55fde1dd631f503b6752370e21b68a", "RECORD_SHA")
    _require(config.get("source_bundle_sha256"), "68b659026fe5af968864d24fba10a6883058db4a9aa700d7f65a5a09c47ab54f", "BUNDLE_SHA")
    _require(config.get("silver_contract"), "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1", "SILVER_CONTRACT")
    _require(config.get("source_network_authorized"), False, "SOURCE_NETWORK")
    _require(config.get("drive_network_authorized"), False, "DRIVE_NETWORK")
    _require(config.get("drive_write_count"), 0, "DRIVE_WRITE")
    _require(config.get("silver_payload_persistence_authorized"), False, "SILVER_PERSISTENCE")
    _require(config.get("silver_remote_write_authorized"), False, "SILVER_REMOTE_WRITE")
    _require(config.get("processing_authorized"), False, "PROCESSING")
    _require(config.get("gold_authorized"), False, "GOLD")
    _require(config.get("historical_collection_authorized"), False, "HISTORICAL_COLLECTION")
    _require(config.get("recurrence_authorized"), False, "RECURRENCE")
    _require(config.get("schedule_enabled"), False, "SCHEDULE")
    _require(config.get("next_gate"), "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW_0_8_0", "NEXT")
    _require(len(PROVEN_DADOS_GERAIS_FIELDS), 52, "ALLOWLIST_COUNT")
    return {
        "drive_network_called": False,
        "drive_write_count": 0,
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "network_called": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_payload_persisted": False,
        "silver_remote_write_authorized": False,
        "source_network_called": False,
        "status": f"{PASS}_DESIGN",
    }


def preview(config: dict, *, root: str | Path) -> dict:
    validate_config(config)
    root_path = Path(root)
    record = load_json(root_path / config["record_payload_path"])
    manifest = load_json(root_path / config["manifest_payload_path"])

    _require(set(record), set(PROVEN_DADOS_GERAIS_FIELDS), "SCHEMA")
    _require(len(record), 52, "SCHEMA_COUNT_RUNTIME")
    record_bytes = _canonical_bytes(record)
    record_sha256 = hashlib.sha256(record_bytes).hexdigest()
    _require(record_sha256, config["record_sha256"], "RECORD_HASH")

    identity = config["expected_identity"]
    _require(record.get("COD_MUNI"), identity["municipality_code"], "MUNICIPALITY_CODE")
    _require(_normalize_name(record.get("NOM_MUNI")), _normalize_name(identity["municipality_name"]), "MUNICIPALITY_NAME")
    _require(record.get("NUM_ANO"), identity["year"], "YEAR")
    _require(record.get("NUM_PERI"), identity["period"], "PERIOD")
    _require(str(record.get("SIG_UF", "")).strip().upper(), identity["state"], "STATE")

    _require(manifest.get("bronze_contract"), "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_V1", "BRONZE_CONTRACT")
    _require(manifest.get("source_id"), config["source_id"], "MANIFEST_SOURCE")
    _require(manifest.get("resource"), identity["resource"], "MANIFEST_RESOURCE")
    _require(manifest.get("municipality_code"), identity["municipality_code"], "MANIFEST_MUNICIPALITY")
    _require(manifest.get("year"), identity["year"], "MANIFEST_YEAR")
    _require(manifest.get("period"), identity["period"], "MANIFEST_PERIOD")
    _require(manifest.get("state"), identity["state"], "MANIFEST_STATE")
    _require(manifest.get("record_count"), 1, "MANIFEST_RECORD_COUNT")
    _require(manifest.get("schema_key_count"), 52, "MANIFEST_SCHEMA_COUNT")
    _require(manifest.get("record_sha256"), record_sha256, "MANIFEST_RECORD_HASH")
    _require(manifest.get("historical_collection_authorized"), False, "MANIFEST_HISTORICAL_COLLECTION")
    _require(manifest.get("processing_authorized"), False, "MANIFEST_PROCESSING")
    _require(manifest.get("recurrence_authorized"), False, "MANIFEST_RECURRENCE")

    silver_payload = {
        "data": record,
        "identity": {
            "municipality_code": identity["municipality_code"],
            "municipality_name": identity["municipality_name"],
            "period": identity["period"],
            "resource": identity["resource"],
            "state": identity["state"],
            "year": identity["year"],
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
    silver_bytes = _canonical_bytes(silver_payload)
    silver_sha256 = hashlib.sha256(silver_bytes).hexdigest()
    _require(_canonical_bytes(silver_payload["data"]), record_bytes, "LOSSLESS_EMBEDDING")
    _require(len(silver_bytes), config["expected_silver_payload_bytes"], "SILVER_BYTES_RUNTIME")
    _require(silver_sha256, config["expected_silver_payload_sha256"], "SILVER_SHA_RUNTIME")

    return {
        "drive_network_called": False,
        "drive_write_count": 0,
        "gate_id": config["gate_id"],
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "identity_verified": True,
        "lossless_record_embedding_verified": True,
        "network_called": False,
        "next_gate": config["next_gate"],
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": record_sha256,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "silver_contract": config["silver_contract"],
        "silver_payload_bytes": len(silver_bytes),
        "silver_payload_persisted": False,
        "silver_payload_sha256": silver_sha256,
        "silver_remote_write_authorized": False,
        "source_network_called": False,
        "status": PASS,
    }
