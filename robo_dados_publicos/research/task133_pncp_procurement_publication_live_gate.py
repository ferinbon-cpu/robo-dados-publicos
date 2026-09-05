from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any
import unicodedata


class Task133Stop(RuntimeError):
    """Fail-closed TASK 133 design or future-payload contract error."""


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task133Stop(code)


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text.upper())
    return " ".join(text.split())


def validate_task133_contract(x: dict[str, Any]) -> dict[str, Any]:
    _r(x.get("schema") == "TASK133_PNCP_PROCUREMENT_PUBLICATION_LIVE_GATE_DESIGN_V1", "TASK133_SCHEMA")
    _r(x.get("mode") == "T0_OFFLINE_LIVE_GATE_DESIGN_ONLY", "TASK133_MODE")
    _r(x.get("base_sha") == "ca09484b3967e6e7820d949dc8859129d5586b24", "TASK133_BASE")
    _r(x.get("issue") == 468, "TASK133_ISSUE")

    dep = x.get("depends_on") or {}
    _r(dep.get("task") == "TASK_132_PROCUREMENT_PUBLICATION_SURFACE_SELECTION", "TASK133_DEP_TASK")
    _r(dep.get("merge_sha") == "ca09484b3967e6e7820d949dc8859129d5586b24", "TASK133_DEP_SHA")

    a = x.get("authorization") or {}
    _r(a.get("owner_authorization_required") is True, "TASK133_AUTH_REQUIRED")
    _r(a.get("authorized_now") is False, "TASK133_AUTH_MUST_BE_FALSE")
    _r(a.get("one_shot_required") is True and a.get("max_live_runs") == 1, "TASK133_ONE_SHOT")
    _r(a.get("must_be_issued_after_gate_merge") is True, "TASK133_AUTH_AFTER_MERGE")
    _r(a.get("fixed_artifact_path") == "docs/evidence/TASK_133_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json", "TASK133_AUTH_PATH")
    _r(a.get("authorization_artifact_must_be_absent_in_design") is True, "TASK133_AUTH_ABSENT")
    _r(a.get("owner_instruction_consumed") is False, "TASK133_AUTH_NOT_CONSUMED")

    s = x.get("source") or {}
    _r(s.get("registry") == "PNCP", "TASK133_REGISTRY")
    _r(s.get("endpoint") == "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao", "TASK133_ENDPOINT")
    _r(
        s.get("exact_url")
        == "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=500",
        "TASK133_EXACT_URL",
    )
    _r(s.get("source_role") == "SECONDARY_AGGREGATOR", "TASK133_ROLE")
    _r(s.get("official_registry_surface") is True, "TASK133_OFFICIAL_SURFACE")
    _r(s.get("cnpj_orgao") == "45132495000140", "TASK133_CNPJ")
    _r(s.get("data_inicial") == "20251128" and s.get("data_final") == "20260904", "TASK133_DATES")
    _r(s.get("codigo_modalidade_contratacao") == 12 and s.get("modalidade_nome") == "Credenciamento", "TASK133_MODALITY")
    _r(s.get("pagina") == 1 and s.get("tamanho_pagina") == 500, "TASK133_PAGE")
    _r(s.get("max_bytes") == 20971520, "TASK133_BYTES")

    t = x.get("transport") or {}
    _r(t.get("method") == "GET", "TASK133_METHOD")
    _r(t.get("get_requests_max") == 1, "TASK133_GET")
    _r(t.get("redirects_max") == 0, "TASK133_REDIRECT")
    _r(t.get("retry") == 0, "TASK133_RETRY")
    _r(t.get("timeout_seconds") == 60, "TASK133_TIMEOUT")
    _r(t.get("accept") == "application/json", "TASK133_ACCEPT")
    _r(t.get("exact_url_only") is True, "TASK133_EXACT_ONLY")

    rc = x.get("response_contract") or {}
    _r(rc.get("data_field") == "data", "TASK133_DATA_FIELD")
    _r(rc.get("total_registros_field") == "totalRegistros", "TASK133_TOTAL_REGISTROS_FIELD")
    _r(rc.get("total_paginas_field") == "totalPaginas", "TASK133_TOTAL_PAGINAS_FIELD")
    _r(rc.get("numero_pagina_field") == "numeroPagina", "TASK133_NUMERO_PAGINA_FIELD")
    _r(rc.get("no_pagination_in_this_execution") is True, "TASK133_NO_PAGING")

    m = x.get("matching") or {}
    _r(
        tuple(m.get("normalized_strong_policy_markers") or ())
        == (
            "PROGRAMA DE EDUCACAO INTEGRAL",
            "PROGRAMA ESCOLA EM TEMPO INTEGRAL",
            "ESCOLA EM TEMPO INTEGRAL",
            "EDUCACAO EM TEMPO INTEGRAL",
            "EDUCACAO INTEGRAL",
        ),
        "TASK133_STRONG_MARKERS",
    )
    _r(
        tuple(m.get("title_context_markers") or ())
        == ("CREDENCIAMENTO", "OFICINEIRO", "OFICINEIROS", "OFICINAS EXTRACURRICULARES"),
        "TASK133_CONTEXT_MARKERS",
    )
    _r(m.get("strong_policy_marker_required") is True, "TASK133_STRONG_REQUIRED")
    _r(m.get("weak_context_alone_qualifies") is False, "TASK133_WEAK_GUARD")
    _r(tuple(m.get("fields_to_search") or ()) == ("objetoCompra", "informacaoComplementar"), "TASK133_FIELDS")
    _r(m.get("max_candidates") == 100, "TASK133_MAX_CANDIDATES")

    sem = x.get("epistemic_semantics") or {}
    _r(sem.get("source_role") == "SECONDARY_AGGREGATOR", "TASK133_SEM_ROLE")
    _r(sem.get("administrative_identifier_candidate_max_status") == "CORROBORATED", "TASK133_STATUS_CAP")
    _r(sem.get("primary_municipal_verification_required") is True, "TASK133_PRIMARY")
    for key in ("automatic_financial_identity", "automatic_transaction_identity", "automatic_supplier_linkage"):
        _r(sem.get(key) is False, f"TASK133_{key.upper()}")
    _r(sem.get("weak_join_forbidden") is True, "TASK133_WEAK_JOIN")

    p = x.get("persistence") or {}
    _r(p and all(v is False for v in p.values()), "TASK133_PERSISTENCE")

    f = x.get("followup_authorization") or {}
    _r(f and all(v is False for v in f.values()), "TASK133_FOLLOWUP")

    effects = x.get("remote_effects_in_task133_design") or {}
    _r(effects and all(v is False for v in effects.values()), "TASK133_REMOTE_EFFECT")
    return x


