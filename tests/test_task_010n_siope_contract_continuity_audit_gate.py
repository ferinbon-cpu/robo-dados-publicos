import copy
import json
import unittest
from pathlib import Path

from scripts.github_task_010n_siope_contract_continuity_audit_gate import EVIDENCE, validate


class Task010NContractContinuityAuditGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(Path(EVIDENCE).read_text(encoding="utf-8"))

    def test_pinned_evidence_passes(self):
        validate(copy.deepcopy(self.data))

    def test_rejects_canonical_promotion(self):
        data = copy.deepcopy(self.data)
        data["canonical_state"]["year_2025"] = "PROVEN"
        with self.assertRaisesRegex(ValueError, "canonical state"):
            validate(data)

    def test_rejects_2025_in_closed_series(self):
        data = copy.deepcopy(self.data)
        data["canonical_state"]["closed_annual_series"] = "2016-2025"
        with self.assertRaisesRegex(ValueError, "canonical state"):
            validate(data)

    def test_rejects_gold_2025(self):
        data = copy.deepcopy(self.data)
        data["scope"]["gold_2025_computed"] = True
        with self.assertRaisesRegex(ValueError, "Gold 2025"):
            validate(data)

    def test_rejects_network(self):
        data = copy.deepcopy(self.data)
        data["scope"]["network_requests"] = 1
        with self.assertRaisesRegex(ValueError, "offline"):
            validate(data)

    def test_rejects_positive_break_from_absence(self):
        data = copy.deepcopy(self.data)
        data["positive_break_audit"]["result"] = "POSITIVE_SEMANTIC_BREAK_FOUND"
        with self.assertRaisesRegex(ValueError, "absence of evidence"):
            validate(data)

    def test_rejects_invalid_result_pair(self):
        data = copy.deepcopy(self.data)
        data["result"] = {"class": "B", "code": "CONTINUITY_SUPPORTED_NO_POSITIVE_BREAK_FOUND"}
        with self.assertRaisesRegex(ValueError, "A/B/C"):
            validate(data)

    def test_rejects_authorization(self):
        data = copy.deepcopy(self.data)
        data["guards"]["semantic_promotion_authorized"] = True
        with self.assertRaisesRegex(ValueError, "authorizations"):
            validate(data)


if __name__ == "__main__":
    unittest.main()
