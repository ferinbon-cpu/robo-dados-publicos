from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class Task167Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task167Stop(code)


BUDGET_KEY_RE = re.compile(
    r"(fonte|orcament|dota[cç][aã]o|programa|a[cç][aã]o|natureza|despesa|"
    r"unidade|org[aã]o|empenho|contabil|c[oó]digo|identificador|id)",
    re.IGNORECASE,
)

DETAIL_ALLOW = {
    "anoCompra", "sequencialCompra", "numeroControlePNCP", "processo",
    "numeroCompra", "objetoCompra", "valorTotalEstimado", "valorTotalHomologado",
    "dataPublicacaoPncp", "modalidadeId", "modalidadeNome", "situacaoCompraId",
    "situacaoCompraNome", "modoDisputaId", "modoDisputaNome",
}
ITEM_ALLOW = {
    "numeroItem", "descricao", "materialOuServico", "materialOuServicoNome",
    "quantidade", "unidadeMedida", "valorUnitarioEstimado", "valorTotal",
    "criterioJulgamentoId", "criterioJulgamentoNome", "situacaoCompraItemNome",
}
HISTORY_ALLOW = {
    "sequencialHistorico", "dataHoraEvento", "dataPublicacaoPncp",
    "situacaoCompraId", "situacaoCompraNome", "justificativa",
}
CONTRACT_ALLOW = {
    "numeroControlePNCP", "numeroContratoEmpenho", "anoContrato",
    "sequencialContrato", "processo", "objetoContrato", "valorInicial",
    "valorGlobal", "valorAcumulado", "dataAssinatura", "dataVigenciaInicio",
    "dataVigenciaFim", "tipoContratoId", "tipoContratoNome",
}


def load_config(path: str | Path) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK167_PNCP_STABLE_ID_DIRECT_JSON_TRAVERSAL_V1", "TASK167_CONFIG_SCHEMA")
    _stop(obj["authorization"]["scope"] == "PNCP_LIVE_READ_DISCOVERY_ONLY", "TASK167_AUTH_SCOPE")
    _stop(obj["authorization"]["new_per_route_authorization_required"] is False, "TASK167_AUTH_REUSE")
    _stop(obj["source"]["origin"] == "https://pncp.gov.br", "TASK167_ORIGIN")
    _stop(obj["source"]["cnpj"] == "45132495000140", "TASK167_CNPJ")
    _stop(obj["source"]["retryMax"] == 0, "TASK167_RETRY")
    _stop(obj["source"]["redirectsMax"] == 0, "TASK167_REDIRECT")
    _stop(obj["persistence"]["rawPayloadGit"] is False, "TASK167_RAW_GIT")
    _stop(obj["persistence"]["rawPayloadDrive"] is False, "TASK167_RAW_DRIVE")
    _stop(obj["persistence"]["rawPayloadWorkflowArtifact"] is False, "TASK167_RAW_ARTIFACT")
    return obj


def build_url(config: dict[str, Any], target: dict[str, Any], route: dict[str, Any]) -> str:
    path = route["path"].format(
        cnpj=config["source"]["cnpj"],
        ano=target["ano"],
        sequencial=target["sequencial"],
    )
    return config["source"]["origin"] + path


