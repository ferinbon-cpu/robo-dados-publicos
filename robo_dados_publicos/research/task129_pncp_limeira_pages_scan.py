from __future__ import annotations

from copy import deepcopy
from hashlib import sha1
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.research.task128_pncp_limeira_contracts_scan import normalize_text


class Task129Stop(RuntimeError):
    """Fail-closed TASK 129 validation error."""


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task129Stop(code)


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def validate_task129_contract(x: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    _r(x.get("schema") == "TASK129_PNCP_LIMEIRA_PAGES2_5_SCAN_V1", "TASK129_SCHEMA")
    _r(x.get("mode") == "T1_SINGLE_USE_OFFICIAL_REGISTRY_REMAINING_PAGES_SCAN", "TASK129_MODE")

    up = x.get("upstream") or {}
    root = Path(root)
    raw = (root / str(up.get("task128_path") or "")).read_bytes()
    _r(_git_blob_sha(raw) == up.get("task128_git_blob_sha"), "TASK129_TASK128_BLOB")
    evidence = json.loads(raw.decode("utf-8"))
    _r(evidence.get("status") == "PARTIAL_PAGE1_REQUIRES_FRESH_PAGING_GATE", "TASK129_TASK128_STATUS")
    coverage = evidence.get("coverage") or {}
    _r(coverage.get("total_registros") == 2023 and coverage.get("total_paginas") == 5, "TASK129_TASK128_COVERAGE")
    _r(coverage.get("rows_on_page") == 500 and evidence.get("candidate_count") == 0, "TASK129_TASK128_PAGE1")

    source = x.get("source") or {}
    _r(source.get("registry") == "PNCP" and source.get("source_role") == "SECONDARY_AGGREGATOR", "TASK129_SOURCE")
    _r(source.get("cnpj_orgao") == "45132495000140", "TASK129_CNPJ")
    _r(source.get("data_inicial") == "20251128" and source.get("data_final") == "20260904", "TASK129_DATES")
    _r(source.get("tamanho_pagina") == 500, "TASK129_PAGE_SIZE")
    _r(source.get("pages") == [2, 3, 4, 5], "TASK129_PAGES")
    urls = source.get("exact_urls") or []
    _r(len(urls) == 4, "TASK129_URL_COUNT")
    for page, url in zip([2, 3, 4, 5], urls):
        expected = (
            "https://pncp.gov.br/api/consulta/v1/contratos"
            f"?dataInicial=20251128&dataFinal=20260904&cnpjOrgao=45132495000140"
            f"&pagina={page}&tamanhoPagina=500"
        )
        _r(url == expected, "TASK129_URL")
    _r(source.get("max_bytes_per_page") == 20971520, "TASK129_BYTES")

    transport = x.get("transport") or {}
    _r(transport.get("method") == "GET", "TASK129_METHOD")
    _r(transport.get("get_requests_max") == 4, "TASK129_GET_BUDGET")
    _r(transport.get("exact_page_order") == [2, 3, 4, 5], "TASK129_ORDER")
    _r(transport.get("redirects_max") == 0 and transport.get("retry") == 0, "TASK129_RETRY_REDIRECT")
    _r(transport.get("timeout_seconds") == 30, "TASK129_TIMEOUT")
    _r(transport.get("stop_on_first_failure") is True, "TASK129_STOP_FIRST")
    _r(transport.get("no_page1_reread") is True, "TASK129_NO_PAGE1")

    matching = x.get("matching") or {}
    _r(tuple(matching.get("normalized_strong_policy_markers") or ()) == (
        "PROGRAMA DE EDUCACAO INTEGRAL",
        "PROGRAMA ESCOLA EM TEMPO INTEGRAL",
        "ESCOLA EM TEMPO INTEGRAL",
        "EDUCACAO EM TEMPO INTEGRAL",
        "EDUCACAO INTEGRAL",
        "FOMENTO ETI",
    ), "TASK129_STRONG")
    _r(tuple(matching.get("weak_support_terms") or ()) == (
        "OFICINA", "OFICINEIRO", "EXTRACURRICULAR", "TEMPO INTEGRAL"
    ), "TASK129_WEAK")
    _r(matching.get("weak_terms_qualify_alone") is False, "TASK129_WEAK_GUARD")
    _r(tuple(matching.get("fields_to_search") or ()) == ("objetoContrato", "informacaoComplementar"), "TASK129_FIELDS")
    _r(matching.get("max_candidates") == 100, "TASK129_MAX_CANDIDATES")

    completion = x.get("completion_rules") or {}
    _r(completion.get("required_total_registros") == 2023 and completion.get("required_total_paginas") == 5, "TASK129_REQUIRED_META")
    _r(completion.get("required_pages") == [2, 3, 4, 5], "TASK129_REQUIRED_PAGES")
    _r(completion.get("required_remaining_rows") == 1523 and completion.get("full_scope_rows") == 2023, "TASK129_REQUIRED_ROWS")

    semantics = x.get("epistemic_semantics") or {}
    _r(semantics.get("source_role") == "SECONDARY_AGGREGATOR", "TASK129_ROLE")
    _r(semantics.get("no_match_proves_global_absence") is False, "TASK129_GLOBAL_ABSENCE")
    _r(semantics.get("no_match_proves_no_municipal_execution") is False, "TASK129_EXEC_ABSENCE")
    _r(semantics.get("generic_or_abbreviated_unmatched_objects_remain_possible") is True, "TASK129_GENERIC_GAP")
    _r(semantics.get("municipal_primary_verification_required") is True, "TASK129_PRIMARY")
    _r(semantics.get("automatic_financial_identity") is False, "TASK129_FINANCIAL_PROMOTION")
    _r(semantics.get("automatic_transaction_identity") is False, "TASK129_TRANSACTION_PROMOTION")

    persistence = x.get("persistence") or {}
    _r(persistence.get("raw_json_git") is False and persistence.get("raw_json_drive") is False, "TASK129_RAW")
    _r(persistence.get("sanitized_candidate_evidence_git") is True, "TASK129_SANITIZED")
    for key in ("bronze", "silver", "gold", "rag", "state_registry", "queue", "serving", "publication"):
        _r(persistence.get(key) is False, "TASK129_PERSIST")

    _r(x.get("future_retry_authorized") is False, "TASK129_FUTURE_RETRY")
    _r(x.get("future_additional_paging_authorized") is False, "TASK129_FUTURE_PAGING")
    return x


def scan_page_payload(payload: dict[str, Any], page: int, contract: dict[str, Any]) -> dict[str, Any]:
    _r(page in {2, 3, 4, 5}, "TASK129_PAGE_NUMBER")
    _r(isinstance(payload, dict), "TASK129_PAYLOAD_OBJECT")
    data = payload.get("data")
    _r(isinstance(data, list), "TASK129_DATA")
    _r(payload.get("totalRegistros") == 2023, "TASK129_TOTAL_REGISTROS")
    _r(payload.get("totalPaginas") == 5, "TASK129_TOTAL_PAGINAS")
    _r(payload.get("numeroPagina") == page, "TASK129_PAGE_MISMATCH")
    _r(len(data) > 0, "TASK129_EMPTY_EXPECTED_PAGE")

    strong = contract["matching"]["normalized_strong_policy_markers"]
    weak = contract["matching"]["weak_support_terms"]
    candidates: list[dict[str, Any]] = []

    for index, row in enumerate(data):
        _r(isinstance(row, dict), "TASK129_ROW_OBJECT")
        searchable = " ".join(
            normalize_text(row.get(field))
            for field in contract["matching"]["fields_to_search"]
        )
        strong_hits = [term for term in strong if term in searchable]
        weak_hits = [term for term in weak if term in searchable]
        if not strong_hits:
            continue
        candidates.append({
            "page": page,
            "row_index": index,
            "strong_policy_markers": strong_hits,
            "weak_support_terms": weak_hits,
            "source_role": "SECONDARY_AGGREGATOR",
            "status": "CANDIDATE_REQUIRES_MUNICIPAL_PRIMARY_VERIFICATION",
            "fields": {
                field: deepcopy(row.get(field))
                for field in contract["candidate_fields"]
                if row.get(field) is not None
            },
        })
        _r(len(candidates) <= contract["matching"]["max_candidates"], "TASK129_CANDIDATE_LIMIT")

    return {
        "page": page,
        "rows": len(data),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def combine_page_results(page_results: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    _r([item.get("page") for item in page_results] == [2, 3, 4, 5], "TASK129_RESULT_PAGE_ORDER")
    remaining_rows = sum(int(item.get("rows", 0)) for item in page_results)
    _r(remaining_rows == contract["completion_rules"]["required_remaining_rows"], "TASK129_REMAINING_ROWS")
    candidates = [
        candidate
        for item in page_results
        for candidate in (item.get("candidates") or [])
    ]
    _r(len(candidates) <= contract["matching"]["max_candidates"], "TASK129_COMBINED_CANDIDATE_LIMIT")

    total_rows = contract["upstream"]["page1_rows"] + remaining_rows
    _r(total_rows == contract["completion_rules"]["full_scope_rows"], "TASK129_FULL_ROWS")
    status = (
        contract["completion_rules"]["candidate_result"]
        if candidates
        else contract["completion_rules"]["zero_candidate_result"]
    )
    return {
        "status": status,
        "coverage": {
            "pages": [1, 2, 3, 4, 5],
            "total_registros": 2023,
            "rows_scanned": total_rows,
            "exhaustive_within_pncp_query_and_lexical_scope": True,
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "bounded_no_match_only": len(candidates) == 0,
        "proves_global_absence": False,
        "proves_no_municipal_eiti_execution": False,
        "municipal_primary_verification_required": True,
        "financial_identity_promoted": False,
        "transaction_identity_promoted": False,
    }


def load_task129_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        x = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task129Stop("TASK129_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task129Stop("TASK129_JSON") from exc
    _r(isinstance(x, dict), "TASK129_OBJECT")
    return validate_task129_contract(x, root=root)
