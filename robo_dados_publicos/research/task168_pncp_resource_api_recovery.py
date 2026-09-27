from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import (
    Task167Stop,
    fetch_route,
    sanitize_payload,
    validate_detail_identity,
)


class Task168Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task168Stop(code)


def _fold(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()


def load_config(path: str | Path) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK168_PNCP_RESOURCE_API_RECOVERY_V1", "TASK168_CONFIG_SCHEMA")
    _stop(obj["authorization"]["scope"] == "PNCP_LIVE_READ_DISCOVERY_ONLY", "TASK168_AUTH_SCOPE")
    _stop(obj["authorization"]["new_per_route_authorization_required"] is False, "TASK168_AUTH_REUSE")
    _stop(obj["source"]["resourceApiBase"] == "https://pncp.gov.br/api/pncp", "TASK168_RESOURCE_BASE")
    _stop(obj["source"]["retryMax"] == 0, "TASK168_RETRY")
    _stop(obj["source"]["redirectsMax"] == 0, "TASK168_REDIRECT")
    _stop(obj["preflight"]["url"] == "https://pncp.gov.br/api/pncp/v1/modalidades?statusAtivo=true", "TASK168_PREFLIGHT_URL")
    _stop(obj["requestBudget"]["totalMaxIfHealthy"] == 7, "TASK168_REQUEST_BUDGET")
    _stop(obj["requestBudget"]["totalMaxIfPreflightUnavailable"] == 1, "TASK168_PREFLIGHT_STOP_BUDGET")
    _stop(obj["fallback"]["htmlDomJsReverseEngineeringAuthorized"] is False, "TASK168_NO_REVERSE_ENGINEERING")
    _stop(obj["persistence"]["rawPayloadGit"] is False, "TASK168_RAW_GIT")
    _stop(obj["persistence"]["rawPayloadDrive"] is False, "TASK168_RAW_DRIVE")
    _stop(obj["persistence"]["rawPayloadWorkflowArtifact"] is False, "TASK168_RAW_ARTIFACT")
    return obj


def sanitize_preflight(payload: Any, required_id: int, required_name_contains: str) -> dict[str, Any]:
    _stop(isinstance(payload, list), "TASK168_PREFLIGHT_SCHEMA")
    selected = []
    found = None
    for row in payload:
        _stop(isinstance(row, dict), "TASK168_PREFLIGHT_ROW_SCHEMA")
        item = {
            key: row.get(key)
            for key in ("id", "nome", "statusAtivo")
            if key in row and isinstance(row.get(key), (str, int, float, bool, type(None)))
        }
        selected.append(item)
        if row.get("id") == required_id:
            found = row

    _stop(found is not None, "TASK168_REQUIRED_MODALITY_MISSING")
    _stop(
        _fold(required_name_contains) in _fold(found.get("nome")),
        "TASK168_REQUIRED_MODALITY_NAME_MISMATCH",
    )
    _stop(found.get("statusAtivo") is True, "TASK168_REQUIRED_MODALITY_INACTIVE")

    return {
        "shape": "LIST",
        "count": len(payload),
        "required_modality": {
            "id": found.get("id"),
            "nome": found.get("nome"),
            "statusAtivo": found.get("statusAtivo"),
        },
        "selected": selected,
    }


def build_target_url(config: dict[str, Any], target: dict[str, Any], route: dict[str, Any]) -> str:
    return config["source"]["origin"] + route["path"].format(
        ano=target["ano"],
        sequencial=target["sequencial"],
    )


def _as_rows(payload: Any, code: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return [payload]
    _stop(isinstance(payload, list), code)
    _stop(all(isinstance(row, dict) for row in payload), code)
    return payload


def validate_cross_route_control_identity(payload: Any, target: dict[str, Any], route_id: str) -> dict[str, Any]:
    rows = _as_rows(payload, f"TASK168_{route_id}_SCHEMA")
    observed = []
    for row in rows:
        for key in ("numeroControlePNCPCompra", "numeroControlePncpCompra"):
            if key in row and row.get(key) not in (None, ""):
                value = str(row.get(key))
                observed.append(value)
                _stop(
                    value == target["numeroControlePNCP"],
                    f"TASK168_{route_id}_CONTROL_IDENTITY_MISMATCH",
                )
    return {
        "identity_field_observations": observed,
        "identity_confirmed_by_payload_field": bool(observed),
    }


def sanitize_list_or_object(route_id: str, payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        working = [payload]
        observed_shape = "OBJECT"
    else:
        _stop(isinstance(payload, list), f"TASK168_{route_id}_SCHEMA")
        working = payload
        observed_shape = "LIST"

    if route_id == "BUDGET_SOURCES":
        # The TASK 167 sanitizer expects a list and preserves only selected structural/budget signals.
        sanitized = sanitize_payload("BUDGET_SOURCES", working)
    elif route_id == "LINKED_CONTRACTS":
        sanitized = sanitize_payload("LINKED_CONTRACTS", working)
    else:
        raise Task168Stop(f"TASK168_UNEXPECTED_ROUTE_{route_id}")
    sanitized["observed_shape"] = observed_shape
    return sanitized


def execute(config: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "TASK168_PNCP_RESOURCE_API_RECOVERY_RESULT_V1",
        "authorization_scope": config["authorization"]["scope"],
        "preflight": None,
        "targets": [],
        "request_count": 0,
        "raw_payload_persisted": False,
        "pncp_no_data_created": False,
        "payment_inference_from_pncp": "FORBIDDEN",
        "financial_identity_auto_promotion": "FORBIDDEN",
        "transaction_identity_auto_promotion": "FORBIDDEN",
    }

    meta, payload = fetch_route(
        config["preflight"]["url"],
        int(config["source"]["timeoutSeconds"]),
        int(config["source"]["maxBytesPerRoute"]),
    )
    result["request_count"] += 1
    preflight: dict[str, Any] = {"id": config["preflight"]["id"], **meta}

    if payload is None:
        preflight["status"] = "SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
        result["preflight"] = preflight
        result["status"] = "STOP_RESOURCE_API_PREFLIGHT_UNAVAILABLE"
        result["target_routes_attempted"] = 0
        result["next_action"] = "OFFICIAL_MACHINE_READABLE_FALLBACK_DOCUMENTATION"
        return result

    try:
        preflight["sanitized"] = sanitize_preflight(
            payload,
            int(config["preflight"]["requiredModalityId"]),
            str(config["preflight"]["requiredModalityNameContains"]),
        )
        preflight["status"] = "PASS_RESOURCE_API_HEALTHY"
    except Exception as exc:
        preflight["status"] = "STOP_PREFLIGHT_SCHEMA_OR_DOMAIN_IDENTITY"
        preflight["validation_error"] = f"{type(exc).__name__}:{str(exc)}"
        result["preflight"] = preflight
        result["status"] = "STOP_RESOURCE_API_PREFLIGHT_INVALID"
        result["target_routes_attempted"] = 0
        result["next_action"] = "OFFICIAL_MACHINE_READABLE_FALLBACK_DOCUMENTATION"
        return result

    result["preflight"] = preflight

    for target in config["targets"]:
        target_out = {
            "target_id": target["id"],
            "expected_identity": {
                "ano": target["ano"],
                "sequencial": target["sequencial"],
                "numeroControlePNCP": target["numeroControlePNCP"],
                "processo": target["processo"],
            },
            "routes": [],
        }
        for route in config["essentialRoutes"]:
            url = build_target_url(config, target, route)
            meta, payload = fetch_route(
                url,
                int(config["source"]["timeoutSeconds"]),
                int(config["source"]["maxBytesPerRoute"]),
            )
            result["request_count"] += 1
            route_out: dict[str, Any] = {"route": route["id"], **meta}

            if payload is None:
                route_out["status"] = "SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
            else:
                try:
                    if route["id"] == "DETAIL":
                        _stop(isinstance(payload, dict), "TASK168_DETAIL_SCHEMA")
                        validate_detail_identity(payload, target, "45132495000140")
                        route_out["sanitized"] = sanitize_payload("DETAIL", payload)
                        route_out["identity"] = {
                            "identity_confirmed_by_payload_field": True,
                            "numeroControlePNCP": target["numeroControlePNCP"],
                        }
                    else:
                        route_out["identity"] = validate_cross_route_control_identity(
                            payload,
                            target,
                            route["id"],
                        )
                        route_out["sanitized"] = sanitize_list_or_object(route["id"], payload)
                    route_out["status"] = "PASS_SANITIZED"
                except (Task167Stop, Task168Stop, Exception) as exc:
                    route_out["status"] = "STOP_SCHEMA_OR_IDENTITY"
                    route_out["validation_error"] = f"{type(exc).__name__}:{str(exc)}"
            target_out["routes"].append(route_out)
        result["targets"].append(target_out)

    _stop(
        result["request_count"] <= config["requestBudget"]["totalMaxIfHealthy"],
        "TASK168_REQUEST_BUDGET_EXCEEDED",
    )
    result["target_routes_attempted"] = sum(len(t["routes"]) for t in result["targets"])
    result["status"] = "RESOURCE_API_HEALTHY_TARGET_TRAVERSAL_COMPLETED_FAIL_CLOSED_PER_ROUTE"
    result["next_action"] = "ADJUDICATE_SANITIZED_TARGET_EVIDENCE"
    return result
