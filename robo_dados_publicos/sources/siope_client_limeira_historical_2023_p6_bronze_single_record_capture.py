from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

from robo_dados_publicos.sources.siope_client import (
    PROVEN_DADOS_GERAIS_FIELDS,
    SiopeClient,
    SiopeClientError,
    SiopeClientPolicy,
)

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE"


class Historical2023P6BronzeCaptureError(RuntimeError):
    def __init__(self, message: str, *, request_count: int = 0):
        super().__init__(message)
        self.request_count = request_count


def _require(actual, expected, code: str, *, request_count: int = 0) -> None:
    if actual != expected:
        raise Historical2023P6BronzeCaptureError(f"{ERROR}_{code}", request_count=request_count)


def _normalize_name(value) -> str:  # noqa: ANN001
    text = unicodedata.normalize("NFKD", str(value).strip())
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _as_int(value, code: str) -> int:  # noqa: ANN001
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise Historical2023P6BronzeCaptureError(f"{ERROR}_{code}", request_count=1) from None


def validate_config(config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "ONE_REQUEST_ONE_HISTORICAL_RECORD_IMMUTABLE_BRONZE_CAPTURE",
        "manual_confirmation_required": True,
        "single_historical_record_capture_authorized": True,
        "historical_collection_authorized": False,
        "drive_persistence_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, key.upper())
    _require(config.get("query"), {"ano": 2023, "periodo": 6, "uf": "SP", "municipality_code": 352690}, "QUERY")
    _require(
        config.get("policy"),
        {"timeout_seconds": 60, "max_response_bytes": 262144, "max_attempts": 1, "follow_redirects": False, "follow_nextlink": False},
        "POLICY",
    )
    _require(
        config.get("capture"),
        {
            "expected_record_count": 1,
            "expected_schema_key_count": 52,
            "canonical_json": True,
            "raw_public_record_persistence_authorized": True,
            "persist_response_envelope": False,
            "persist_nextlink_url": False,
        },
        "CAPTURE",
    )
    _require(len(PROVEN_DADOS_GERAIS_FIELDS), 52, "ALLOWLIST_COUNT")
    return {
        "status": f"{PASS}_DESIGN",
        "network_called": False,
        "request_count": 0,
        "target_year": 2023,
        "target_period": 6,
        "single_historical_record_capture_authorized": True,
        "historical_collection_authorized": False,
        "drive_persistence_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def capture(config: dict, *, output_dir: str | Path, opener=None) -> dict:
    validate_config(config)
    q, p = config["query"], config["policy"]
    try:
        client = SiopeClient(policy=SiopeClientPolicy(**p), opener=opener)
        page = client.get_dados_gerais_page(
            ano=q["ano"],
            periodo=q["periodo"],
            uf=q["uf"],
            municipality_code=q["municipality_code"],
            select_fields=tuple(sorted(PROVEN_DADOS_GERAIS_FIELDS)),
        )
    except SiopeClientError as exc:
        raise Historical2023P6BronzeCaptureError(f"{ERROR}_{str(exc)}", request_count=exc.request_count) from None

    _require(page.status, 200, "HTTP", request_count=1)
    _require(page.content_type in {"application/json", "application/odata+json"}, True, "CONTENT_TYPE", request_count=1)
    _require(page.nextlink_present, False, "NEXTLINK", request_count=1)
    _require(len(page.records), 1, "RECORD_COUNT", request_count=1)
    record = page.records[0]
    _require(set(record), set(PROVEN_DADOS_GERAIS_FIELDS), "SCHEMA", request_count=1)
    _require(_as_int(record.get("COD_MUNI"), "COD_MUNI"), 352690, "MUNICIPALITY", request_count=1)
    _require(_normalize_name(record.get("NOM_MUNI")), "LIMEIRA", "MUNICIPALITY_NAME", request_count=1)
    _require(_as_int(record.get("NUM_ANO"), "NUM_ANO"), 2023, "YEAR", request_count=1)
    _require(_as_int(record.get("NUM_PERI"), "NUM_PERI"), 6, "PERIOD", request_count=1)
    _require(str(record.get("SIG_UF", "")).strip().upper(), "SP", "STATE", request_count=1)

    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    record_sha256 = hashlib.sha256(canonical).hexdigest()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    record_path = out / "record.json"
    manifest_path = out / "manifest.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "bronze_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_V1",
        "source_id": config["source_id"],
        "resource": "Dados_Gerais_Siope",
        "software_version": config["software_version"],
        "municipality_code": 352690,
        "year": 2023,
        "period": 6,
        "state": "SP",
        "record_count": 1,
        "schema_key_count": 52,
        "record_sha256": record_sha256,
        "response_sha256": page.response_sha256,
        "response_byte_count": page.response_byte_count,
        "validation_prerequisite_run_id": 33028313110,
        "response_envelope_persisted": False,
        "nextlink_url_persisted": False,
        "drive_persistence_authorized": False,
        "historical_collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "request_count": page.request_count,
        "resource": "Dados_Gerais_Siope",
        "response_status": page.status,
        "content_type": page.content_type,
        "value_count": 1,
        "selected_schema_exact": True,
        "selected_schema_key_count": 52,
        "record_sha256": record_sha256,
        "response_sha256": page.response_sha256,
        "response_byte_count": page.response_byte_count,
        "bronze_record_persisted": True,
        "bronze_manifest_persisted": True,
        "response_envelope_persisted": False,
        "odata_nextlink_present": False,
        "retry_performed": False,
        "redirect_followed": False,
        "single_historical_record_capture_authorized": True,
        "historical_collection_authorized": False,
        "drive_persistence_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
