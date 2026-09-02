import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_eiti_granular_execution_source_selection import (
    Task051Error,
    validate_task051_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E51 = ROOT / "docs/evidence/TASK_051_F01_EITI_GRANULAR_EXECUTION_SOURCE_SELECTION_0.8.0.json"
E49 = ROOT / "docs/evidence/TASK_049_F01_EITI_ACTION_LINKAGE_CLOSURE_REVIEW_0.8.0.json"
E50 = ROOT / "docs/evidence/TASK_050_F01_LOA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task051SourceSelectionTests(unittest.TestCase):
    def test_evidence_passes(self):
        result = validate_task051_evidence(load(E51), load(E49), load(E50))
        self.assertEqual(result["status"], "PASS_TASK051_GRANULAR_EXECUTION_SOURCE_SELECTION_REVIEW")
        self.assertEqual(result["next_gate"], "TASK_052_EXISTING_CUSTODY_GRANULAR_SOURCE_INVENTORY")
        self.assertTrue(result["authorization_required"])
        self.assertFalse(result["gold"])

    def test_fail_closed_if_ppa_search_reopened(self):
        evidence = load(E51)
        evidence["closed_paths"]["repeat_program_2001_action_label_search"] = True
        with self.assertRaises(Task051Error):
            validate_task051_evidence(evidence, load(E49), load(E50))

    def test_fail_closed_if_live_inventory_auto_authorized(self):
        evidence = load(E51)
        evidence["next_bounded_gate"]["authorization_required_before_live_inventory"] = False
        with self.assertRaises(Task051Error):
            validate_task051_evidence(evidence, load(E49), load(E50))

    def test_fail_closed_if_amount_equality_allowed(self):
        evidence = load(E51)
        evidence["not_sufficient_alone"].remove("AMOUNT_EQUALITY_ONLY")
        with self.assertRaises(Task051Error):
            validate_task051_evidence(evidence, load(E49), load(E50))


if __name__ == "__main__":
    unittest.main()
