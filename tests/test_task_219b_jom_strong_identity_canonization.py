import json
import unittest
from pathlib import Path

from robo_dados_publicos.research.task219b_jom_strong_identity_canonization import (
    ROOT,
    build_identity_index,
    derive_legacy_anchors,
    identity_key,
    load_config,
    sha256_path,
)


class TestTask219BJomStrongIdentityCanonization(unittest.TestCase):
    def test_config_is_offline_and_forbids_weak_identity(self):
        cfg = load_config()
        self.assertFalse(any(cfg["remote_effects"].values()))
        guards = cfg["identity_guards"]
        self.assertFalse(guards["cnpj_alone_is_identity"])
        self.assertFalse(guards["amount_similarity_is_identity"])
        self.assertFalse(guards["date_proximity_is_identity"])
        self.assertFalse(guards["object_text_is_identity"])
        self.assertFalse(guards["semantic_similarity_is_identity"])
        self.assertFalse(guards["end_to_end_chain_proven_by_this_task"])

    def test_legacy_task216_anchor_model_is_reproduced_exactly(self):
        cfg = load_config()
        path = ROOT / cfg["legacy_corpus"]["fixture"]
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        anchors = derive_legacy_anchors(events)
        self.assertEqual(len(events), 303)
        self.assertEqual(len(anchors), 54)
        self.assertEqual(len({row["event_id"] for row in anchors}), 48)
        self.assertEqual(len({identity_key(row) for row in anchors}), 42)

    def test_process_may_span_suppliers_but_contract_conflict_is_visible(self):
        old = [
            {"event_id": "A", "anchor_type": "PROCESS_IDENTITY", "anchor_value": "900.001/2026", "supplier_cnpj": "11111111000111"},
            {"event_id": "B", "anchor_type": "CONTRACT_IDENTITY", "anchor_value": "1/2026", "supplier_cnpj": "33333333000133"},
        ]
        new = [
            {"event_id": "C", "anchor_type": "PROCESS_IDENTITY", "anchor_value": "900.001/2026", "supplier_cnpj": "22222222000122"},
            {"event_id": "D", "anchor_type": "CONTRACT_IDENTITY", "anchor_value": "1/2026", "supplier_cnpj": "44444444000144"},
        ]
        got = build_identity_index(old, new)
        self.assertEqual(got["audit"]["process_identities_with_multiple_suppliers"], 1)
        self.assertEqual(got["audit"]["contract_identities_with_multiple_suppliers"], 1)

    def test_materialized_outputs_match_canonical_counts_and_hash(self):
        cfg = load_config()
        new_path = ROOT / cfg["outputs"]["new_anchor_fixture"]
        index_path = ROOT / cfg["outputs"]["combined_identity_index"]
        evidence_path = ROOT / cfg["outputs"]["evidence"]
        self.assertTrue(new_path.is_file())
        self.assertTrue(index_path.is_file())
        self.assertTrue(evidence_path.is_file())
        self.assertEqual(
            sha256_path(new_path),
            cfg["source_runtime"]["files"]["task219a_strong_identity_anchors.jsonl"],
        )
        rows = [json.loads(line) for line in new_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 395)
        self.assertEqual(len({identity_key(row) for row in rows}), 270)
        index = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual(len(index["identities"]), 303)
        self.assertEqual(index["counts"]["new_unique_identities"], 261)
        self.assertEqual(index["counts"]["combined_unique_identities"], 303)
        self.assertEqual(index["audit"]["contract_identities_with_multiple_suppliers"], 0)
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["scientific_adjudication"]["contextual_paths_after"], 34)
        self.assertFalse(evidence["scientific_adjudication"]["end_to_end_jom_pncp_tce_chain_proven"])
        self.assertEqual(
            evidence["scientific_adjudication"]["remaining_blockers"],
            ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"],
        )


if __name__ == "__main__":
    unittest.main()
