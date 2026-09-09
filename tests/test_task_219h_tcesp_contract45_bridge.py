import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219H_TCESP_CONTRACT45_BRIDGE_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219H_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219H_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219h-tcesp-contract45-bridge-live-once.yml"
TASK187 = ROOT / "config/task187_tcesp_rich_expenses_2026.v1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def test_task219h_live_workflow_removed_and_source_preserved():
    ev = load(EVIDENCE)
    assert not LIVE.exists()
    assert blob_sha(HIST) == ev["runtime"]["executed_workflow_blob_sha"]
    assert ev["runtime"]["historical_source_exact_blob_match"] is True
    assert ev["runtime"]["workflow_removed_after_run"] is True


def test_task219h_current_tcesp_snapshot_equals_task187():
    ev = load(EVIDENCE)
    old = load(TASK187)
    assert ev["source"]["zip_sha256"] == old["source"]["zip_sha256"]
    assert ev["source"]["csv_sha256"] == old["source"]["csv_sha256"]
    assert ev["source"]["row_count"] == old["observed"]["row_count"]
    assert ev["source"]["months"] == old["source"]["months_expected"]
    assert ev["source"]["current_snapshot_adds_new_months_vs_task187"] is False


def test_task219h_exact_supplier_chain_is_one_commitment():
    ev = load(EVIDENCE)
    chain = ev["tcesp_exact_supplier_chain"]
    assert chain["supplier_cnpj"] == "37457979000131"
    assert chain["unique_commitments"] == ["3286-2026"]
    assert chain["candidate_row_count"] == 3
    assert chain["all_rows_same_commitment"] is True
    assert {r["stage"] for r in chain["rows"]} == {"Empenhado", "Valor Liquidado", "Valor Pago"}


def test_task219h_stage_values_are_observed_not_balance_inference():
    ev = load(EVIDENCE)
    chain = ev["tcesp_exact_supplier_chain"]
    assert chain["observed_stage_amounts_brl"] == {
        "EMPENHADO": "174999.99",
        "LIQUIDADO": "17500.00",
        "PAGO": "17500.00",
    }
    assert chain["balance_or_contract_execution_fraction_inferred"] is False


def test_task219h_strong_procurement_identity_remains_fail_closed():
    ev = load(EVIDENCE)
    adj = ev["strong_identity_adjudication"]
    assert adj["exact_supplier_cnpj_match"] is True
    assert adj["supplier_accounting_candidate_proven"] is True
    assert adj["single_commitment_candidate_proven"] is True
    assert adj["strong_document_identifier_hit_count"] == 0
    assert adj["typed_contract_45_2026_found_in_tcesp"] is False
    assert adj["typed_process_902281_2025_found_in_tcesp"] is False
    assert adj["typed_bidding_10_2026_found_in_tcesp"] is False
    assert adj["jom_to_tcesp_procurement_identity_proven"] is False


def test_task219h_no_question_promotion_and_authorization_consumed():
    ev = load(EVIDENCE)
    st = ev["scientific_state"]
    assert st["new_accounting_identifier"] == "3286-2026"
    assert st["new_primary_control_evidence"] is True
    assert st["question_promotion_performed"] is False
    assert st["contextual_paths_after"] == 34
    assert st["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]
    assert ev["authorization_consumption"]["authorization_exhausted_for_future_network"] is True


def test_task219h_payload_contains_only_exact_supplier_candidates():
    p = load(PAYLOAD)
    assert p["target_cnpj"] == "37457979000131"
    assert p["candidate_count"] == 3
    assert p["strong_hit_count"] == 0
    assert all("37457979000131" in r["supplier_id"] for r in p["candidate_rows"])
    assert {r["commitment"].strip() for r in p["candidate_rows"]} == {"3286-2026"}
