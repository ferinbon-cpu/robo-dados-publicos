from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.research.task253_jom_pncp_explicit_control_canonization import (
    Task253Error,
    build_explicit_pncp_anchors,
    load_config,
    normalize_explicit_pncp_controls,
    validate_committed_outputs,
    validate_strong_anchors,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task253_jom_pncp_explicit_control_canonization.v1.json"
EVENTS = ROOT / "docs/evidence/fixtures/task253/TASK_253_EXPLICIT_PNCP_SOURCE_EVENTS.jsonl"
PNCP = ROOT / "docs/evidence/fixtures/task253/TASK_253_EXPLICIT_PNCP_CONTROL_ANCHORS.jsonl"
STRONG = ROOT / "docs/evidence/fixtures/task253/TASK_253_TASK252_STRONG_IDENTITY_ANCHORS.jsonl"


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class Task253CanonizationTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(CONFIG)
        self.events = load_jsonl(EVENTS)
        self.pncp = load_jsonl(PNCP)
        self.strong = load_jsonl(STRONG)

    def test_full_repository_gate_passes(self):
        result = validate_committed_outputs(ROOT)
        self.assertEqual(result["status"], "PASS_TASK253_JOM_PNCP_EXPLICIT_CONTROL_CANONIZATION")
        self.assertEqual(result["explicit_pncp_controls"], 8)
        self.assertEqual(result["projected_103_unique_identities"], 317)

    def test_eight_controls_rederive_exactly(self):
        derived = build_explicit_pncp_anchors(self.events, self.cfg)
        self.assertEqual(derived, self.pncp)
        self.assertEqual(len(derived), 8)
        self.assertEqual(len({r["anchor_value"] for r in derived}), 8)
        self.assertTrue(all(r["evidence_class"] == "EXPLICIT_PNCP_ID_IN_OFFICIAL_JOM_TEXT" for r in derived))

    def test_spacing_noise_normalizes_without_similarity(self):
        text = "PNCP ID : 45132495000140 -1-00646 / 2026"
        self.assertEqual(normalize_explicit_pncp_controls(text, self.cfg), ["45132495000140-1-000646/2026"])

    def test_foreign_cnpj_fails_closed(self):
        with self.assertRaisesRegex(Task253Error, "TASK253_PNCP_FOREIGN_CNPJ"):
            normalize_explicit_pncp_controls("PNCP ID: 99999999999999-1-000001/2026", self.cfg)

    def test_wrong_year_fails_closed(self):
        with self.assertRaisesRegex(Task253Error, "TASK253_PNCP_YEAR_DRIFT"):
            normalize_explicit_pncp_controls("PNCP ID: 45132495000140-1-000001/2025", self.cfg)

    def test_event_source_hash_drift_fails_closed(self):
        altered = copy.deepcopy(self.events)
        altered[0]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(Task253Error, "TASK253_EVENT_SOURCE_SHA"):
            build_explicit_pncp_anchors(altered, self.cfg)

    def test_excerpt_drift_fails_closed(self):
        altered = copy.deepcopy(self.events)
        altered[0]["excerpt_redacted"] += " x"
        with self.assertRaisesRegex(Task253Error, "TASK253_EVENT_EXCERPT_SHA"):
            build_explicit_pncp_anchors(altered, self.cfg)

    def test_strong_anchor_counts(self):
        counts = validate_strong_anchors(self.strong, self.cfg)
        self.assertEqual(counts["strong_anchor_rows"], 20)
        self.assertEqual(counts["strong_anchor_events"], 18)
        self.assertEqual(counts["strong_unique_identities"], 18)
        self.assertEqual(counts["strong_unique_process_identities"], 11)
        self.assertEqual(counts["strong_unique_contract_identities"], 7)

    def test_remote_effects_are_all_false(self):
        self.assertTrue(self.cfg["remote_effects"])
        self.assertFalse(any(self.cfg["remote_effects"].values()))
        self.assertFalse(self.cfg["explicit_pncp_rule"]["remote_resolution_proven_by_this_task"])
        self.assertFalse(self.cfg["explicit_pncp_rule"]["tce_chain_proven_by_this_task"])


if __name__ == "__main__":
    unittest.main()
