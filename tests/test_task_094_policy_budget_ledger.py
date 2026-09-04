from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.research.budget_ledger import (
    BudgetLedgerStop,
    budget_event_to_research_entity,
    budget_identity_sha256,
    load_budget_ledger_contract,
    reconstruct_budget_snapshot,
    validate_budget_event,
)
from robo_dados_publicos.research.ontology import validate_entity


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/policy_budget_ledger.v1.json"


IDENTITY = {
    "entity": "LIMEIRA",
    "fiscal_year": 2026,
    "org": "EDUCACAO",
    "unit": "SME",
    "function": "12",
    "subfunction": "361",
    "program": "2001",
    "action": "2680",
    "expense_nature": "3.3.90.39",
    "funding_source": "01",
}


def event(
    suffix: str,
    event_type: str,
    amount: str,
    effective_date: str,
    *,
    status: str = "PROVEN",
    identity=None,
    sequence: int = 0,
):
    evidence = [] if status not in {"PROVEN", "CORROBORATED"} else [f"EVIDENCE:{suffix}"]
    return {
        "event_id": f"BUDGET_EVENT:{suffix}",
        "event_type": event_type,
        "effective_date": effective_date,
        "sequence": sequence,
        "amount": amount,
        "assertion_status": status,
        "evidence_ids": evidence,
        "source_document_id": "DOC:BUDGET_2026",
        "identity": dict(IDENTITY if identity is None else identity),
        "attributes": {},
    }


