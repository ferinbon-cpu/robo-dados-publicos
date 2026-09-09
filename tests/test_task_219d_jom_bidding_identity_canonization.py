import json
import unittest

from robo_dados_publicos.research.task219d_jom_bidding_identity_canonization import (
    ROOT,
    identity_key,
    load_config,
    sha256_path,
)


class TestTask219DJomBiddingIdentityCanonization(unittest.TestCase):
    def test_contract_forbids_weak_identity(self):
        cfg = load_config()
        rules = cfg["rules"]
        self.assertEqual(set(rules["modality_map"].values()), {6, 8, 9})
        self.assertFalse(rules["supplier_is_identity"])
        self.assertFalse(rules["date_is_identity"])
        self.assertFalse(rules["object_text_is_identity"])
        self.assertFalse(rules["semantic_similarity_is_identity"])
        self.assertTrue(rules["edital_publication_date_may_scope_search_only"])
        self.assertFalse(any(cfg["remote_effects"].values()))

    def test_materialized_counts_are_exact(self):
        cfg = load_config()
        new_path = ROOT / cfg["outputs"]["new_anchor_fixture"]
        idx_path = ROOT / cfg["outputs"]["combined_index"]
        seeds_path = ROOT / cfg["outputs"]["search_seeds"]
        ev_path = ROOT / cfg["outputs"]["evidence"]
        for path in (new_path, idx_path, seeds_path, ev_path):
            self.assertTrue(path.is_file())

        new = [json.loads(x) for x in new_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        self.assertEqual(len(new), 246)
        self.assertEqual(len({identity_key(r) for r in new}), 130)

        index = json.loads(idx_path.read_text(encoding="utf-8"))
        self.assertEqual(len(index["identities"]), 143)
        by_mod = {
            str(mid): sum(1 for r in index["identities"] if r["modality_id"] == mid)
            for mid in (6, 8, 9)
        }
        self.assertEqual(by_mod, {"6": 126, "8": 13, "9": 4})
        self.assertEqual(sum(1 for r in index["identities"] if r["has_edital_seed"]), 49)

        seeds = json.loads(seeds_path.read_text(encoding="utf-8"))
        self.assertEqual(seeds["seed_count"], 35)
        self.assertTrue(all(s["date_role"] == "SEARCH_SCOPE_ONLY_NOT_IDENTITY" for s in seeds["seeds"]))
        self.assertTrue(all(s["target_identity_count"] >= 1 for s in seeds["seeds"]))

        evidence = json.loads(ev_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["counts"]["overlap_unique_identities"], 8)
        self.assertEqual(evidence["counts"]["new_only_unique_identities"], 122)
        self.assertEqual(evidence["counts"]["combined_unique_identities"], 143)
        self.assertEqual(evidence["counts"]["combined_daily_search_seed_count"], 35)
        self.assertFalse(evidence["scientific_adjudication"]["pncp_match_proven_by_this_task"])
        self.assertEqual(evidence["scientific_adjudication"]["contextual_paths_after"], 34)

    def test_evidence_hashes_match_outputs(self):
        cfg = load_config()
        ev = json.loads((ROOT / cfg["outputs"]["evidence"]).read_text(encoding="utf-8"))
        out = ev["outputs"]
        self.assertEqual(sha256_path(ROOT / out["new_anchor_fixture"]), out["new_anchor_fixture_sha256"])
        self.assertEqual(sha256_path(ROOT / out["combined_index"]), out["combined_index_sha256"])
        self.assertEqual(sha256_path(ROOT / out["search_seeds"]), out["search_seeds_sha256"])


if __name__ == "__main__":
    unittest.main()
