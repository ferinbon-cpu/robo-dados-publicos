from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any
import unicodedata


class Task128Stop(RuntimeError):
    """Fail-closed TASK 128 contract or payload validation error."""


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task128Stop(code)


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text.upper())
    return " ".join(text.split())


def validate_task128_contract(x: dict[str, Any]) -> dict[str, Any]:
    _r(x.get("schema") == "TASK128_PNCP_LIMEIRA_CONTRACTS_PAGE1_SCAN_V1", "TASK128_SCHEMA")
    _r(x.get("mode") == "T1_SINGLE_USE_OFFICIAL_REGISTRY_PAGE1_SCAN", "TASK128_MODE")
    s = x.get("source") or {}
    _r(s.get("registry") == "PNCP", "TASK128_REGISTRY")
    _r(s.get("base_url") == "https://pncp.gov.br/api/consulta", "TASK128_BASE_URL")
    _r(
        s.get("exact_url")
        == "https://pncp.gov.br/api/consulta/v1/contratos?dataInicial=20251128&dataFinal=20260904&cnpjOrgao=45132495000140&pagina=1&tamanhoPagina=500",
        "TASK128_URL",
    )
    _r(s.get("source_role") == "SECONDARY_AGGREGATOR", "TASK128_ROLE")
    _r(s.get("official_registry_surface") is True, "TASK128_REGISTRY_SURFACE")
    _r(s.get("cnpj_orgao") == "45132495000140", "TASK128_CNPJ")
    _r(s.get("data_inicial") == "20251128" and s.get("data_final") == "20260904", "TASK128_DATES")
    _r(s.get("pagina") == 1 and s.get("tamanho_pagina") == 500, "TASK128_PAGE")
    _r(s.get("max_bytes") == 20971520, "TASK128_BYTES")

    t = x.get("transport") or {}
    _r(t.get("method") == "GET", "TASK128_METHOD")
    _r(t.get("get_requests_max") == 1, "TASK128_GET")
    _r(t.get("redirects_max") == 0, "TASK128_REDIRECT")
    _r(t.get("retry") == 0, "TASK128_RETRY")
    _r(t.get("timeout_seconds") == 30, "TASK128_TIMEOUT")
    _r(t.get("accept") == "application/json", "TASK128_ACCEPT")
    _r(t.get("exact_url_only") is True, "TASK128_EXACT")

    rc = x.get("response_contract") or {}
    _r(rc.get("data_field") == "data", "TASK128_DATA_FIELD")
    _r(rc.get("total_registros_field") == "totalRegistros", "TASK128_TOTAL_REGISTROS_FIELD")
    _r(rc.get("total_paginas_field") == "totalPaginas", "TASK128_TOTAL_PAGINAS_FIELD")
    _r(rc.get("numero_pagina_field") == "numeroPagina", "TASK128_NUMERO_PAGINA_FIELD")
    _r(rc.get("no_pagination_in_task") is True, "TASK128_NO_PAGING")

    m = x.get("matching") or {}
    strong = tuple(m.get("normalized_strong_policy_markers") or ())
    _r(
        strong
        == (
            "PROGRAMA DE EDUCACAO INTEGRAL",
            "PROGRAMA ESCOLA EM TEMPO INTEGRAL",
            "ESCOLA EM TEMPO INTEGRAL",
            "EDUCACAO EM TEMPO INTEGRAL",
            "EDUCACAO INTEGRAL",
            "FOMENTO ETI",
        ),
        "TASK128_STRONG_MARKERS",
    )
    _r(
        tuple(m.get("weak_support_terms") or ())
        == ("OFICINA", "OFICINEIRO", "EXTRACURRICULAR", "TEMPO INTEGRAL"),
        "TASK128_WEAK_TERMS",
    )
    _r(m.get("weak_terms_qualify_alone") is False, "TASK128_WEAK_GUARD")
    _r(tuple(m.get("fields_to_search") or ()) == ("objetoContrato", "informacaoComplementar"), "TASK128_SEARCH_FIELDS")
    _r(m.get("max_candidates") == 100, "TASK128_MAX_CANDIDATES")

    sem = x.get("epistemic_semantics") or {}
    _r(sem.get("source_role") == "SECONDARY_AGGREGATOR", "TASK128_SEM_ROLE")
    _r(sem.get("search_result_can_be_proven_within_scope") is True, "TASK128_SEARCH_STATUS")
    for key in ("accounting_execution_max_status", "administrative_event_max_status", "policy_linkage_max_status"):
        _r(sem.get(key) == "CORROBORATED", "TASK128_STATUS_CAP")
    _r(sem.get("automatic_financial_identity") is False, "TASK128_FINANCIAL_PROMOTION")
    _r(sem.get("automatic_transaction_identity") is False, "TASK128_TRANSACTION_PROMOTION")
    _r(sem.get("municipal_primary_verification_required") is True, "TASK128_PRIMARY_VERIFY")
    _r(sem.get("weak_join_forbidden") is True, "TASK128_WEAK_JOIN")

    p = x.get("persistence") or {}
    _r(p.get("raw_json_git") is False and p.get("raw_json_drive") is False, "TASK128_RAW_PERSIST")
    _r(p.get("sanitized_candidate_evidence_git") is True, "TASK128_SANITIZED_EVIDENCE")
    for key in ("bronze","silver","gold","rag","state_registry","queue","serving","publication"):
        _r(p.get(key) is False, "TASK128_PERSIST")
    _r(x.get("future_paging_authorized") is False, "TASK128_FUTURE_PAGING")
    _r(x.get("future_retry_authorized") is False, "TASK128_FUTURE_RETRY")
    return x


