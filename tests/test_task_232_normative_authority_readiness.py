import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "config" / "normative_sme_legal_authority_readiness.v1.json"
COVERAGE = ROOT / "config" / "normative_sme_legal_coverage.v1.json"


class TestTask232NormativeAuthorityReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(READINESS.read_text(encoding="utf-8"))
        cls.coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
        cls.items = {x["id"]: x for x in cls.obj["items"]}
        cls.packages = {x["source_package_id"]: x for x in cls.obj["source_packages"]}

    def test_exact_integrated_set_from_task222(self):
        integrated = {
            x["id"] for x in self.coverage["items"]
            if x["status"] == "INTEGRADO_CORPUS"
        }
        self.assertEqual(len(integrated), 11)
        self.assertEqual(set(self.items), integrated)
        self.assertEqual(self.obj["scope"]["integrated_menu_items"], 11)

    def test_eight_logical_source_packages(self):
        self.assertEqual(len(self.packages), 8)
        self.assertEqual(self.obj["scope"]["logical_source_packages"], 8)
        self.assertEqual(self.obj["summary"]["distinct_logical_source_packages"], 8)

    def test_menu_overlap_is_not_double_counted(self):
        self.assertEqual(
            self.items["SMELEGAL-014"]["source_package_id"],
            self.items["SMELEGAL-028"]["source_package_id"],
        )
        self.assertEqual(
            self.items["SMELEGAL-045"]["source_package_id"],
            self.items["SMELEGAL-061"]["source_package_id"],
        )
        self.assertEqual(
            self.items["SMELEGAL-056"]["source_package_id"],
            self.items["SMELEGAL-065"]["source_package_id"],
        )
        self.assertEqual(
            self.items["SMELEGAL-028"]["source_identity_status"],
            "DERIVED_SUBSET_OF_PACKAGE",
        )
        self.assertEqual(
            self.items["SMELEGAL-065"]["source_identity_status"],
            "DERIVED_SUBSET_OF_PACKAGE",
        )

    def test_only_primary_normative_text_is_usable_as_source_text(self):
        usable = {
            x["id"] for x in self.obj["items"]
            if x["decision_use"] == "SOURCE_TEXT_USABLE_WITH_VIGENCY_GUARD"
        }
        self.assertEqual(usable, {"SMELEGAL-011", "SMELEGAL-012", "SMELEGAL-054"})
        for item_id in usable:
            self.assertEqual(self.items[item_id]["source_role"], "PRIMARY_NORMATIVE_TEXT")
        self.assertEqual(self.obj["summary"]["primary_normative_menu_items"], 3)
        self.assertEqual(self.obj["summary"]["context_only_menu_items"], 8)

    def test_training_guidance_and_templates_are_context_only(self):
        forbidden_roles = {
            "TRAINING_MATERIAL",
            "OPERATIONAL_GUIDANCE",
            "ONBOARDING_RECORD_TEMPLATE",
            "ADMINISTRATIVE_INSTRUCTION",
        }
        for item in self.obj["items"]:
            if item["source_role"] in forbidden_roles:
                self.assertEqual(
                    item["decision_use"],
                    "CONTEXT_ONLY_NOT_STANDALONE_LEGAL_AUTHORITY",
                )

    def test_no_current_vigency_is_inferred(self):
        self.assertEqual(self.obj["summary"]["current_vigency_proven_items"], 0)
        for item in self.obj["items"]:
            self.assertEqual(item["vigency_status"], "NOT_REVALIDATED_CURRENTLY")
        for package in self.obj["source_packages"]:
            self.assertEqual(package["vigency_status"], "NOT_REVALIDATED_CURRENTLY")

    def test_known_extraction_evidence(self):
        self.assertEqual(self.packages["PKG-LC41-1991"]["pages"], 25)
        self.assertEqual(self.packages["PKG-LC41-1991"]["extraction_status"], "PDF_TEXT_OK")
        self.assertEqual(self.packages["PKG-LC461-2009"]["pages"], 32)
        self.assertEqual(self.packages["PKG-LC461-2009"]["extraction_status"], "PDF_TEXT_OK")
        self.assertEqual(self.packages["PKG-LEI6089-2018"]["pages"], 26)
        self.assertEqual(self.packages["PKG-LEI6089-2018"]["extraction_status"], "OCR_OK_SOURCE_SCAN")
        self.assertEqual(self.packages["PKG-CONSELHO-CICLO-2022"]["pages"], 61)
        self.assertEqual(self.packages["PKG-CONSELHO-CICLO-2022"]["source_role"], "TRAINING_MATERIAL")

    def test_ocr_does_not_become_official_publication(self):
        self.assertIn("OCR_NE_OFFICIAL_PUBLICATION", self.obj["guards"])
        lei = self.packages["PKG-LEI6089-2018"]
        self.assertIn("official publication", lei["authority_note"])

    def test_next_official_targets_are_bounded(self):
        self.assertEqual(
            self.obj["summary"]["next_official_vigency_targets"],
            [
                "PKG-LC41-1991",
                "PKG-LC461-2009",
                "PKG-LEI6089-2018",
                "PKG-VICE-DIRETOR",
            ],
        )

    def test_required_fail_closed_guards(self):
        required = {
            "INTEGRADO_CORPUS_NE_CURRENT_VIGENCY_PROOF",
            "TRAINING_MATERIAL_NE_NORMATIVE_ACT",
            "OPERATIONAL_GUIDANCE_NE_LAW",
            "ADMINISTRATIVE_TEMPLATE_NE_GENERAL_NORM",
            "OCR_NE_OFFICIAL_PUBLICATION",
            "MENU_ITEM_NE_DISTINCT_SOURCE_PACKAGE",
            "DUPLICATE_MENU_ENTRY_NE_NEW_AUTHORITY",
            "EMBEDDED_AMENDMENT_REFERENCES_NE_COMPLETE_CURRENT_CONSOLIDATION",
            "SOURCE_TEXT_PRESENT_NE_NO_LATER_AMENDMENT",
            "NO_GENERIC_OTHER_NETWORK_RULE_INVENTION",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(set(self.obj["guards"])))

    def test_no_remote_effects_and_no_coverage_change(self):
        self.assertEqual(self.obj["scope"]["contextual_coverage"], "38/38_UNCHANGED")
        self.assertTrue(all(value is False for value in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
