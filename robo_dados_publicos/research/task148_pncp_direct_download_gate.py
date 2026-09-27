from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Task148Stop(RuntimeError):
    pass


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task148Stop(code)


def validate_task148_contract(x: dict[str, Any]) -> dict[str, Any]:
    _r(x.get("schema") == "TASK148_PNCP_DIRECT_DOWNLOAD_GATE_V1", "TASK148_SCHEMA")
    _r(x.get("mode") == "T0_OFFLINE_DIRECT_DOWNLOAD_GATE_ONLY", "TASK148_MODE")
    _r(x.get("issue") == 506, "TASK148_ISSUE")
    _r(x.get("base_sha") == "81e764fdf2a079c8151ae4d5bb7f0e29c885e682", "TASK148_BASE")

    a=x.get("fresh_owner_authorization") or {}
    _r(a.get("instruction") == "Prossiga autorizado", "TASK148_AUTH")
    _r(a.get("task_specific") is True, "TASK148_AUTH_SCOPE")
    _r(a.get("independent_from_task146_authorization") is True, "TASK148_AUTH_INDEPENDENT")

    u=x.get("upstream") or {}
    _r(u.get("task147_merge_sha") == "81e764fdf2a079c8151ae4d5bb7f0e29c885e682", "TASK148_UPSTREAM_SHA")
    _r(u.get("task147_result") == "STOP_MANAGED_WEB_CACHE_MISS_NO_PNCP_CONTENT", "TASK148_UPSTREAM_RESULT")

    s=x.get("source") or {}
    expected="https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=50"
    _r(s.get("exact_url") == expected, "TASK148_URL")
    _r(s.get("source_role") == "SECONDARY_AGGREGATOR", "TASK148_ROLE")
    _r(s.get("page") == 1 and s.get("page_size") == 50, "TASK148_PAGE")

    t=x.get("future_transport") or {}
    _r(t.get("kind") == "DIRECT_TEMPORARY_DOWNLOAD", "TASK148_TRANSPORT")
    _r(t.get("invocations_max") == 1, "TASK148_INVOCATIONS")
    for k in ("retry","search_queries","clicks","alternate_endpoints","pagination_followups"):
        _r(t.get(k) == 0, f"TASK148_{k.upper()}")
    _r(t.get("raw_payload_git_persistence") is False, "TASK148_RAW_GIT")
    _r(t.get("raw_payload_drive_persistence") is False, "TASK148_RAW_DRIVE")
    _r(t.get("temporary_local_payload_allowed") is True, "TASK148_TEMP")
    _r(t.get("local_sha256_on_success") is True, "TASK148_SHA")
    _r(t.get("local_byte_count_on_success") is True, "TASK148_BYTES")

    e=x.get("epistemic_semantics") or {}
    _r(e.get("positive_candidate_discovery_allowed") is True, "TASK148_POSITIVE")
    _r(e.get("administrative_identifier_candidate_max_status") == "CORROBORATED", "TASK148_STATUS")
    _r(e.get("negative_exhaustive_conclusion_allowed") is False, "TASK148_NEGATIVE")
    _r(e.get("pncp_no_match_from_transport_failure_or_empty_result_allowed") is False, "TASK148_NOMATCH")
    _r(e.get("primary_municipal_verification_required") is True, "TASK148_PRIMARY")
    for k in ("automatic_financial_identity","automatic_transaction_identity","automatic_supplier_linkage"):
        _r(e.get(k) is False, f"TASK148_{k.upper()}")

    r=x.get("remote_effects_in_design") or {}
    _r(r and all(v is False for v in r.values()), "TASK148_REMOTE")
    return x


def load(path: str | Path) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    _r(isinstance(obj,dict),"TASK148_OBJECT")
    return validate_task148_contract(obj)