class TestTask094PolicyBudgetLedger(unittest.TestCase):
    def test_contract_is_t0_and_remote_effect_free(self):
        contract = load_budget_ledger_contract(CONTRACT)
        self.assertEqual("POLICY_BUDGET_LEDGER_V1", contract["schema"])
        self.assertEqual(["PROVEN", "CORROBORATED"], contract["default_canonical_statuses"])
        self.assertTrue(all(value is False for value in contract["remote_effects"].values()))

    def test_budget_identity_is_exact_multidimensional_not_label_similarity(self):
        first = budget_identity_sha256(IDENTITY)
        second = budget_identity_sha256({**IDENTITY, "action": "2720"})
        self.assertEqual(64, len(first))
        self.assertNotEqual(first, second)

    def test_reconstructs_authorization_and_execution_stages(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "1000.00", "2026-01-01"),
            event("SUP", "AUTHORIZATION_SUPPLEMENT", "200.00", "2026-03-01"),
            event("EMP", "COMMITMENT", "800.00", "2026-04-01"),
            event("LIQ", "LIQUIDATION", "700.00", "2026-05-01"),
            event("PAG", "PAYMENT", "600.00", "2026-06-01"),
            event("ANU", "AUTHORIZATION_CANCEL", "100.00", "2026-07-01"),
        ]
        snapshot = reconstruct_budget_snapshot(events)
        self.assertEqual("1100.00", snapshot["authorization_current"])
        self.assertEqual("800.00", snapshot["committed"])
        self.assertEqual("700.00", snapshot["liquidated"])
        self.assertEqual("600.00", snapshot["paid"])
        self.assertEqual("300.00", snapshot["available_authorization"])
        self.assertFalse(snapshot["policy_attribution_inferred"])
        self.assertEqual(6, len(snapshot["history"]))

    def test_as_of_reconstructs_prior_budget_state(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "1000.00", "2026-01-01"),
            event("SUP", "AUTHORIZATION_SUPPLEMENT", "200.00", "2026-03-01"),
            event("EMP", "COMMITMENT", "800.00", "2026-04-01"),
        ]
        snapshot = reconstruct_budget_snapshot(events, as_of="2026-03-15")
        self.assertEqual("1200.00", snapshot["authorization_current"])
        self.assertEqual("0.00", snapshot["committed"])
        self.assertEqual(["BUDGET_EVENT:EMP"], snapshot["after_as_of_event_ids"])

    def test_candidate_event_is_preserved_but_excluded_from_canonical_state(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "1000.00", "2026-01-01"),
            event(
                "CAND",
                "COMMITMENT",
                "900.00",
                "2026-02-01",
                status="CANDIDATE",
            ),
            event("EMP", "COMMITMENT", "300.00", "2026-02-02"),
        ]
        snapshot = reconstruct_budget_snapshot(events)
        self.assertEqual("300.00", snapshot["committed"])
        self.assertEqual(
            ["BUDGET_EVENT:CAND"],
            snapshot["excluded_noncanonical_event_ids"],
        )

    def test_commitment_cannot_exceed_current_authorization(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01"),
            event("EMP", "COMMITMENT", "100.01", "2026-02-01"),
        ]
        with self.assertRaisesRegex(BudgetLedgerStop, "COMMITTED_EXCEEDS_AUTHORIZATION"):
            reconstruct_budget_snapshot(events)

    def test_liquidation_cannot_exceed_commitment(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01"),
            event("EMP", "COMMITMENT", "80.00", "2026-02-01"),
            event("LIQ", "LIQUIDATION", "80.01", "2026-03-01"),
        ]
        with self.assertRaisesRegex(BudgetLedgerStop, "LIQUIDATED_EXCEEDS_COMMITTED"):
            reconstruct_budget_snapshot(events)

    def test_payment_cannot_exceed_liquidation(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01"),
            event("EMP", "COMMITMENT", "80.00", "2026-02-01"),
            event("LIQ", "LIQUIDATION", "70.00", "2026-03-01"),
            event("PAG", "PAYMENT", "70.01", "2026-04-01"),
        ]
        with self.assertRaisesRegex(BudgetLedgerStop, "PAID_EXCEEDS_LIQUIDATED"):
            reconstruct_budget_snapshot(events)

    def test_authorization_cancel_cannot_invade_committed_balance(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01"),
            event("EMP", "COMMITMENT", "80.00", "2026-02-01"),
            event("ANU", "AUTHORIZATION_CANCEL", "21.00", "2026-03-01"),
        ]
        with self.assertRaisesRegex(BudgetLedgerStop, "COMMITTED_EXCEEDS_AUTHORIZATION"):
            reconstruct_budget_snapshot(events)

    def test_stage_cancellation_is_explicit_and_cannot_make_balance_negative(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01"),
            event("EMP", "COMMITMENT", "80.00", "2026-02-01"),
            event("EST", "COMMITMENT_CANCEL", "80.01", "2026-03-01"),
        ]
        with self.assertRaisesRegex(BudgetLedgerStop, "NEGATIVE_NET_BALANCE"):
            reconstruct_budget_snapshot(events)

    def test_mixed_budget_identities_are_forbidden_in_one_snapshot(self):
        other = {**IDENTITY, "action": "2720"}
        events = [
            event("AUTH1", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01"),
            event(
                "AUTH2",
                "AUTHORIZATION_INITIAL",
                "100.00",
                "2026-01-01",
                identity=other,
            ),
        ]
        with self.assertRaisesRegex(BudgetLedgerStop, "MIXED_BUDGET_IDENTITIES"):
            reconstruct_budget_snapshot(events)

    def test_negative_or_overprecision_amount_is_forbidden(self):
        for bad in ("-1.00", "1.001", "abc", "0.00"):
            with self.subTest(amount=bad):
                with self.assertRaisesRegex(BudgetLedgerStop, "TASK094_AMOUNT"):
                    validate_budget_event(
                        event("BAD", "AUTHORIZATION_INITIAL", bad, "2026-01-01")
                    )

    def test_duplicate_event_id_fails_closed(self):
        duplicate = event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01")
        with self.assertRaisesRegex(BudgetLedgerStop, "DUPLICATE_EVENT_ID"):
            reconstruct_budget_snapshot([duplicate, dict(duplicate)])

    def test_empty_event_list_fails_closed(self):
        with self.assertRaisesRegex(BudgetLedgerStop, "EVENTS_EMPTY"):
            reconstruct_budget_snapshot([])

    def test_invalid_canonical_status_selection_fails_closed(self):
        events = [event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01")]
        with self.assertRaisesRegex(BudgetLedgerStop, "CANONICAL_STATUSES_EMPTY"):
            reconstruct_budget_snapshot(events, canonical_statuses=[])
        with self.assertRaisesRegex(BudgetLedgerStop, "CANONICAL_STATUSES_INVALID"):
            reconstruct_budget_snapshot(events, canonical_statuses=["PROVEN", "NOT_A_STATUS"])

    def test_as_of_before_all_events_returns_zero_state_and_future_event_list(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-02-01"),
            event("EMP", "COMMITMENT", "20.00", "2026-03-01"),
        ]
        snapshot = reconstruct_budget_snapshot(events, as_of="2026-01-31")
        self.assertEqual("0.00", snapshot["authorization_current"])
        self.assertEqual("0.00", snapshot["committed"])
        self.assertEqual("0.00", snapshot["liquidated"])
        self.assertEqual("0.00", snapshot["paid"])
        self.assertEqual([], snapshot["applied_event_ids"])
        self.assertEqual(
            ["BUDGET_EVENT:AUTH", "BUDGET_EVENT:EMP"],
            snapshot["after_as_of_event_ids"],
        )

    def test_as_of_is_inclusive_of_events_on_cutoff_date(self):
        events = [
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01"),
            event("EMP", "COMMITMENT", "20.00", "2026-02-01"),
        ]
        snapshot = reconstruct_budget_snapshot(events, as_of="2026-02-01")
        self.assertEqual("20.00", snapshot["committed"])
        self.assertEqual([], snapshot["after_as_of_event_ids"])

    def test_contract_rejects_non_boolean_false_remote_effect(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract["remote_effects"]["network"] = 0
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(BudgetLedgerStop, "CONTRACT_REMOTE_EFFECT"):
                load_budget_ledger_contract(path)

    def test_contract_rejects_required_identity_dimension_drift(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract["required_identity_dimensions"] = ["entity"]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(
                BudgetLedgerStop,
                "CONTRACT_REQUIRED_IDENTITY_DIMENSIONS",
            ):
                load_budget_ledger_contract(path)

    def test_budget_event_projection_rejects_invalid_canonical_event(self):
        invalid = event("BADPROJ", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01")
        invalid["evidence_ids"] = []
        with self.assertRaisesRegex(
            BudgetLedgerStop,
            "CANONICAL_EVENT_EVIDENCE_REQUIRED",
        ):
            budget_event_to_research_entity(invalid)

    def test_duplicate_canonical_statuses_fail_closed(self):
        events = [event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01")]
        with self.assertRaisesRegex(BudgetLedgerStop, "CANONICAL_STATUSES_INVALID"):
            reconstruct_budget_snapshot(
                events,
                canonical_statuses=["PROVEN", "PROVEN"],
            )

    def test_budget_event_projects_into_generic_research_entity(self):
        research_entity = budget_event_to_research_entity(
            event("AUTH", "AUTHORIZATION_INITIAL", "100.00", "2026-01-01")
        )
        validated = validate_entity(research_entity)
        self.assertEqual("BUDGET_EVENT", validated["type"])
        self.assertEqual("BUDGET_EVENT:AUTH", validated["id"])
        self.assertEqual("2026-01-01", validated["valid_from"])


if __name__ == "__main__":
    unittest.main()
