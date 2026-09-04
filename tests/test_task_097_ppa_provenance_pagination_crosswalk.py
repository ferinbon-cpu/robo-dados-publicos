from __future__ import annotations

from pathlib import Path
import unittest

from robo_dados_publicos.research.provenance_locator import (
    ProvenanceLocatorStop,
    compare_page_locators,
    load_locator_contract,
    normalize_task097_ppa_locator_case,
    validate_locator,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/research_locator_provenance.v1.json"

LEGACY = {
    "page": 18,
    "coordinate_system": "LEGACY_UNTYPED_PAGE",
    "source_key": "ppa_7213_2025",
    "source_sha256": None,
}

PRIMARY = {
    "page": 15,
    "coordinate_system": "JOURNAL_EDITION_PDF_PAGE",
    "source_key": "SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf",
    "source_sha256": "cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a",
    "page_text_sha256": "b6d44ee39efeed3b1acc3dccabbf56c73fb6914ef8ce15003d144c44a59e5eb4",
}


class TestTask097PpaProvenancePaginationCrosswalk(unittest.TestCase):
    def test_canonical_task097_case_stays_unresolved(self):
        contract = load_locator_contract(CONTRACT)
        result = normalize_task097_ppa_locator_case(contract)
        self.assertEqual(
            "PASS_TASK097_PPA_LOCATOR_PROVENANCE_NORMALIZED_NO_EQUIVALENCE_CLAIM",
            result["status"],
        )
        self.assertEqual(18, result["legacy_page"])
        self.assertEqual(15, result["primary_journal_page"])
        self.assertEqual(
            "UNRESOLVED_LEGACY_COORDINATE_SYSTEM",
            result["equivalence_status"],
        )

    def test_raw_18_and_15_are_not_equated(self):
        comparison = compare_page_locators(LEGACY, PRIMARY)
        self.assertIsNone(comparison["equivalent_page"])
        self.assertEqual(
            "UNRESOLVED_LEGACY_COORDINATE_SYSTEM",
            comparison["status"],
        )

    def test_arithmetic_difference_alone_cannot_resolve_legacy_locator(self):
        with self.assertRaisesRegex(
            ProvenanceLocatorStop,
            "OFFSET_CANNOT_RESOLVE_UNTYPED_LEGACY_PAGE",
        ):
            compare_page_locators(
                LEGACY,
                PRIMARY,
                proven_offset={
                    "right_minus_left": -3,
                    "basis": "mere arithmetic difference",
                    "basis_sha256": "a" * 64,
                },
            )

    def test_same_source_and_coordinate_system_can_compare_directly(self):
        left = dict(PRIMARY)
        right = dict(PRIMARY)
        comparison = compare_page_locators(left, right)
        self.assertEqual("PROVEN_SAME_COORDINATE_SYSTEM", comparison["status"])
        self.assertTrue(comparison["equivalent_page"])

    def test_same_page_number_different_sources_is_not_direct_equivalence(self):
        left = dict(PRIMARY)
        right = dict(PRIMARY)
        right["source_key"] = "another.pdf"
        right["source_sha256"] = "d" * 64
        comparison = compare_page_locators(left, right)
        self.assertEqual(
            "UNRESOLVED_CROSS_COORDINATE_SYSTEM",
            comparison["status"],
        )
        self.assertIsNone(comparison["equivalent_page"])

    def test_page_hash_requires_stable_source_hash(self):
        bad = dict(PRIMARY)
        bad["source_sha256"] = None
        with self.assertRaisesRegex(
            ProvenanceLocatorStop,
            "PAGE_HASH_WITHOUT_SOURCE_HASH",
        ):
            validate_locator(bad)

    def test_legacy_untyped_locator_cannot_gain_invented_source_hash(self):
        bad = dict(LEGACY)
        bad["source_sha256"] = "e" * 64
        with self.assertRaisesRegex(
            ProvenanceLocatorStop,
            "LEGACY_UNTYPED_MUST_NOT_GAIN_INVENTED_SOURCE_HASH",
        ):
            validate_locator(bad)

    def test_explicit_offset_requires_typed_coordinate_systems_and_basis_hash(self):
        left = {
            "page": 10,
            "coordinate_system": "STANDALONE_PDF_PAGE",
            "source_key": "standalone.pdf",
            "source_sha256": "1" * 64,
        }
        right = {
            "page": 13,
            "coordinate_system": "JOURNAL_EDITION_PDF_PAGE",
            "source_key": "journal.pdf",
            "source_sha256": "2" * 64,
        }
        comparison = compare_page_locators(
            left,
            right,
            proven_offset={
                "right_minus_left": 3,
                "basis": "explicit page-by-page mapping artifact",
                "basis_sha256": "3" * 64,
            },
        )
        self.assertEqual("PROVEN_EXPLICIT_OFFSET", comparison["status"])
        self.assertTrue(comparison["equivalent_page"])


if __name__ == "__main__":
    unittest.main()
