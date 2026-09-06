import copy
import json

import pytest

from robo_dados_publicos.research.task170_limeira_tda_accounting_discovery_gate import (
    DEFAULT_CONTRACT,
    Task170Stop,
    validate_contract,
)


def _write(tmp_path, obj):
    p = tmp_path / "task170.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def _base():
    return json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))


def test_task170_contract_passes():
    result = validate_contract()
    assert result["status"] == "PASS"
    assert result["selected_source"] == "LIMEIRA_TDA_PORTAL"
    assert result["live_authorized"] is False
    assert result["network_requests"] == 0


def test_task170_cannot_authorize_live(tmp_path):
    obj = _base()
    obj["authorization_boundary"]["live_discovery_authorized_now"] = True
    with pytest.raises(Task170Stop, match="TASK170_LIVE_BOUNDARY"):
        validate_contract(_write(tmp_path, obj))


def test_task170_rejects_wrong_source(tmp_path):
    obj = _base()
    obj["selected_source"]["source_id"] = "TCE_SP_2026_BULK"
    with pytest.raises(Task170Stop, match="TASK170_SOURCE"):
        validate_contract(_write(tmp_path, obj))


def test_task170_rejects_endpoint_guessing_permission(tmp_path):
    obj = _base()
    obj["future_live_discovery_gate"]["forbidden_discovery"].remove("endpoint_guessing")
    with pytest.raises(Task170Stop, match="TASK170_FORBIDDEN_DISCOVERY_MISSING"):
        validate_contract(_write(tmp_path, obj))


def test_task170_requires_blocked_access_not_no_data(tmp_path):
    obj = _base()
    obj["future_live_discovery_gate"]["access_barrier_semantics"]["redirect_to_login_logout_root_or_session_barrier"] = "NO_DATA"
    with pytest.raises(Task170Stop, match="TASK170_ACCESS_SEMANTICS"):
        validate_contract(_write(tmp_path, obj))


def test_task170_rejects_retry(tmp_path):
    obj = _base()
    obj["future_live_discovery_gate"]["request_budget"]["retry"] = 1
    with pytest.raises(Task170Stop, match="TASK170_RETRY_REDIRECT"):
        validate_contract(_write(tmp_path, obj))


def test_task170_preserves_unknown_financial_identity(tmp_path):
    obj = _base()
    obj["scientific_guards"]["current_financial_identity"] = "PROVEN"
    with pytest.raises(Task170Stop, match="TASK170_FINANCIAL_STATE"):
        validate_contract(_write(tmp_path, obj))


def test_task170_preserves_weak_join_guards(tmp_path):
    obj = _base()
    obj["promotion_preconditions_after_future_route_discovery"]["weak_joins_forbidden"].remove("semantic_similarity")
    with pytest.raises(Task170Stop, match="TASK170_WEAK_JOIN_GUARD"):
        validate_contract(_write(tmp_path, obj))