def _int_field(payload: dict[str, Any], field: str, code: str) -> int:
    value = payload.get(field)
    _r(isinstance(value, int) and not isinstance(value, bool) and value >= 0, code)
    return value


def interpret_future_payload(payload: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    """Offline definition of how a future authorized one-shot payload must be interpreted."""
    contract = validate_task133_contract(contract)
    _r(isinstance(payload, dict), "TASK133_PAYLOAD_OBJECT")
    rc = contract["response_contract"]
    data = payload.get(rc["data_field"])
    _r(isinstance(data, list), "TASK133_PAYLOAD_DATA")
    total_registros = _int_field(payload, rc["total_registros_field"], "TASK133_TOTAL_REGISTROS")
    total_paginas = _int_field(payload, rc["total_paginas_field"], "TASK133_TOTAL_PAGINAS")
    numero_pagina = _int_field(payload, rc["numero_pagina_field"], "TASK133_NUMERO_PAGINA")
    _r(numero_pagina == 1, "TASK133_PAGE_MISMATCH")
    _r(total_registros >= len(data), "TASK133_TOTAL_LT_PAGE")
    _r(total_registros == 0 or len(data) > 0, "TASK133_POSITIVE_TOTAL_EMPTY_PAGE")
    if total_paginas == 0:
        _r(total_registros == 0, "TASK133_ZERO_PAGES_WITH_RECORDS")

    strong = contract["matching"]["normalized_strong_policy_markers"]
    context = contract["matching"]["title_context_markers"]
    fields = contract["matching"]["fields_to_search"]
    candidates: list[dict[str, Any]] = []

    for index, row in enumerate(data):
        _r(isinstance(row, dict), "TASK133_ROW_OBJECT")
        searchable = " ".join(normalize_text(row.get(field)) for field in fields)
        strong_hits = [term for term in strong if term in searchable]
        context_hits = [term for term in context if term in searchable]
        if not strong_hits:
            continue
        candidates.append(
            {
                "row_index": index,
                "strong_policy_markers": strong_hits,
                "context_markers": context_hits,
                "source_role": "SECONDARY_AGGREGATOR",
                "status": "CANDIDATE_ADMIN_IDENTIFIER_REQUIRES_PRIMARY_VERIFICATION",
                "fields": {
                    field: deepcopy(row.get(field))
                    for field in contract["candidate_fields"]
                    if row.get(field) is not None
                },
                "financial_identity_promoted": False,
                "transaction_identity_promoted": False,
            }
        )
        _r(len(candidates) <= contract["matching"]["max_candidates"], "TASK133_CANDIDATE_LIMIT")

    exhaustive = total_paginas <= 1
    if candidates and exhaustive:
        status = "CANDIDATE_ADMIN_IDENTIFIER_REQUIRES_PRIMARY_VERIFICATION"
    elif candidates:
        status = "PARTIAL_CANDIDATE_ADMIN_IDENTIFIER_REQUIRES_PRIMARY_VERIFICATION"
    elif exhaustive:
        status = "NO_MATCH_WITHIN_PNCP_CNPJ_MODALITY_DATE_SCOPE_ONLY"
    else:
        status = "PARTIAL_PAGE1_NO_CONCLUSION_FRESH_GATE_REQUIRED"

    return {
        "status": status,
        "coverage": {
            "total_registros": total_registros,
            "total_paginas": total_paginas,
            "numero_pagina": numero_pagina,
            "rows_on_page": len(data),
            "exhaustive_within_query_scope": exhaustive,
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "weak_context_never_qualifies_alone": True,
        "primary_municipal_verification_required": True,
        "financial_identity_promoted": False,
        "transaction_identity_promoted": False,
    }


def load_task133_contract(path: str | Path) -> dict[str, Any]:
    try:
        x = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task133Stop("TASK133_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task133Stop("TASK133_JSON") from exc
    _r(isinstance(x, dict), "TASK133_OBJECT")
    return validate_task133_contract(x)