def _int_field(payload: dict[str, Any], field: str, code: str) -> int:
    value = payload.get(field)
    _r(isinstance(value, int) and not isinstance(value, bool) and value >= 0, code)
    return value


def scan_pncp_payload(payload: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    contract = validate_task128_contract(contract)
    _r(isinstance(payload, dict), "TASK128_PAYLOAD_OBJECT")
    rc = contract["response_contract"]
    data = payload.get(rc["data_field"])
    _r(isinstance(data, list), "TASK128_PAYLOAD_DATA")
    total_registros = _int_field(payload, rc["total_registros_field"], "TASK128_PAYLOAD_TOTAL_REGISTROS")
    total_paginas = _int_field(payload, rc["total_paginas_field"], "TASK128_PAYLOAD_TOTAL_PAGINAS")
    numero_pagina = _int_field(payload, rc["numero_pagina_field"], "TASK128_PAYLOAD_NUMERO_PAGINA")
    _r(numero_pagina == 1, "TASK128_PAYLOAD_PAGE_MISMATCH")
    _r(total_registros >= len(data), "TASK128_PAYLOAD_TOTAL_LT_PAGE")
    _r(total_registros == 0 or len(data) > 0, "TASK128_POSITIVE_TOTAL_EMPTY_PAGE")

    if total_registros == 0:
        _r(len(data) == 0, "TASK128_EMPTY_WITH_DATA")
    if total_paginas == 0:
        _r(total_registros == 0, "TASK128_ZERO_PAGES_WITH_RECORDS")

    strong = contract["matching"]["normalized_strong_policy_markers"]
    weak = contract["matching"]["weak_support_terms"]
    fields = contract["matching"]["fields_to_search"]
    candidates: list[dict[str, Any]] = []

    for index, row in enumerate(data):
        _r(isinstance(row, dict), "TASK128_ROW_OBJECT")
        normalized_fields = {
            field: normalize_text(row.get(field))
            for field in fields
        }
        searchable = " ".join(normalized_fields.values())
        strong_hits = [term for term in strong if term in searchable]
        weak_hits = [term for term in weak if term in searchable]
        if not strong_hits:
            continue
        candidate = {
            "row_index": index,
            "strong_policy_markers": strong_hits,
            "weak_support_terms": weak_hits,
            "source_role": "SECONDARY_AGGREGATOR",
            "status": "CANDIDATE_REQUIRES_MUNICIPAL_PRIMARY_VERIFICATION",
            "automatic_financial_identity": False,
            "automatic_transaction_identity": False,
            "fields": {
                field: deepcopy(row.get(field))
                for field in contract["candidate_fields"]
                if row.get(field) is not None
            },
        }
        candidates.append(candidate)
        _r(len(candidates) <= contract["matching"]["max_candidates"], "TASK128_CANDIDATE_LIMIT")

    exhaustive = total_paginas <= 1
    if not exhaustive and candidates:
        status = "PARTIAL_CANDIDATE_MATCH_PAGE1_ONLY"
    elif not exhaustive:
        status = "PARTIAL_PAGE1_REQUIRES_FRESH_PAGING_GATE"
    elif candidates:
        status = "CANDIDATE_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE"
    else:
        status = "NO_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE_ONLY"

    return {
        "status": status,
        "query_scope": {
            "cnpj_orgao": contract["source"]["cnpj_orgao"],
            "data_inicial": contract["source"]["data_inicial"],
            "data_final": contract["source"]["data_final"],
            "pagina": 1,
            "tamanho_pagina": 500,
        },
        "coverage": {
            "total_registros": total_registros,
            "total_paginas": total_paginas,
            "numero_pagina": numero_pagina,
            "rows_on_page": len(data),
            "exhaustive_within_query_scope": exhaustive,
            "fresh_paging_gate_required": not exhaustive,
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "weak_terms_never_qualify_alone": True,
        "financial_identity_promoted": False,
        "transaction_identity_promoted": False,
        "municipal_primary_verification_required": True,
    }


def load_task128_contract(path: str | Path) -> dict[str, Any]:
    try:
        x = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task128Stop("TASK128_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task128Stop("TASK128_JSON") from exc
    _r(isinstance(x, dict), "TASK128_OBJECT")
    return validate_task128_contract(x)