def _primitive(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _selected_dict(obj: dict[str, Any], allow: set[str]) -> dict[str, Any]:
    return {k: obj.get(k) for k in sorted(allow) if k in obj and _primitive(obj.get(k))}


def _entity_summary(obj: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    org = obj.get("orgaoEntidade")
    if isinstance(org, dict):
        out["orgaoEntidade"] = {
            k: org.get(k) for k in ("cnpj", "razaoSocial", "poderId", "esferaId")
            if k in org and _primitive(org.get(k))
        }
    unit = obj.get("unidadeOrgao")
    if isinstance(unit, dict):
        out["unidadeOrgao"] = {
            k: unit.get(k) for k in ("codigoUnidade", "nomeUnidade", "municipioNome", "ufSigla")
            if k in unit and _primitive(unit.get(k))
        }
    return out


def _extract_budget_signals(value: Any, path: str = "", limit: int = 200) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    def walk(v: Any, p: str) -> None:
        if len(signals) >= limit:
            return
        if isinstance(v, dict):
            for k, x in v.items():
                np = f"{p}.{k}" if p else str(k)
                if _primitive(x) and BUDGET_KEY_RE.search(np):
                    signals.append({"path": np, "value": x, "status": "CANDIDATE_NOT_PROVEN"})
                else:
                    walk(x, np)
        elif isinstance(v, list):
            for i, x in enumerate(v[:100]):
                walk(x, f"{p}[{i}]")

    walk(value, path)
    return signals


def sanitize_payload(route_id: str, payload: Any) -> dict[str, Any]:
    if route_id == "DETAIL":
        _stop(isinstance(payload, dict), "TASK167_DETAIL_SCHEMA")
        selected = _selected_dict(payload, DETAIL_ALLOW)
        selected.update(_entity_summary(payload))
        return {
            "shape": "OBJECT",
            "top_level_keys": sorted(payload.keys()),
            "selected": selected,
            "budget_accounting_signals": _extract_budget_signals(payload),
        }

    _stop(isinstance(payload, list), f"TASK167_{route_id}_SCHEMA")
    if route_id == "ITEMS":
        normalized = [_selected_dict(x, ITEM_ALLOW) for x in payload if isinstance(x, dict)]
    elif route_id == "HISTORY":
        normalized = [_selected_dict(x, HISTORY_ALLOW) for x in payload if isinstance(x, dict)]
    elif route_id == "LINKED_CONTRACTS":
        normalized = []
        for x in payload:
            if isinstance(x, dict):
                row = _selected_dict(x, CONTRACT_ALLOW)
                row.update(_entity_summary(x))
                normalized.append(row)
    else:
        normalized = []
        for x in payload:
            if isinstance(x, dict):
                normalized.append({
                    "selected_budget_fields": _extract_budget_signals(x, limit=100),
                    "top_level_keys": sorted(x.keys()),
                })
    keys = sorted({k for x in payload if isinstance(x, dict) for k in x.keys()})
    return {
        "shape": "LIST",
        "count": len(payload),
        "item_keys": keys,
        "selected": normalized,
        "budget_accounting_signals": _extract_budget_signals(payload),
    }


def validate_detail_identity(payload: dict[str, Any], target: dict[str, Any], expected_cnpj: str) -> None:
    org = payload.get("orgaoEntidade") or {}
    observed_cnpj = str(org.get("cnpj") or payload.get("cnpj") or "")
    _stop(observed_cnpj == expected_cnpj, "TASK167_ENTITY_IDENTITY_MISMATCH")
    _stop(payload.get("anoCompra") == target["ano"], "TASK167_YEAR_IDENTITY_MISMATCH")
    _stop(payload.get("sequencialCompra") == target["sequencial"], "TASK167_SEQUENCE_IDENTITY_MISMATCH")
    _stop(payload.get("numeroControlePNCP") == target["numeroControlePNCP"], "TASK167_CONTROL_IDENTITY_MISMATCH")
    _stop(str(payload.get("processo") or "").strip().upper() == target["processo"].upper(), "TASK167_PROCESS_IDENTITY_MISMATCH")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_route(url: str, timeout: int, max_bytes: int) -> tuple[dict[str, Any], Any | None]:
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "robo-dados-publicos-task167/0.8.0"},
    )
    raw = b""
    status = None
    content_type = None
    transport_error = None
    try:
        with opener.open(req, timeout=timeout) as response:
            status = int(response.status)
            content_type = response.headers.get("Content-Type")
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise Task167Stop("TASK167_RESPONSE_TOO_LARGE")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        transport_error = f"HTTP_ERROR_{exc.code}"
    except urllib.error.URLError as exc:
        transport_error = f"URL_ERROR:{type(exc.reason).__name__}"
    except Exception as exc:
        transport_error = f"TRANSPORT_ERROR:{type(exc).__name__}:{str(exc)[:160]}"

    meta = {
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "bytes_received": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "transport_error": transport_error,
    }
    if status != 200 or not raw:
        return meta, None

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        meta["parse_error"] = f"{type(exc).__name__}:{str(exc)[:160]}"
        return meta, None
    return meta, payload


def execute(config: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "TASK167_PNCP_STABLE_ID_DIRECT_JSON_RESULT_V1",
        "authorization_scope": config["authorization"]["scope"],
        "targets": [],
        "raw_payload_persisted": False,
        "payment_inference_from_pncp": "FORBIDDEN",
        "financial_identity_auto_promotion": "FORBIDDEN",
        "transaction_identity_auto_promotion": "FORBIDDEN",
    }

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
        detail_validated = False
        for route in config["routes"]:
            url = build_url(config, target, route)
            meta, payload = fetch_route(
                url,
                int(config["source"]["timeoutSeconds"]),
                int(config["source"]["maxBytesPerRoute"]),
            )
            route_out: dict[str, Any] = {"route": route["id"], **meta}
            if payload is None:
                route_out["status"] = "SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
            else:
                try:
                    if route["id"] == "DETAIL":
                        validate_detail_identity(payload, target, config["source"]["cnpj"])
                        detail_validated = True
                    route_out["sanitized"] = sanitize_payload(route["id"], payload)
                    route_out["status"] = "PASS_SANITIZED"
                except Exception as exc:
                    route_out["status"] = "STOP_SCHEMA_OR_IDENTITY"
                    route_out["validation_error"] = f"{type(exc).__name__}:{str(exc)}"
            target_out["routes"].append(route_out)
        target_out["detail_identity_validated"] = detail_validated
        out["targets"].append(target_out)

    out["candidate_accounting_signals"] = [
        {
            "target_id": t["target_id"],
            "route": r["route"],
            "signals": r.get("sanitized", {}).get("budget_accounting_signals", []),
        }
        for t in out["targets"]
        for r in t["routes"]
        if r.get("sanitized", {}).get("budget_accounting_signals")
    ]
    return out
