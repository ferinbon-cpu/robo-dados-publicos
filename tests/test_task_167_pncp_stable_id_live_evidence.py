import json
from pathlib import Path


EVIDENCE = Path("docs/evidence/TASK_167_PNCP_STABLE_ID_DIRECT_JSON_TRAVERSAL_0.8.0.json")


def load():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_task167_live_evidence_is_fail_closed():
    e = load()
    assert e["task"] == "TASK_167_PNCP_STABLE_ID_DIRECT_JSON_TRAVERSAL"
    assert e["execution"]["workflow_conclusion"] == "success"
    assert e["execution"]["raw_payload_persisted"] is False
    assert e["adjudication"]["requests_attempted"] == 10
    assert e["adjudication"]["successful_json_bodies"] == 0
    assert e["adjudication"]["candidate_accounting_signals"] == 0
    assert e["adjudication"]["transport_or_http_failure_is_no_data"] is False
    assert e["adjudication"]["pncp_no_data_created"] is False
    assert e["adjudication"]["eiti_financial_identity_proven"] is False
    assert e["adjudication"]["eiti_transaction_identity_proven"] is False
    assert e["adjudication"]["scientific_state"] == "UNCHANGED_UNKNOWN_FINANCIAL_IDENTITY"


def test_all_task167_routes_are_recorded_as_unavailable_not_absent():
    e = load()
    expected = {"DETAIL", "ITEMS", "HISTORY", "BUDGET_SOURCES", "LINKED_CONTRACTS"}
    for target in e["targets"]:
        assert set(target["routes"]) == expected
        assert target["detail_identity_validated_this_run"] is False
        for route in target["routes"].values():
            assert route["bytes_received"] == 0
            assert route["http_status"] in {502, 503}
            assert route["status"] == "SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
