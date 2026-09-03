import json
from pathlib import Path

from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_077_BOUNDED_CONTRACTS_RESOLVER_PILOT_0.8.0.json"


def _evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_task077_selection_is_exactly_one_deterministic_contract_task():
    e = _evidence()
    assert e["base_main_sha"] == "fe34e13b0a476c74adf6356ed85f19e5433a7f35"
    assert e["authorization"]["token_index"] == 7
    assert e["source_plan"]["sha256"] == (
        "faf27576b5b2c3b3c542ae41eeac90c415da1d2f50b6ae8021e1c04bf246d7bc"
    )
    s = e["selection"]
    assert s["task_id"] == "RECTASK_39a82b72abdffa19e0dba705"
    assert s["task_canonical_sha256"] == (
        "33b6ae9cf63368f44f1f30225e15d27edebbaf5386c5e5c16563c38ee7ade2ca"
    )
    assert s["match_keys"] == {
        "year": 2025,
        "contract_number": "09/2025.",
        "cnpj": "12226306000140",
    }


def test_task077_selected_task_has_minimum_resolver_search_key():
    e = _evidence()
    task = {
        "target_source": "LIMEIRA_CONTRATOS",
        "match_keys": e["selection"]["match_keys"],
    }
    assert LimeiraContractsResolver.has_minimum_search_key(task) is True
    assert e["resolver_contract"]["minimum_search_key_present"] is True


def test_task077_stops_without_false_no_match_or_identity():
    e = _evidence()
    p = e["remote_pilot"]
    assert p["selected_task_budget"] == 1
    assert p["selected_tasks_attempted"] == 1
    assert p["surface_reached"] is True
    assert p["form_query_submitted"] is False
    assert p["resolver_completed"] is False
    assert p["candidate_records_returned"] == 0
    assert p["no_match_asserted"] is False
    assert p["stop_reason"] == "STOP_STATEFUL_FORM_QUERY_NOT_EXECUTED_WITHIN_BOUNDED_PILOT"
    assert all(value == 0 for value in e["semantic_audit"].values() if isinstance(value, int))
    assert e["semantic_audit"]["candidate_evidence_only"] is True
    assert all(value == 0 for value in e["hard_boundaries"].values())
    assert e["result"] == (
        "STOP_TASK077_PUBLIC_CONTRACTS_SEARCH_SURFACE_REACHED_FORM_QUERY_NOT_EXECUTED_NO_IDENTITY_ASSERTION"
    )
