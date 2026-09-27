from __future__ import annotations

import hashlib
import json
import socket
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET"
PASS = "PASS_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET"
REQUEST_TIMEOUT_SECONDS = 60


class SiopeOfficialOlindaLimeiraPilotReadonlyGetError(RuntimeError):
    def __init__(self, message: str, *, network_called: bool = False, request_count: int = 0):
        super().__init__(message)
        self.network_called = network_called
        self.request_count = request_count


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_open(req: Request, timeout: int):
    return build_opener(_NoRedirectHandler()).open(req, timeout=timeout)


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(f"{ERROR}_CONFIG_{code}")


def _query_pairs(url: str) -> list[tuple[str, str]]:
    return parse_qsl(urlparse(url).query, keep_blank_values=True)


def _urlerror_is_timeout(exc: URLError) -> bool:
    reason = getattr(exc, "reason", None)
    return isinstance(reason, (TimeoutError, socket.timeout))


def load_config(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(f"{ERROR}_CONFIG_OBJECT_REQUIRED")
    validate_design(payload)
    return payload


def validate_design(config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_DESIGN_0_8_0",
        "live_gate_id": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "EXACT_ONE_REQUEST_LIMEIRA_READONLY_ODATA_FILTERED_SELECTED_GET",
        "expected_path": "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)",
        "resource_get_authorized_by_this_design": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "route_synthesis_or_guessing": "PROHIBITED",
        "automatic_route_promotion": "PROHIBITED",
        "next_gate_after_manual_success": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, key.upper())
    _require(config.get("allowed_hosts"), ["www.fnde.gov.br"], "ALLOWED_HOSTS")
    _require(
        config.get("expected_query_keys_in_order"),
        ["@Ano_Consulta", "@Num_Peri", "@Sig_UF", "$filter", "$select", "$format"],
        "QUERY_KEYS",
    )
    _require(
        config.get("pilot_semantics"),
        {"Ano_Consulta": 2024, "Num_Peri": 6, "Sig_UF": "SP", "municipality": "Limeira", "municipality_code": "352690"},
        "PILOT_SEMANTICS",
    )
    selected_fields = ["COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"]
    _require(config.get("selected_fields"), selected_fields, "SELECTED_FIELDS")
    _require(
        config.get("limits"),
        {"max_response_bytes": 65536, "max_value_count": 8, "max_schema_fields": 5, "max_schema_field_chars": 64},
        "LIMITS",
    )
    _require(
        config.get("verification_rules"),
        {
            "methods": ["GET"],
            "request_count": 1,
            "follow_redirects": False,
            "follow_odata_nextlink": False,
            "send_only_exact_limeira_pilot_values": True,
            "inspect_record_values_transiently_for_identity": True,
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
            "maximum_value_count": 8,
            "record_type": "object",
            "exact_selected_schema_required": True,
            "all_records_must_match_pilot_identity": True,
            "odata_nextlink_must_be_absent": True,
        },
        "SUCCESS_CONTRACT",
    )

    raw = str(config.get("exact_url", ""))
    parsed = urlparse(raw)
    if parsed.scheme != "https" or parsed.hostname != "www.fnde.gov.br":
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(f"{ERROR}_CONFIG_URL_HOST")
    _require(parsed.path, config["expected_path"], "URL_PATH")
    pairs = _query_pairs(raw)
    _require([key for key, _ in pairs], config["expected_query_keys_in_order"], "URL_QUERY_KEY_ORDER")
    _require(
        pairs,
        [
            ("@Ano_Consulta", "2024"),
            ("@Num_Peri", "6"),
            ("@Sig_UF", "'SP'"),
            ("$filter", "COD_MUNI eq 352690"),
            ("$select", "COD_MUNI,NOM_MUNI,NUM_ANO,NUM_PERI,SIG_UF"),
            ("$format", "json"),
        ],
        "URL_QUERY_VALUES",
    )
    if "%20" not in raw or "+" in raw:
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(f"{ERROR}_CONFIG_FILTER_ENCODING")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_DESIGN",
        "gate_id": config["gate_id"],
        "live_gate_id": config["live_gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": config["mode"],
        "network_called": False,
        "request_count": 0,
        "pilot_limeira_values_would_be_sent": True,
        "server_side_filter_required": True,
        "server_side_select_required": True,
        "selected_field_count": len(selected_fields),
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


def _normalize_name(value) -> str:  # noqa: ANN001
    text = unicodedata.normalize("NFKD", str(value).strip())
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _as_int(value, code: str) -> int:  # noqa: ANN001
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_{code}", network_called=True, request_count=1
        ) from None


def run_pilot_get(config: dict, *, opener=None) -> dict:
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
        response = opener(request, timeout=REQUEST_TIMEOUT_SECONDS)
        with response:
            final_url = str(getattr(response, "url", response.geturl()))
            if final_url != url:
                raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                    f"{ERROR}_REDIRECT_OR_URL_DRIFT", network_called=True, request_count=1
                )
            status = int(getattr(response, "status", response.getcode()))
            content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
            raw = response.read(max_bytes + 1)
    except SiopeOfficialOlindaLimeiraPilotReadonlyGetError:
        raise
    except HTTPError as exc:
        code = int(getattr(exc, "code", 0) or 0)
        if 300 <= code < 400:
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_REDIRECT_BLOCKED", network_called=True, request_count=1
            ) from None
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_HTTP_{code}", network_called=True, request_count=1
        ) from None
    except (TimeoutError, socket.timeout):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_TIMEOUT", network_called=True, request_count=1
        ) from None
    except URLError as exc:
        code = "TIMEOUT" if _urlerror_is_timeout(exc) else "NETWORK"
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_{code}", network_called=True, request_count=1
        ) from None
    except OSError:
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_NETWORK", network_called=True, request_count=1
        ) from None

    if len(raw) > max_bytes:
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_RESPONSE_TOO_LARGE", network_called=True, request_count=1
        )
    if status != 200:
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_HTTP_STATUS", network_called=True, request_count=1
        )
    if content_type not in set(config["success_contract"]["allowed_content_types"]):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_CONTENT_TYPE", network_called=True, request_count=1
        )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_INVALID_JSON", network_called=True, request_count=1
        ) from None
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_TOP_LEVEL_OBJECT_REQUIRED", network_called=True, request_count=1
        )
    value = payload.get("value")
    if not isinstance(value, list):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_VALUE_LIST_REQUIRED", network_called=True, request_count=1
        )
    min_count = int(config["success_contract"]["minimum_value_count"])
    max_count = int(config["success_contract"]["maximum_value_count"])
    if not (min_count <= len(value) <= max_count):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_VALUE_COUNT", network_called=True, request_count=1
        )
    if "@odata.nextLink" in payload:
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
            f"{ERROR}_UNEXPECTED_NEXTLINK", network_called=True, request_count=1
        )

    selected = set(config["selected_fields"])
    for record in value:
        if not isinstance(record, dict):
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_RECORD_OBJECT_REQUIRED", network_called=True, request_count=1
            )
        if set(record) != selected:
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_SELECT_SCHEMA_DRIFT", network_called=True, request_count=1
            )
        if _as_int(record.get("COD_MUNI"), "MUNICIPALITY_CODE_INVALID") != 352690:
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_MUNICIPALITY_CODE_MISMATCH", network_called=True, request_count=1
            )
        if _normalize_name(record.get("NOM_MUNI")) != "LIMEIRA":
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_MUNICIPALITY_NAME_MISMATCH", network_called=True, request_count=1
            )
        if _as_int(record.get("NUM_ANO"), "YEAR_INVALID") != 2024:
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_YEAR_MISMATCH", network_called=True, request_count=1
            )
        if _as_int(record.get("NUM_PERI"), "PERIOD_INVALID") != 6:
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_PERIOD_MISMATCH", network_called=True, request_count=1
            )
        if str(record.get("SIG_UF", "")).strip().upper() != "SP":
            raise SiopeOfficialOlindaLimeiraPilotReadonlyGetError(
                f"{ERROR}_STATE_MISMATCH", network_called=True, request_count=1
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
        "pilot_limeira_values_sent": True,
        "response_status": status,
        "content_type": content_type,
        "response_byte_count": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "top_level_json_object": True,
        "value_list_present": True,
        "value_count": len(value),
        "selected_schema_exact": True,
        "selected_schema_key_count": len(selected),
        "all_records_match_municipality_code": True,
        "all_records_match_municipality_name": True,
        "all_records_match_year": True,
        "all_records_match_period": True,
        "all_records_match_state": True,
        "odata_context_present": "@odata.context" in payload,
        "odata_nextlink_present": False,
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
        "manual_single_limeira_pilot_authorization_consumed": True,
        "next_gate": config["next_gate_after_manual_success"],
    }
