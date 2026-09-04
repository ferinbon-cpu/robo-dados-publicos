from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.research.ontology import (
    ResearchOntologyStop,
    legacy_financial_identity_to_status,
    load_ontology_contract,
    validate_research_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/research_ontology.v1.json"


def bundle_fixture():
    return {
        "schema": "RESEARCH_BUNDLE_V1",
        "entities": [
            {
                "id": "POLICY:EXAMPLE",
                "type": "POLICY",
                "label": "Example policy",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "DOC:PRIMARY_001",
                "type": "DOCUMENT",
                "label": "Primary source",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "PROGRAM:001",
                "type": "PROGRAM",
                "label": "Program 001",
                "aliases": [],
                "attributes": {},
            },
        ],
        "evidence": [
            {
                "evidence_id": "EVIDENCE:001",
                "source_entity_id": "DOC:PRIMARY_001",
                "locator": {"page": 10, "anchor": "program objective"},
                "content_sha256": "a" * 64,
                "note": "fixture",
            }
        ],
        "relations": [
            {
                "relation_id": "REL:001",
                "source_id": "PROGRAM:001",
                "target_id": "POLICY:EXAMPLE",
                "relation_type": "PLANS",
                "status": "PROVEN",
                "evidence_ids": ["EVIDENCE:001"],
                "attributes": {},
            }
        ],
        "claims": [
            {
                "claim_id": "CLAIM:001",
                "text": "The program explicitly plans the example policy.",
                "subject_ids": ["PROGRAM:001", "POLICY:EXAMPLE"],
                "status": "PROVEN",
                "evidence_ids": ["EVIDENCE:001"],
                "supporting_evidence_ids": ["EVIDENCE:001"],
                "contradicting_evidence_ids": [],
                "attributes": {},
            }
        ],
    }


class TestTask093ResearchOntology(unittest.TestCase):
    def test_contract_matches_runtime_schema_and_has_zero_remote_effects(self):
        contract = load_ontology_contract(CONTRACT)
        self.assertEqual("RESEARCH_ONTOLOGY_V1", contract["schema"])
        self.assertEqual(
            ["ENTITY", "RELATION", "CLAIM", "EVIDENCE"],
            contract["record_kinds"],
        )
        self.assertNotIn("CLAIM", contract["entity_types"])
        self.assertNotIn("EVIDENCE", contract["entity_types"])
        self.assertTrue(all(value is False for value in contract["remote_effects"].values()))

    def test_generic_non_eiti_policy_bundle_passes(self):
        bundle = validate_research_bundle(bundle_fixture())
        self.assertEqual("POLICY:EXAMPLE", bundle["entities"][0]["id"])
        self.assertEqual("PROVEN", bundle["claims"][0]["status"])
        self.assertEqual(["EVIDENCE:001"], bundle["relations"][0]["evidence_ids"])

    def test_proven_relation_without_evidence_fails(self):
        data = bundle_fixture()
        data["relations"][0]["evidence_ids"] = []
        with self.assertRaisesRegex(ResearchOntologyStop, "RELATION_EVIDENCE_REQUIRED"):
            validate_research_bundle(data)

    def test_proven_claim_cannot_keep_contradicting_evidence(self):
        data = bundle_fixture()
        data["claims"][0]["contradicting_evidence_ids"] = ["EVIDENCE:001"]
        with self.assertRaisesRegex(
            ResearchOntologyStop,
            "PROVEN_CANNOT_HAVE_CONTRADICTING_EVIDENCE",
        ):
            validate_research_bundle(data)

    def test_conflicted_claim_requires_support_and_contradiction(self):
        data = bundle_fixture()
        data["claims"][0]["status"] = "CONFLICTED"
        data["claims"][0]["supporting_evidence_ids"] = ["EVIDENCE:001"]
        data["claims"][0]["contradicting_evidence_ids"] = []
        with self.assertRaisesRegex(
            ResearchOntologyStop,
            "CONFLICTED_CONTRADICTION_REQUIRED",
        ):
            validate_research_bundle(data)

    def test_evidence_must_point_to_document_entity(self):
        data = bundle_fixture()
        data["evidence"][0]["source_entity_id"] = "DOC:PROGRAM_WRONG"
        data["entities"].append(
            {
                "id": "DOC:PROGRAM_WRONG",
                "type": "DOCUMENT",
                "label": "Temporary document",
                "aliases": [],
                "attributes": {},
            }
        )
        # First prove a DOC-typed source works.
        validate_research_bundle(data)
        data["evidence"][0]["source_entity_id"] = "PROGRAM:001"
        with self.assertRaisesRegex(ResearchOntologyStop, "EVIDENCE_SOURCE_ID"):
            validate_research_bundle(data)

    def test_relation_references_must_exist(self):
        data = bundle_fixture()
        data["relations"][0]["target_id"] = "POLICY:MISSING"
        with self.assertRaisesRegex(ResearchOntologyStop, "RELATION_TARGET_MISSING"):
            validate_research_bundle(data)

    def test_duplicate_entity_id_fails_closed(self):
        data = bundle_fixture()
        duplicate = copy.deepcopy(data["entities"][0])
        data["entities"].append(duplicate)
        with self.assertRaisesRegex(ResearchOntologyStop, "DUPLICATE_ENTITY_ID"):
            validate_research_bundle(data)

    def test_legacy_financial_identity_mapping_preserves_existing_semantics(self):
        self.assertEqual("PROVEN", legacy_financial_identity_to_status("A"))
        self.assertEqual("CORROBORATED", legacy_financial_identity_to_status("B"))
        self.assertEqual("CANDIDATE", legacy_financial_identity_to_status("C"))
        self.assertEqual("UNKNOWN", legacy_financial_identity_to_status("D"))
        with self.assertRaisesRegex(
            ResearchOntologyStop,
            "UNKNOWN_LEGACY_FINANCIAL_IDENTITY",
        ):
            legacy_financial_identity_to_status("Z")


if __name__ == "__main__":
    unittest.main()
