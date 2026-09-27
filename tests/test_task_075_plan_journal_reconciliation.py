import json
from pathlib import Path

from robo_dados_publicos.reconciliation.planner import ReconciliationPlanner

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_075_PLAN_JOURNAL_RECONCILIATION_0.8.0.json"


def _evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_task075_exact_task074_gold_inputs_are_pinned():
    e = _evidence()
    assert e["base_main_sha"] == "0b650c43b7561f2b9c94e81399634bd18093a1fb"
    assert e["authorization"]["token_index"] == 5
    assert e["input_aggregate"] == {
        "gold_files": 3,
        "gold_events": 52,
        "bytes": 97913,
    }
    expected = {
        7024: "4e869604c7a870fb0e296e47682a6c821e6f0037a74d2726e3af3afd1ab79118",
        7119: "fbbaea5329eafcca4a2fca9ce1e363a7a65cef8aa4bc5230eaee8e696bab67ff",
        7127: "883eb8066734dbc05992a021b402aece3697de7d1caa542bd598ab9707860b32",
    }
    assert {item["edition"]: item["sha256"] for item in e["gold_inputs"]} == expected
    assert all(len(item["sha256"]) == 64 for item in e["gold_inputs"])


def test_task075_plan_is_unique_deterministic_and_bounded():
    e = _evidence()
    p = e["plan"]
    assert p["generated_tasks"] == 65
    assert p["unique_tasks"] == 65
    assert p["duplicate_task_ids"] == 0
    assert p["canonical_jsonl_bytes"] == 52843
    assert p["canonical_jsonl_sha256"] == (
        "faf27576b5b2c3b3c542ae41eeac90c415da1d2f50b6ae8021e1c04bf246d7bc"
    )
    assert sum(p["target_counts"].values()) == 65
    assert sum(p["status_counts"].values()) == 65
    assert sum(p["origin_source_task_counts"].values()) == 65
    assert p["target_counts"] == {
        "LIMEIRA_CONTRATOS": 5,
        "TCE_SP_DESPESAS": 4,
        "TDA_LIMEIRA": 5,
        "LIMEIRA_LICITACOES": 14,
        "SIAVE_LIMEIRA": 37,
    }


def test_task075_fail_closed_semantics_preserved():
    e = _evidence()
    assert ReconciliationPlanner.TARGETS["TDA_LIMEIRA"]["connector_state"] == (
        "BLOCKED_CONNECTOR_DISCOVERY"
    )
    assert e["plan"]["status_counts"] == {
        "READY_SEARCH": 60,
        "BLOCKED_CONNECTOR_DISCOVERY": 5,
    }
    audit = e["semantic_audit"]
    assert audit["tda_tasks_blocked"] == 5
    assert audit["match_candidate_promotions"] == 0
    assert audit["financial_identity_assertions"] == 0
    assert audit["serving_promotions"] == 0
    assert audit["publication_promotions"] == 0
    assert audit["identity_rule_required_per_task"] is True
    assert audit["supplier_or_value_alone_is_identity"] is False
    assert all(value == 0 for value in e["hard_boundaries"].values())
    assert e["result"] == (
        "PASS_TASK075_52_GOLD_EVENTS_65_UNIQUE_RECONCILIATION_TASKS_PLANNED_NO_IDENTITY_PROMOTION"
    )
