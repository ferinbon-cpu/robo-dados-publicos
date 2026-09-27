from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.review_queue import (
    build_review_item,
    can_resolve_to_auto,
    load_review_contract,
    order_review_queue,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "review_queue.v1.json"


class Task063Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_review_contract(CONTRACT)

    def test_schema_drift_has_top_priority(self):
        item = build_review_item({"file_id":"x","title":"a","family":"PPA","reasons":["KNOWN_FAMILY_REQUIRES_SUPERVISED_REVIEW","SCHEMA_DRIFT"]}, self.contract)
        self.assertEqual(item.reason, "SCHEMA_DRIFT")
        self.assertEqual(item.priority, 1)

    def test_multiple_family_match_gets_role_resolution(self):
        item = build_review_item({"file_id":"x","title":"SOURCE_JOM_PPA.pdf","family":None,"reasons":["MULTIPLE_FAMILY_MATCHES"]}, self.contract)
        self.assertEqual(item.action, "RESOLVE_PRIMARY_DOCUMENT_ROLE")

    def test_unknown_review_reason_defaults_to_maturity_proof(self):
        item = build_review_item({"file_id":"x","title":"x","family":"FUNDEB","reasons":["SOMETHING_NEW"]}, self.contract)
        self.assertEqual(item.reason, "MATURITY_NOT_EXECUTION_READY")

    def test_queue_order_is_deterministic(self):
        a = build_review_item({"file_id":"2","title":"B","family":"PPA","reasons":["KNOWN_FAMILY_REQUIRES_SUPERVISED_REVIEW"]}, self.contract)
        b = build_review_item({"file_id":"1","title":"A","family":"PPA","reasons":["SCHEMA_DRIFT"]}, self.contract)
        self.assertEqual(order_review_queue([a,b])[0].reason, "SCHEMA_DRIFT")

    def test_auto_resolution_requires_all_proof_fields(self):
        self.assertTrue(can_resolve_to_auto(family_known=True,maturity_ready=True,rule_version="v1",provenance_recorded=True))
        self.assertFalse(can_resolve_to_auto(family_known=True,maturity_ready=False,rule_version="v1",provenance_recorded=True))
        self.assertFalse(can_resolve_to_auto(family_known=True,maturity_ready=True,rule_version=None,provenance_recorded=True))


if __name__ == "__main__":
    unittest.main()
