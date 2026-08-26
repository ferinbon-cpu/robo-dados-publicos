from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET"
PASS = "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET"


class SiopeOfficialOlindaMinimalReadonlyGetError(RuntimeError):
    def __init__(self, message: str, *, network_called: bool = False, request_count: int = 0):
        super().__init__(message)
        self.network_called = network_called
        self.request_count = request_count


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_open(req: Request, timeout: int):
    return build_opener(_NoRedirectHandler()).open(req, timeout=timeout)


def load_config(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_CONFIG_OBJECT_REQUIRED")
    validate_design(payload)
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_CONFIG_{code}")


def _query_pairs(url: str) -> list[tuple[str, str]]:
    return parse_qsl(urlparse(url).query, keep_blank_values=True)


def validate_design(config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_DESIGN_0_8_0",
        "live_gate_id": "M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "EXACT_ONE_REQUEST_NON_LIMEIRA_READONLY_ODATA_GET",
        "expected_path": "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)",
        "resource_get_authorized_by_this_design": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "route_synthesis_or_guessing": "PROHIBITED",
        "automatic_route_promotion": "PROHIBITED",
        "next_gate_after_manual_success": "M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_REVIEW_0_8_0",
    }
    for key, value in exact.items():
        _require(config.get(key), value, key.upper())
    _require(config.get("allowed_hosts"), ["www.fnde.gov.br"], "ALLOWED_HOSTS")
    _require(config.get("expected_query_keys_in_order"), ["@Ano_Consulta", "@Num_Peri", "@Sig_UF", "$format"], "QUERY_KEYS")
    _require(
        config.get("fixed_example_semantics"),
        {"Ano_Consulta": 2023, "Num_Peri": 6, "Sig_UF": "PE", "municipality": None, "limeira": False},
        "EXAMPLE_SEMANTICS",
    )
    _require(
        config.get("limits"),
        {"max_response_bytes": 2097152, "max_schema_fields": 128, "max_schema_field_chars": 128},
        "LIMITS",
    )
    _require(
        config.get("verification_rules"),
        {
            "methods": ["GET"],
            "request_count": 1,
            "follow_redirects": False,
            "follow_odata_nextlink": False,
            "send_pilot_limeira_values": False,
            "persist_response_body": False,
            "persist_record_values": False,
            "persist_nextlink_url": False,
            "persist_query_values_in_result": False,
            "download_artifacts": False,
            "submit_forms": False,
            "authenticate": False,
            "capture_credentials": False,
            "capture_cookies": False,
            "post_request": False,
            "head_request": False,
        },
        "RULES",
    )
    _require(
        config.get("success_contract"),
        {
            "http_status": 200,
            "allowed_content_types": ["application/json", "application/odata+json"],
            "top_level_json_type": "object",
            "required_value_type": "list",
            "minimum_value_count": 1,
            "first_record_if_present_type": "object",
        },
        "SUCCESS_CONTRACT",
    )

    raw = str(config.get("exact_url", ""))
    parsed = urlparse(raw)
    if parsed.scheme != "https" or parsed.hostname != "www.fnde.gov.br":
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_CONFIG_URL_HOST")
    _require(parsed.path, config["expected_path"], "URL_PATH")
    pairs = _query_pairs(raw)
    _require([key for key, _ in pairs], config["expected_query_keys_in_order"], "URL_QUERY_KEY_ORDER")
    _require(pairs, [("@Ano_Consulta", "2023"), ("@Num_Peri", "6"), ("@Sig_UF", "'PE'"), ("$format", "json")], "URL_QUERY_VALUES")
    if "Limeira" in raw or "352690" in raw:
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_CONFIG_LIMEIRA_PROHIBITED")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_DESIGN",
        "gate_id": config["gate_id"],
        "live_gate_id": config["live_gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": config["mode"],
        "network_called": False,
        "request_count": 0,
        "fixed_non_limeira_example": True,
        "method": "GET_ONLY",
        "redirects_allowed": False,
        "odata_nextlink_follow_allowed": False,
        "response_body_persistence_allowed": False,
        "record_value_persistence_allowed": False,
        "query_value_persistence_in_result_allowed": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["live_gate_id"],
    }


def _safe_schema_keys(record: dict, *, max_fields: int, max_chars: int) -> list[str]:
    keys: list[str] = []
    for key in sorted(record):
        text = str(key)
        if not text or len(text) > max_chars:
            raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_SCHEMA_KEY_INVALID", network_called=True, request_count=1)
        keys.append(text)
        if len(keys) > max_fields:
            raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_SCHEMA_TOO_WIDE", network_called=True, request_count=1)
    return keys


def run_minimal_get(config: dict, *, opener=None) -> dict:
    validate_design(config)
    opener = opener or _default_open
    url = config["exact_url"]
    request = Request(
        url,
        headers={
            "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 (+public-transparency-research)",
            "Accept": "application/json,application/odata+json;q=0.9",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    max_bytes = int(config["limits"]["max_response_bytes"])
    try:
        response = opener(request, timeout=20)
        with response:
            final_url = str(getattr(response, "url", response.geturl()))
            if final_url != url:
                raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_REDIRECT_OR_URL_DRIFT", network_called=True, request_count=1)
            status = int(getattr(response, "status", response.getcode()))
            content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
            raw = response.read(max_bytes + 1)
    except SiopeOfficialOlindaMinimalReadonlyGetError:
        raise
    except HTTPError as exc:
        code = int(getattr(exc, "code", 0) or 0)
        if 300 <= code < 400:
            raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_REDIRECT_BLOCKED", network_called=True, request_count=1) from None
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_HTTP_{code}", network_called=True, request_count=1) from None
    except (TimeoutError, socket.timeout):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_TIMEOUT", network_called=True, request_count=1) from None
    except URLError:
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_NETWORK", network_called=True, request_count=1) from None
    except OSError:
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_NETWORK", network_called=True, request_count=1) from None

    if len(raw) > max_bytes:
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_RESPONSE_TOO_LARGE", network_called=True, request_count=1)
    if status != 200:
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_HTTP_STATUS", network_called=True, request_count=1)
    if content_type not in set(config["success_contract"]["allowed_content_types"]):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_CONTENT_TYPE", network_called=True, request_count=1)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_INVALID_JSON", network_called=True, request_count=1) from None
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_TOP_LEVEL_OBJECT_REQUIRED", network_called=True, request_count=1)
    value = payload.get("value")
    if not isinstance(value, list):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_VALUE_LIST_REQUIRED", network_called=True, request_count=1)
    if len(value) < int(config["success_contract"]["minimum_value_count"]):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_VALUE_EMPTY", network_called=True, request_count=1)
    if not isinstance(value[0], dict):
        raise SiopeOfficialOlindaMinimalReadonlyGetError(f"{ERROR}_FIRST_RECORD_OBJECT_REQUIRED", network_called=True, request_count=1)

    schema_keys = _safe_schema_keys(
        value[0],
        max_fields=int(config["limits"]["max_schema_fields"]),
        max_chars=int(config["limits"]["max_schema_field_chars"]),
    )
    return {
        "status": PASS,
        "gate_id": config["live_gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": config["mode"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "request_count": 1,
        "fixed_non_limeira_example": True,
        "pilot_limeira_values_sent": False,
        "response_status": status,
        "content_type": content_type,
        "response_byte_count": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "top_level_json_object": True,
        "value_list_present": True,
        "value_count": len(value),
        "first_record_object": True,
        "first_record_schema_keys": schema_keys,
        "first_record_schema_key_count": len(schema_keys),
        "odata_context_present": "@odata.context" in payload,
        "odata_nextlink_present": "@odata.nextLink" in payload,
        "redirect_followed": False,
        "odata_nextlink_followed": False,
        "response_body_persisted": False,
        "record_values_persisted": False,
        "nextlink_url_persisted": False,
        "query_values_persisted_in_result": False,
        "artifact_downloaded": False,
        "form_submission": False,
        "post_request_performed": False,
        "head_request_performed": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "automatic_route_promotion": False,
        "ongoing_resource_get_authorized": False,
        "manual_single_get_authorization_consumed": True,
        "next_gate": config["next_gate_after_manual_success"],
    }
