from __future__ import annotations

import unicodedata

from robo_dados_publicos.sources.siope_client import (
    PROVEN_DADOS_GERAIS_FIELDS,
    SiopeClient,
    SiopeClientError,
    SiopeClientPolicy,
)

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION"


class SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError(RuntimeError):
    def __init__(self, message: str, *, request_count: int = 0):
        super().__init__(message)
        self.request_count = request_count


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError(f"{ERROR}_{code}")


def _normalize_name(value) -> str:  # noqa: ANN001
    text = unicodedata.normalize("NFKD", str(value).strip())
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _as_int(value, code: str) -> int:  # noqa: ANN001
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError(
            f"{ERROR}_{code}", request_count=1
        ) from None


def validate_config(config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "ONE_REQUEST_GENERIC_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_52_FIELD_SCHEMA_VALIDATION",
        "manual_confirmation_required": True,
        "historical_collection_authorized": False,
        "collection_authorized": False,
        "persistence_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, key.upper())
    _require(config.get("query"), {"ano": 2021, "periodo": 6, "uf": "SP", "municipality_code": 352690}, "QUERY")
    _require(config.get("policy"), {
        "timeout_seconds": 60,
        "max_response_bytes": 262144,
        "max_attempts": 1,
        "follow_redirects": False,
        "follow_nextlink": False,
    }, "POLICY")
    _require(config.get("success_contract"), {
        "response_status": 200,
        "allowed_content_types": ["application/json", "application/odata+json"],
        "value_count": 1,
        "selected_schema_key_count": 52,
        "selected_schema_exact": True,
        "all_records_match_identity": True,
        "odata_nextlink_present": False,
    }, "SUCCESS_CONTRACT")
    _require(len(PROVEN_DADOS_GERAIS_FIELDS), 52, "PROVEN_SCHEMA_ALLOWLIST_COUNT")
    return {
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": config["mode"],
        "network_called": False,
        "request_count": 0,
        "generic_client_required": True,
        "proven_schema_allowlist_count": 52,
        "target_year": 2021,
        "target_period": 6,
        "historical_collection_authorized": False,
        "collection_authorized": False,
        "persistence_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["gate_id"],
    }


def run_validation(config: dict, *, opener=None) -> dict:
    validate_config(config)
    q = config["query"]
    p = config["policy"]
    select_fields = tuple(sorted(PROVEN_DADOS_GERAIS_FIELDS))
    try:
        client = SiopeClient(
            policy=SiopeClientPolicy(
                timeout_seconds=p["timeout_seconds"],
                max_response_bytes=p["max_response_bytes"],
                max_attempts=p["max_attempts"],
                follow_redirects=p["follow_redirects"],
                follow_nextlink=p["follow_nextlink"],
            ),
            opener=opener,
        )
        page = client.get_dados_gerais_page(
            ano=q["ano"],
            periodo=q["periodo"],
            uf=q["uf"],
            municipality_code=q["municipality_code"],
            select_fields=select_fields,
        )
    except SiopeClientError as exc:
        raise SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError(
            f"{ERROR}_{str(exc)}", request_count=exc.request_count
        ) from None

    allowed_types = set(config["success_contract"]["allowed_content_types"])
    if page.status != 200 or page.content_type not in allowed_types or len(page.records) != 1:
        raise SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError(
            f"{ERROR}_RESPONSE_CONTRACT", request_count=1
        )
    record = page.records[0]
    if set(record) != PROVEN_DADOS_GERAIS_FIELDS:
        raise SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError(
            f"{ERROR}_FULL_SCHEMA_DRIFT", request_count=1
        )
    if (
        _as_int(record.get("COD_MUNI"), "MUNICIPALITY_CODE_INVALID") != 352690
        or _normalize_name(record.get("NOM_MUNI")) != "LIMEIRA"
        or _as_int(record.get("NUM_ANO"), "YEAR_INVALID") != 2021
        or _as_int(record.get("NUM_PERI"), "PERIOD_INVALID") != 6
        or str(record.get("SIG_UF", "")).strip().upper() != "SP"
    ):
        raise SiopeClientLimeiraHistorical2021P6FullSchemaReadonlyValidationError(
            f"{ERROR}_IDENTITY_MISMATCH", request_count=1
        )

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": config["mode"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "request_count": page.request_count,
        "generic_client_used": True,
        "resource": "Dados_Gerais_Siope",
        "response_status": page.status,
        "content_type": page.content_type,
        "response_byte_count": page.response_byte_count,
        "response_sha256": page.response_sha256,
        "odata_context_present": page.odata_context_present,
        "odata_nextlink_present": page.nextlink_present,
        "odata_nextlink_followed": False,
        "redirect_followed": False,
        "retry_performed": False,
        "value_count": len(page.records),
        "proven_schema_allowlist_count": len(PROVEN_DADOS_GERAIS_FIELDS),
        "selected_schema_exact": True,
        "selected_schema_key_count": len(record),
        "all_records_match_municipality_code": True,
        "all_records_match_municipality_name": True,
        "all_records_match_year": True,
        "all_records_match_period": True,
        "all_records_match_state": True,
        "response_body_persisted": False,
        "record_values_persisted": False,
        "query_values_persisted_in_result": False,
        "nextlink_url_persisted": False,
        "historical_collection_authorized": False,
        "collection_authorized": False,
        "persistence_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "manual_single_historical_period_validation_authorization_consumed": True,
        "next_gate": config["next_gate"],
    }
