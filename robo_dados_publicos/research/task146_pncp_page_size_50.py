from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Task146Stop(RuntimeError):
    pass


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task146Stop(code)


def validate_task146_contract(x: dict[str, Any]) -> dict[str, Any]:
    _r(x.get("schema") == "TASK146_PNCP_PROCUREMENT_PAGE_SIZE_50_V1", "TASK146_SCHEMA")
    _r(x.get("mode") == "T0_OFFLINE_CORRECTION_GATE_ONLY", "TASK146_MODE")
    _r(x.get("issue") == 502, "TASK146_ISSUE")

    a=x.get("fresh_owner_authorization") or {}
    _r(a.get("instruction") == "Autorizado", "TASK146_AUTH")
    _r(a.get("user_supplied_exact_url") is True, "TASK146_USER_URL")
    _r(a.get("independent_from_prior_10_unit_authorization") is True, "TASK146_AUTH_SEPARATE")

    h=x.get("historical_correction") or {}
    _r(h.get("prior_page_size") == 500, "TASK146_PRIOR_SIZE")
    _r(h.get("prior_user_observed_response_status") == 400, "TASK146_PRIOR_STATUS")
    _r(h.get("prior_user_observed_error") == "Tamanho de página inválido", "TASK146_PRIOR_ERROR")
    _r(h.get("historical_artifacts_rewritten") is False, "TASK146_HISTORY")
    _r(h.get("canonical_future_page_size") == 50, "TASK146_SIZE")

    s=x.get("source") or {}
    expected="https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=50"
    _r(s.get("exact_url") == expected, "TASK146_URL")
    _r(s.get("source_role") == "SECONDARY_AGGREGATOR", "TASK146_ROLE")
    _r(s.get("page") == 1 and s.get("page_size") == 50, "TASK146_PAGE")

    w=x.get("managed_web_execution") or {}
    _r(w.get("open_invocations_max") == 1, "TASK146_OPEN")
    _r(w.get("search_queries") == 0, "TASK146_SEARCH")
    _r(w.get("clicks") == 0, "TASK146_CLICK")
    _r(w.get("retry") == 0, "TASK146_RETRY")
    _r(w.get("followup_opens") == 0, "TASK146_FOLLOWUP")
    _r(w.get("raw_payload_persistence") is False, "TASK146_RAW")

    e=x.get("epistemic_semantics") or {}
    _r(e.get("positive_candidate_discovery_allowed") is True, "TASK146_POSITIVE")
    _r(e.get("negative_exhaustive_conclusion_allowed") is False, "TASK146_NEGATIVE")
    _r(e.get("pncp_no_match_allowed") is False, "TASK146_NOMATCH")
    _r(e.get("administrative_identifier_candidate_max_status") == "CORROBORATED", "TASK146_STATUS")
    _r(e.get("primary_municipal_verification_required") is True, "TASK146_PRIMARY")
    for k in ("automatic_financial_identity","automatic_transaction_identity","automatic_supplier_linkage"):
        _r(e.get(k) is False, f"TASK146_{k.upper()}")

    r=x.get("remote_effects_in_design") or {}
    _r(r and all(v is False for v in r.values()), "TASK146_REMOTE")
    return x


def load(path: str | Path) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    _r(isinstance(obj,dict),"TASK146_OBJECT")
    return validate_task146_contract(obj)
