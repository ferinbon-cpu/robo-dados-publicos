"""Offline preflight for a separately authorized, manual TASK284 browser session.

No networking or browser action is implemented. A PASS validates an observation
of an explicit submit binding, not the provenance of supplied observations and
never financial identity. The operator must inspect the fresh official DOM.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .task283_tda_tce_namespace_dossier import require

ROOT = Path(__file__).resolve().parents[2]


def load_contract() -> dict:
    data = json.loads((ROOT / "config/task284_tda_namespace_acquisition.v1.json").read_text())
    require(data["schema"] == "TASK284_TDA_NAMESPACE_ACQUISITION_V1", "TASK284_SCHEMA")
    require(data["automatic_execution_allowed"] is False, "TASK284_AUTOMATION")
    require(data["limits"] == {"browser_sessions": 1, "initial_navigations": 1, "top_area_actions": 1, "target_queries": 1, "retries": 0, "lateral_actions": 0, "pncp_requests": 0, "pagination": 0, "batch": 0, "direct_endpoint_requests": 0, "source_writes": 0}, "TASK284_LIMITS")
    require(data["capture"] == {"raw_html": False, "har": False, "cookies": False, "tokens": False, "hidden_values": False, "control_values": False, "only_sanitized_observations_and_hashes": True}, "TASK284_CAPTURE")
    require(data["payment_attribution_authorized"] is False and data["positive_witness_automatic_promotion"] is False and data["query_result_is_namespace_proof"] is False, "TASK284_PROMOTION")
    return data


def validate_binding(observed: dict) -> dict:
    contract = load_contract()
    require(observed.get("area_name") == contract["detail_area"]["name"] and observed.get("area_origin") == contract["detail_area"]["origin"], "TASK284_AREA_IDENTITY")
    aid = observed.get("area_id", "")
    require(isinstance(aid, str) and re.fullmatch(r"[A-Za-z0-9_]{1,100}", aid) is not None, "TASK284_AREA_ID")
    require(observed.get("area_count") == 1, "TASK284_AREA_NOT_UNIQUE")
    fid = "AREAFILTER_" + aid
    require(observed.get("filter_id") == fid, "TASK284_FILTER_ROOT")
    require(observed.get("number_id") == "FILTEREDIT_" + aid + "_epn" and observed.get("number_count") == 1 and observed.get("number_label") == "Nro Empenho", "TASK284_NUMBER_BINDING")
    require(observed.get("year_id") == "FILTERCOMBO_" + aid + "_exe" and observed.get("year_count") == 1 and observed.get("year_label") == "Exercício" and observed.get("year_2026_option_count") == 1, "TASK284_YEAR_BINDING")
    require(observed.get("controls_inside_filter") is True, "TASK284_CONTROL_SCOPE")
    require(observed.get("submit_count") == 1 and observed.get("submit_visible") is True, "TASK284_SUBMIT_NOT_UNIQUE")
    # Only the already specified exact argument is executable by this gate.
    # An AreaId argument needs a reviewed extension grounded in official source.
    handler = observed.get("submit_handler", "")
    require(isinstance(handler, str) and re.fullmatch(r"\s*(?:return\s+)?submmitApply\(['\"]" + re.escape(fid) + r"['\"]\);?\s*(?:return false;?)?\s*", handler) is not None, "TASK284_SUBMIT_ARGUMENT")
    require(observed.get("numeric_query_3286_explicitly_supported") is True, "TASK284_QUERY_SYNTAX")
    return {"status": "PASS_MANUAL_QUERY_BINDING_ONLY", "namespace_identity_proven": False, "payment_attribution_authorized": False}
