import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_071_LIVE_JOURNAL_BRONZE_BATCH_0.8.0.json"
AUDIT = ROOT / "config/batch_run_manifest.v1.json"


def test_task071_satisfies_batch_audit_contract():
    e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    c = json.loads(AUDIT.read_text(encoding="utf-8"))
    for field in c["required_fields"]:
        assert field in e
    assert len(e["item_decisions"]) == e["counters"]["metadata_records"] == 3
    assert e["final_readback_verified"] is True
    assert e["authorization_id"] == "AUTH_10_INBOX_JORNAL_OFICIAL_V1"
    assert e["counters"]["drive_writes"] == e["counters"]["bronze_writes"] == 3
    assert e["counters"]["silver_writes"] == 0
    assert e["counters"]["gold_writes"] == 0
    assert e["counters"]["serving_writes"] == 0
    assert e["counters"]["publications"] == 0


def test_task071_readback_is_byte_identical():
    e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert len(e["bronze_results"]) == 3
    for item in e["bronze_results"]:
        assert item["readback_match"] is True
        assert item["source_bytes"] == item["readback_bytes"]
        assert item["source_sha256"] == item["readback_sha256"]
        assert len(item["source_sha256"]) == 64


def test_task071_keeps_promotion_boundaries_closed():
    e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    h = e["hard_boundaries"]
    assert all(h[k] == 0 for k in ("semantic_parse","ocr","silver_writes","gold_writes","rag_writes","serving_writes","publications","source_moves","source_deletes","bronze_overwrites"))
    assert e["dedupe"]["same_title_or_size_used_as_duplicate_proof"] is False
    assert e["dedupe"]["sha256_is_content_identity"] is True
