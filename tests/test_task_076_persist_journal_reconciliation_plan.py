import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_076_PERSIST_JOURNAL_RECONCILIATION_PLAN_0.8.0.json"


def _evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_task076_exact_task075_plan_persisted_create_only():
    e = _evidence()
    assert e["base_main_sha"] == "9c8c01c77176a8cbf90a680b9aec381cfae963b2"
    assert e["authorization"]["token_index"] == 6
    source = e["source_plan"]
    persisted = e["persistence"]
    assert source["tasks"] == persisted["readback_bytes"] * 0 + 65
    assert source["bytes"] == persisted["bytes"] == persisted["readback_bytes"] == 52843
    assert source["sha256"] == persisted["sha256"] == persisted["readback_sha256"]
    assert source["sha256"] == (
        "faf27576b5b2c3b3c542ae41eeac90c415da1d2f50b6ae8021e1c04bf246d7bc"
    )
    assert persisted["create_only"] is True
    assert persisted["overwrite"] is False
    assert persisted["readback_match"] is True
    assert persisted["byte_for_byte_match"] is True


def test_task076_readback_semantics_remain_fail_closed():
    e = _evidence()
    r = e["readback_semantics"]
    assert r["tasks"] == 65
    assert r["unique_task_ids"] == 65
    assert r["status_counts"] == {
        "READY_SEARCH": 60,
        "BLOCKED_CONNECTOR_DISCOVERY": 5,
    }
    assert r["target_counts"] == {
        "LIMEIRA_CONTRATOS": 5,
        "TCE_SP_DESPESAS": 4,
        "TDA_LIMEIRA": 5,
        "LIMEIRA_LICITACOES": 14,
        "SIAVE_LIMEIRA": 37,
    }
    assert r["identity_rule_present_on_all_tasks"] is True


def test_task076_only_one_allowed_drive_create_occurred():
    e = _evidence()
    h = e["hard_boundaries"]
    assert h["drive_writes"] == 1
    assert h["drive_overwrites"] == 0
    for key, value in h.items():
        if key != "drive_writes":
            assert value == 0
    assert e["result"] == (
        "PASS_TASK076_RECONCILIATION_PLAN_GOLD_CREATE_ONLY_SHA256_READBACK_VERIFIED"
    )
