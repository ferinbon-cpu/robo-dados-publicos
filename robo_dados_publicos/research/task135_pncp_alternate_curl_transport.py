from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class Task135Stop(RuntimeError):
    pass


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task135Stop(code)


def validate_task135_contract(x: dict[str, Any]) -> dict[str, Any]:
    _r(x.get("schema") == "TASK135_PNCP_ALTERNATE_CURL_TRANSPORT_DESIGN_V1", "TASK135_SCHEMA")
    _r(x.get("mode") == "T0_OFFLINE_ALTERNATE_TRANSPORT_DESIGN_ONLY", "TASK135_MODE")
    _r(x.get("base_sha") == "cc6b6cf41f360d0c0d8414aa3ff04f036363d2f0", "TASK135_BASE")
    _r(x.get("issue") == 472, "TASK135_ISSUE")

    a = x.get("authorization_source") or {}
    _r(a.get("artifact") == "docs/evidence/TASK_134_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json", "TASK135_AUTH_PATH")
    _r(a.get("must_remain_unconsumed_before_execution") is True, "TASK135_AUTH_STATE")
    _r(a.get("does_not_create_new_scope") is True, "TASK135_AUTH_SCOPE")

    s = x.get("source") or {}
    expected = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=500"
    _r(s.get("exact_url") == expected, "TASK135_URL")
    p = urlparse(s["exact_url"])
    _r(p.scheme == "https" and p.hostname == "pncp.gov.br", "TASK135_HOST")
    _r(s.get("https_only") is True, "TASK135_HTTPS")
    _r(s.get("source_role") == "SECONDARY_AGGREGATOR", "TASK135_ROLE")

    c = x.get("curl") or {}
    _r(c.get("binary") == "curl", "TASK135_BINARY")
    _r(c.get("method") == "GET", "TASK135_METHOD")
    _r(c.get("max_requests") == 1, "TASK135_REQUESTS")
    _r(c.get("follow_redirects") is False, "TASK135_REDIRECT")
    _r(c.get("retry") == 0, "TASK135_RETRY")
    _r(c.get("max_time_seconds") == 60, "TASK135_MAX_TIME")
    _r(c.get("connect_timeout_seconds") == 15, "TASK135_CONNECT_TIMEOUT")
    _r(c.get("max_response_bytes") == 20971520, "TASK135_MAX_BYTES")
    _r(c.get("accept") == "application/json", "TASK135_ACCEPT")

    h = x.get("local_handling") or {}
    _r(h.get("temporary_raw_file_only") is True, "TASK135_TMP_ONLY")
    _r(h.get("raw_git_persistence") is False, "TASK135_RAW_GIT")
    _r(h.get("raw_drive_persistence") is False, "TASK135_RAW_DRIVE")
    _r(h.get("delete_raw_after_hash_and_parse") is True, "TASK135_DELETE_RAW")
    _r(h.get("sanitized_evidence_only") is True, "TASK135_SANITIZED")

    i = x.get("interpretation") or {}
    _r(i.get("parser_contract") == "TASK133_PNCP_PROCUREMENT_PUBLICATION_LIVE_GATE_DESIGN_V1", "TASK135_PARSER")
    _r(i.get("strong_policy_marker_required") is True, "TASK135_STRONG")
    _r(i.get("weak_context_alone_qualifies") is False, "TASK135_WEAK")
    _r(i.get("primary_municipal_verification_required") is True, "TASK135_PRIMARY")
    for k in ("automatic_financial_identity", "automatic_transaction_identity", "automatic_supplier_linkage"):
        _r(i.get(k) is False, f"TASK135_{k.upper()}")

    _r(x.get("followup_endpoints_authorized") is False, "TASK135_FOLLOWUP")
    effects = x.get("remote_effects_in_task135_design") or {}
    _r(effects and all(v is False for v in effects.values()), "TASK135_REMOTE")
    return x


def build_curl_argv(x: dict[str, Any], output_path: str) -> list[str]:
    x = validate_task135_contract(x)
    c = x["curl"]
    return [
        "curl",
        "--silent",
        "--show-error",
        "--request", "GET",
        "--proto", "=https",
        "--max-redirs", "0",
        "--retry", "0",
        "--connect-timeout", str(c["connect_timeout_seconds"]),
        "--max-time", str(c["max_time_seconds"]),
        "--max-filesize", str(c["max_response_bytes"]),
        "--header", f"Accept: {c['accept']}",
        "--user-agent", c["user_agent"],
        "--output", output_path,
        "--write-out", "%{http_code}|%{size_download}|%{url_effective}",
        x["source"]["exact_url"],
    ]


def load(path: str | Path) -> dict[str, Any]:
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task135Stop("TASK135_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task135Stop("TASK135_JSON") from exc
    _r(isinstance(obj, dict), "TASK135_OBJECT")
    return validate_task135_contract(obj)
