from scripts.verify_task089_bounded_query_evidence import run


def test_task089_full_offline_evidence_verifier():
    out = run()
    assert out["status"] == "PASS_TASK089_BOUNDED_QUERY_EVIDENCE_OFFLINE"
    assert out["resolver_status"] == "NO_MATCH"
    assert out["request_count"] == 3
    assert out["candidate_count"] == 0
    assert out["future_execution_authorized"] is False
