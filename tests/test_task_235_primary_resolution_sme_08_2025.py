import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "config" / "education_assignment_resolution_08_2025_primary.v1.json"
TASK234 = ROOT / "config" / "education_assignment_2026_authority.v1.json"


class TestTask235PrimaryResolutionSME08(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(PRIMARY.read_text(encoding="utf-8"))
        cls.prior = json.loads(TASK234.read_text(encoding="utf-8"))
        cls.articles = {row["article"]: row for row in cls.obj["article_index"]}

    def test_exact_primary_source_identity(self):
        src = self.obj["source"]
        self.assertEqual(src["act"], "Resolução SME nº 08, de 09 de dezembro de 2025")
        self.assertEqual(src["publication_label"], "(RETIFICAÇÃO)")
        self.assertEqual(src["edition"], 7139)
        self.assertEqual(src["publication_date"], "2025-12-16")
        self.assertEqual(src["resolution_page_span"], [168, 186])
        self.assertEqual(src["normative_article_span"], [1, 34])
        self.assertTrue(src["pdf_url"].endswith("u_137_15122025182852.pdf"))

    def test_article_index_is_complete_and_contiguous(self):
        self.assertEqual(len(self.obj["article_index"]), 34)
        self.assertEqual(set(self.articles), set(range(1, 35)))
        for number, row in self.articles.items():
            self.assertTrue(row["pages"], number)
            self.assertTrue(all(168 <= p <= 183 for p in row["pages"]), number)
            self.assertTrue(row["topic"].strip(), number)

    def test_annex_i_is_proven_and_bounded(self):
        annex = self.obj["annex_i"]
        self.assertEqual(annex["pages"], [184, 185, 186])
        self.assertEqual(len(annex["selected_schedule"]), 4)
        self.assertEqual(annex["selected_schedule"][-1]["date_range"], ["2026-01-15", "2026-01-16"])

    def test_binary_custody_is_not_fabricated(self):
        src = self.obj["source"]
        self.assertEqual(src["binary_custody_status"], "NOT_CUSTODIED_NO_BYTE_HASH")
        self.assertFalse(self.obj["summary"]["binary_hash_available"])
        self.assertNotIn("sha256", src)
        self.assertIn("PRIMARY_PUBLICATION_TEXT_RECOVERED_NE_BINARY_CUSTODY", self.obj["global_guards"])
        self.assertIn("BINARY_HASH_MUST_NOT_BE_INVENTED", self.obj["global_guards"])

    def test_task234_historical_placeholder_is_preserved_but_superseded(self):
        old = self.prior["sources"]["sme_operational_page"]["resolution_citation"]
        self.assertEqual(old["full_original_custody"], "NOT_ACQUIRED")
        self.assertTrue(self.obj["target"]["does_not_rewrite_historical_task234_file"])
        self.assertTrue(self.obj["summary"]["task234_resolution_placeholder_superseded_by_overlay"])
        self.assertEqual(
            self.obj["target"]["task235_status"],
            "PRIMARY_OFFICIAL_PUBLICATION_IDENTITY_AND_TEXT_RECOVERED_BINARY_NOT_CUSTODIED",
        )

    def test_primary_rule_precedence_is_explicit(self):
        p = self.obj["authority_precedence"]
        self.assertEqual(p[0], "PRIMARY_NORMATIVE_OFFICIAL_PUBLICATION_EXACT_ARTICLE_TEXT")
        self.assertLess(p.index("PRIMARY_NORMATIVE_OFFICIAL_PUBLICATION_EXACT_ARTICLE_TEXT"), p.index("OFFICIAL_OPERATIONAL_PAGE_CURRENT_WORKFLOW"))

    def test_article_23_and_30_are_primary_confirmations(self):
        a23 = self.articles[23]
        a30 = self.articles[30]
        self.assertEqual(a23["pages"], [181])
        self.assertIn("30", a23["topic"])
        self.assertIn("45", a23["topic"])
        self.assertEqual(a30["pages"], [183])
        self.assertIn("same contract", a30["topic"])
        confirms = " ".join(self.obj["task234_cross_check"]["primary_confirms"])
        self.assertIn("SMEOP-R06", confirms)
        self.assertIn("SMEOP-R07", confirms)
        self.assertIn("SMEOP-R02", confirms)

    def test_article_34_effective_date_is_preserved(self):
        src = self.obj["source"]
        self.assertTrue(src["effective_rule"]["effective_on_publication"])
        self.assertEqual(src["effective_rule"]["retroactive_effect_date"], "2025-12-06")
        self.assertEqual(self.articles[34]["pages"], [183])

    def test_lt_formation_timing_divergence_is_not_reconciled(self):
        d = self.obj["task234_cross_check"]["divergence"]
        self.assertEqual(d["id"], "LT_FORMATION_TIMING_DIVERGENCE")
        self.assertEqual(d["interpretation"], "UNRESOLVED_POSSIBLE_LATER_OPERATIONAL_OR_NORMATIVE_CHANGE")
        self.assertIn("upload", d["primary_publication"])
        self.assertIn("first semester", d["current_operational_page"])
        self.assertEqual(d["guard"], "DO_NOT_TREAT_OPERATIONAL_PAGE_AS_AMENDMENT_WITHOUT_OFFICIAL_MODIFIER_TRACE")
        self.assertTrue(self.obj["summary"]["lt_timing_divergence_open"])

    def test_operational_only_rules_are_not_silently_promoted(self):
        remaining = " ".join(self.obj["task234_cross_check"]["remains_operational_only_unless_separately_traced"])
        for rule_id in ("SMEOP-R03", "SMEOP-R04", "SMEOP-R05", "SMEOP-R08", "SMEOP-R09"):
            self.assertIn(rule_id, remaining)

    def test_selected_limits_are_exact(self):
        selected = self.obj["primary_selected_rules"]
        self.assertIn("48 h/a", selected["pss_48_hour_ceiling"]["rule"])
        self.assertIn("66 h/a", selected["cross_school_supplemental_ceiling"]["rule"])
        self.assertIn("Two-business-day", selected["appeals"]["rule"])

    def test_required_fail_closed_guards(self):
        required = {
            "PRIMARY_PUBLICATION_TEXT_RECOVERED_NE_BINARY_CUSTODY",
            "RETIFICACAO_LABEL_MUST_BE_PRESERVED",
            "ARTICLE_PAGE_PROVENANCE_REQUIRED",
            "NO_UNSEEN_TEXT_RECONSTRUCTION",
            "PRIMARY_EXACT_ARTICLE_GT_OPERATIONAL_PAGE_FOR_NORMATIVE_WORDING",
            "OPERATIONAL_PAGE_MAY_PROVE_CURRENT_WORKFLOW_WITHOUT_AMENDING_NORM",
            "DO_NOT_TREAT_OPERATIONAL_PAGE_AS_AMENDMENT_WITHOUT_OFFICIAL_MODIFIER_TRACE",
            "TASK234_HISTORICAL_PLACEHOLDER_MUST_NOT_BE_SILENTLY_REWRITTEN",
            "BINARY_HASH_MUST_NOT_BE_INVENTED",
            "NO_PERSONAL_LOGIN_DATA_MATERIALIZATION",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(set(self.obj["global_guards"])))

    def test_remote_effects_are_read_only_and_coverage_unchanged(self):
        effects = self.obj["remote_effects"]
        self.assertTrue(effects["source_network_read_only"])
        for key in ("drive_write", "serving", "publication", "schedule", "recurrence"):
            self.assertFalse(effects[key])
        self.assertEqual(self.obj["summary"]["contextual_coverage"], "38/38_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
