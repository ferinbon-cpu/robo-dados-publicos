import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "config" / "normative_official_authority_snapshot_2026_09_11.v1.json"
READINESS = ROOT / "config" / "normative_sme_legal_authority_readiness.v1.json"


class TestTask233NormativeOfficialAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        cls.readiness = json.loads(READINESS.read_text(encoding="utf-8"))
        cls.packages = {x["source_package_id"]: x for x in cls.obj["packages"]}

    def test_snapshot_is_date_bound_and_has_exact_targets(self):
        self.assertEqual(self.obj["verified_at"], "2026-09-11")
        self.assertTrue(self.obj["snapshot_bound"])
        self.assertEqual(
            set(self.packages),
            {"PKG-LC41-1991", "PKG-LC461-2009", "PKG-LEI6089-2018", "PKG-VICE-DIRETOR"},
        )
        self.assertEqual(self.obj["summary"]["target_packages"], 4)

    def test_task232_targets_are_promoted_without_rewriting_readiness(self):
        prior = set(self.readiness["summary"]["next_official_vigency_targets"])
        self.assertEqual(prior, set(self.packages))
        self.assertEqual(self.readiness["summary"]["current_vigency_proven_items"], 0)

    def test_three_base_norms_are_officially_in_force(self):
        for package_id in ("PKG-LC41-1991", "PKG-LC461-2009", "PKG-LEI6089-2018"):
            self.assertTrue(self.packages[package_id]["official_status"].startswith("IN_FORCE_OFFICIAL_SNAPSHOT"))
            self.assertEqual(self.packages[package_id]["official_status_text"], "Em vigor")
        self.assertEqual(self.obj["summary"]["base_norms_officially_in_force"], 3)

    def test_lc41_recent_direct_amendment_is_explicit(self):
        acts = self.packages["PKG-LC41-1991"]["current_modifiers_or_related_acts"]
        self.assertEqual(len(acts), 1)
        act = acts[0]
        self.assertEqual(act["act"], "Lei Complementar nº 1.017/2026")
        self.assertEqual(act["relationship"], "DIRECT_STRUCTURAL_AMENDMENT")
        self.assertEqual(act["official_status"], "Em vigor")
        self.assertIn("article 50", act["effect_proven"])

    def test_lc461_modifier_roles_are_not_flattened(self):
        acts = {x["act"]: x for x in self.packages["PKG-LC461-2009"]["current_modifiers_or_related_acts"]}
        self.assertEqual(acts["Lei Complementar nº 949/2024"]["relationship"], "DIRECT_STRUCTURAL_AMENDMENT")
        self.assertEqual(acts["Lei Complementar nº 987/2025"]["relationship"], "DIRECT_STRUCTURAL_AMENDMENT")
        self.assertEqual(acts["Lei Complementar nº 1.014/2026"]["relationship"], "REMUNERATION_REVIEW_RELATED_ACT")
        self.assertEqual(
            acts["Lei Complementar nº 1.027/2026"]["relationship"],
            "DIRECT_STRUCTURAL_AMENDMENT_WITH_OFFICIAL_PUBLICATION_TRACE",
        )

    def test_lc1027_requires_post_approval_events(self):
        acts = {x["act"]: x for x in self.packages["PKG-LC461-2009"]["current_modifiers_or_related_acts"]}
        act = acts["Lei Complementar nº 1.027/2026"]
        self.assertEqual(act["proposal_label_status"], "Aprovado")
        self.assertEqual(act["official_status"], "ENACTED_AND_PUBLISHED_OFFICIAL_PROCESS_TRACE")
        joined = " ".join(act["later_process_events"])
        self.assertIn("Promulgado e Sancionado", joined)
        self.assertIn("published", joined)
        self.assertIn("7320", joined)
        self.assertIn("13-22", joined)
        self.assertNotEqual(act["proposal_label_status"], act["official_status"])

    def test_lc1027_index_lag_is_not_nonexistence(self):
        act = next(
            x for x in self.packages["PKG-LC461-2009"]["current_modifiers_or_related_acts"]
            if x["act"] == "Lei Complementar nº 1.027/2026"
        )
        self.assertEqual(
            act["index_status"],
            "LEGISLACAO_DIGITAL_SPECIFIC_1027_RECORD_NOT_ESTABLISHED_IN_THIS_SNAPSHOT",
        )
        self.assertEqual(
            act["index_guard"],
            "INDEX_LAG_NE_NONEXISTENCE_WHEN_OFFICIAL_PUBLICATION_TRACE_EXISTS",
        )

    def test_current_vice_director_framework_comes_from_official_lc461(self):
        lc = self.packages["PKG-LC461-2009"]
        vd = lc["current_primary_rules_selected"]["vice_director"]
        self.assertEqual(vd["legal_role"], "Posto de trabalho de suporte pedagogico")
        self.assertIn("Conselho de Escola", vd["selection_rule"])
        self.assertIn("SME", vd["selection_rule"])
        self.assertIn("mayoral designation", vd["selection_rule"])
        self.assertIn("3 years", vd["minimum_experience"])
        self.assertEqual(vd["authority_source_url"], "https://consulta.limeira.sp.leg.br/Normas/Exibir/2820")

    def test_legacy_vice_director_admin_package_remains_unresolved(self):
        pkg = self.packages["PKG-VICE-DIRETOR"]
        self.assertEqual(
            pkg["official_status"],
            "SPLIT_AUTHORITY_CURRENT_FRAMEWORK_VERIFIED_LEGACY_ADMIN_STATUS_UNRESOLVED",
        )
        legacy = pkg["legacy_local_admin_package"]
        self.assertEqual(legacy["current_official_status"], "UNRESOLVED")
        self.assertEqual(legacy["search_failure_meaning"], "NO_REPEAL_OR_VIGENCY_INFERENCE_ALLOWED")
        self.assertGreaterEqual(len(pkg["unresolved_components"]), 3)

    def test_lei6089_no_amendment_found_is_not_no_amendment_exists(self):
        pkg = self.packages["PKG-LEI6089-2018"]
        self.assertEqual(pkg["current_modifiers_or_related_acts"], [])
        self.assertIn("NOT_A_CLAIM_THAT_NONE_EXISTS", pkg["modifier_search_conclusion"])

    def test_authority_precedence_is_official_first(self):
        precedence = self.obj["authority_precedence"]
        self.assertEqual(precedence[0], "OFFICIAL_CURRENT_CONSOLIDATED_OR_STATUS_SOURCE")
        self.assertEqual(precedence[-1], "DERIVED_RAG_GUIDE_OR_TRAINING_MATERIAL")

    def test_required_fail_closed_guards(self):
        required = {
            "APPROVED_BILL_NE_ENACTED_LAW",
            "OFFICIAL_CONSOLIDATED_TEXT_GT_DERIVED_CORPUS_FOR_CURRENT_RULE",
            "BASE_LAW_IN_FORCE_NE_UNCHANGED_SINCE_ORIGINAL",
            "OLD_ADMIN_INSTRUCTION_NE_CURRENT_UNLESS_OFFICIAL_TRACE_FOUND",
            "CURRENT_STATUS_IS_SNAPSHOT_DATE_BOUND",
            "NO_REPEAL_INFERENCE_FROM_SEARCH_FAILURE",
            "LC1027_2026_MODIFIES_LC461",
            "INDEX_LAG_NE_NONEXISTENCE_WHEN_OFFICIAL_PUBLICATION_TRACE_EXISTS",
            "REMUNERATION_REVIEW_ACT_NE_STRUCTURAL_STATUTE_AMENDMENT",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(set(self.obj["global_guards"])))

    def test_remote_effects_are_read_only(self):
        effects = self.obj["remote_effects"]
        self.assertTrue(effects["source_network_read_only"])
        for key in ("drive_write", "serving", "publication", "schedule", "recurrence"):
            self.assertFalse(effects[key])
        self.assertEqual(self.obj["summary"]["contextual_coverage"], "38/38_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
