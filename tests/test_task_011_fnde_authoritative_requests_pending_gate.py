import copy
import json
import unittest
from scripts.github_task_011_fnde_authoritative_requests_pending_gate import DECISION, EVIDENCE, validate


class PendingRequestsGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    def reject(self, fn):
        data = copy.deepcopy(self.data); fn(data)
        with self.assertRaises(ValueError): validate(data)
    def test_current_manifest_passes(self): self.assertEqual(validate(copy.deepcopy(self.data)), DECISION)
    def test_rejects_protocol_swap_typo_and_mapping(self):
        self.reject(lambda d: d["requests"][0].update(protocol=d["requests"][1]["protocol"]))
        self.reject(lambda d: d["requests"][1].update(protocol="23546.111503/2026-96"))
        self.reject(lambda d: d["requests"][2].update(blocker_id="B1_NUM_POPU"))
    def test_rejects_authority_deadline_and_received(self):
        self.reject(lambda d: d.update(authority="IBGE")); self.reject(lambda d: d.update(deadline="2026-09-22"))
        self.reject(lambda d: d["requests"][0].update(response_status="RECEIVED"))
    def test_rejects_every_target_proposition_mutation(self):
        self.reject(lambda d: d["requests"][0]["target_propositions"].__setitem__(0, "text drift"))
        self.reject(lambda d: d["requests"][1]["target_propositions"].pop())
        self.reject(lambda d: d["requests"][2]["target_propositions"].append("extra proposition"))
        self.reject(lambda d: d["requests"][0]["target_propositions"].reverse())
        self.reject(lambda d: d["requests"][1].update(target_propositions=copy.deepcopy(d["requests"][0]["target_propositions"])))
    def test_request_never_promotes_semantics_or_downstream(self):
        for key, value in (("S1_NUM_POPU", "PROVEN"), ("S2_FINANCIAL_ALIAS_BRIDGE", "PROVEN"), ("CURRENTLY_EFFECTIVE_DECLARATION", "PROVEN"), ("gold_2025", "PROVEN"), ("closed_annual_series", "2016-2025"), ("release_0_8_0", "ACTIVE"), ("year_2026", "PROVEN")):
            with self.subTest(key=key): self.reject(lambda d, k=key, v=value: d["canonical_state"].update({k: v}))


if __name__ == "__main__": unittest.main()
