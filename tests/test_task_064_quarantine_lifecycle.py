from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.quarantine_lifecycle import (
    can_release,
    can_release_to_routing,
    content_read_allowed_by_quarantine_state,
    load_quarantine_contract,
    next_quarantine_state,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "quarantine_lifecycle.v1.json"

class Task064Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.contract = load_quarantine_contract(CONTRACT)

    def test_out_of_scope_archives_by_default(self):
        self.assertEqual(next_quarantine_state("SOURCE_OUTSIDE_AUTHORIZED_FOLDER_SCOPE", self.contract), "ARCHIVED_NO_ACTION")

    def test_unknown_family_gets_metadata_review_only(self):
        self.assertEqual(next_quarantine_state("UNRECOGNIZED_FAMILY", self.contract), "METADATA_REVIEWED")

    def test_quarantine_never_authorizes_content(self):
        for state in self.contract["states"]:
            self.assertFalse(content_read_allowed_by_quarantine_state(state))

    def test_release_requires_all_proofs(self):
        self.assertTrue(can_release(cause_resolved=True, rule_version="v1", provenance_recorded=True, authorized_scope_confirmed=True))
        self.assertFalse(can_release(cause_resolved=True, rule_version=None, provenance_recorded=True, authorized_scope_confirmed=True))

    def test_routing_release_requires_family_rule_and_maturity_entry(self):
        self.assertTrue(can_release_to_routing(release_ok=True, family_known=True, controller_rule_match=True, maturity_entry_exists=True))
        self.assertFalse(can_release_to_routing(release_ok=True, family_known=True, controller_rule_match=False, maturity_entry_exists=True))

if __name__ == "__main__": unittest.main()
