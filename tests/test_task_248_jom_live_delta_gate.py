import copy
import json
import unittest
from pathlib import Path

from scripts.github_task_248_jom_live_delta_gate import EVIDENCE, validate


class Task248JomLiveDeltaGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(Path(EVIDENCE).read_text(encoding="utf-8"))

    def test_canonical_evidence_passes(self):
        validate(copy.deepcopy(self.evidence))

    def test_rejects_edition_mutation(self):
        data = copy.deepcopy(self.evidence)
        data["delta_editions"][0]["edition"] = 9999
        with self.assertRaises(ValueError):
            validate(data)

    def test_rejects_pdf_download_side_effect(self):
        data = copy.deepcopy(self.evidence)
        data["execution"]["document_download_count"] = 1
        with self.assertRaises(ValueError):
            validate(data)

    def test_rejects_recurrence_activation(self):
        data = copy.deepcopy(self.evidence)
        data["execution"]["recurrence_performed"] = True
        with self.assertRaises(ValueError):
            validate(data)

    def test_rejects_result_hash_mutation(self):
        data = copy.deepcopy(self.evidence)
        data["source_result"]["result_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate(data)


if __name__ == "__main__":
    unittest.main()
