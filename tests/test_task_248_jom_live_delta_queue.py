from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/github_task_248_jom_live_delta_queue_gate.py"

spec = importlib.util.spec_from_file_location("task248_gate", GATE_PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class Task248JomLiveDeltaQueueTest(unittest.TestCase):
    def setUp(self) -> None:
        self.evidence = json.loads(gate.EVIDENCE.read_text(encoding="utf-8"))
        self.queue = json.loads(gate.QUEUE.read_text(encoding="utf-8"))
        self.task247 = json.loads(gate.TASK247.read_text(encoding="utf-8"))

    def test_canonical_files_pass(self) -> None:
        result = gate.validate_files()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["delta_editions"], [7321, 7322, 7323, 7324])
        self.assertFalse(result["document_download"])
        self.assertFalse(result["recurrence"])

    def test_tampered_live_result_hash_fails_closed(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["live_result"]["observed_month_count"] = 10
        with self.assertRaisesRegex(ValueError, "TASK248_RESULT_HASH_RECOMPUTE"):
            gate.validate_payloads(evidence, self.queue, self.task247)

    def test_duplicate_queue_edition_fails_closed(self) -> None:
        queue = copy.deepcopy(self.queue)
        queue["items"][3] = copy.deepcopy(queue["items"][2])
        with self.assertRaises(ValueError):
            gate.validate_payloads(self.evidence, queue, self.task247)

    def test_wrong_document_host_fails_closed(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        queue = copy.deepcopy(self.queue)
        bad = "https://example.com/fake.pdf"
        evidence["live_result"]["delta_editions"][0]["document_url"] = bad
        evidence["live_result"]["result_sha256"] = gate.canonical_result_hash(evidence["live_result"])
        evidence["provenance"]["sanitized_result_sha256"] = evidence["live_result"]["result_sha256"]
        queue["items"][0]["document_url"] = bad
        with self.assertRaises(ValueError):
            gate.validate_payloads(evidence, queue, self.task247)

    def test_any_remote_effect_in_task248_queue_fails_closed(self) -> None:
        queue = copy.deepcopy(self.queue)
        queue["effects"]["source_network"] = True
        with self.assertRaisesRegex(ValueError, "TASK248_EFFECT_NOT_INERT"):
            gate.validate_payloads(self.evidence, queue, self.task247)


if __name__ == "__main__":
    unittest.main()
