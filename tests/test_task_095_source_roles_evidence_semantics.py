from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from robo_dados_publicos.research.evidence_semantics import (
    EvidenceSemanticsStop,
    allowed_evidence_status,
    can_evidence_support_status,
    load_source_role_contract,
    source_role_max_status,
    validate_negative_evidence,
    validate_semantic_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/source_role_evidence_semantics.v1.json"


def evidence(
    *,
    role="BUDGET_PRIMARY",
    domain="BUDGET_AUTHORIZATION",
    kind="DIRECT_EXPLICIT",
    status="PROVEN",
):
    return {
        "evidence_id": "EVIDENCE:001",
        "source_document_id": "DOC:001",
        "source_role": role,
        "claim_domain": domain,
        "evidence_kind": kind,
        "locator": {"page": 1},
        "requested_status": status,
        "input_evidence_ids": [],
        "reproducible": False,
        "negative_search_id": None,
        "note": "fixture",
    }


class TestTask095SourceRolesEvidenceSemantics(unittest.TestCase):
    def test_contract_is_remote_effect_free(self):
        contract = load_source_role_contract(CONTRACT)
        self.assertEqual("SOURCE_ROLE_EVIDENCE_SEMANTICS_V1", contract["schema"])
        self.assertTrue(all(value is False for value in contract["remote_effects"].values()))

    def test_budget_primary_can_directly_prove_authorization_not_execution(self):
        self.assertEqual(
            "PROVEN",
            source_role_max_status("BUDGET_PRIMARY", "BUDGET_AUTHORIZATION"),
        )
        self.assertEqual(
            "CANDIDATE",
            source_role_max_status("BUDGET_PRIMARY", "ACCOUNTING_EXECUTION"),
        )

    def test_doctrine_cannot_prove_local_accounting_execution(self):
        record = evidence(
            role="DOCTRINAL_SOURCE",
            domain="ACCOUNTING_EXECUTION",
            status="PROVEN",
        )
        with self.assertRaisesRegex(
            EvidenceSemanticsStop,
            "STATUS_EXCEEDS_SOURCE_OR_KIND_CAPABILITY",
        ):
            validate_semantic_evidence(record)

    def test_normative_primary_proves_norm_not_implementation(self):
        self.assertEqual(
            "PROVEN",
            allowed_evidence_status(
                "NORMATIVE_PRIMARY",
                "LEGAL_NORM",
                "DIRECT_EXPLICIT",
            ),
        )
        self.assertEqual(
            "CANDIDATE",
            allowed_evidence_status(
                "NORMATIVE_PRIMARY",
                "ACCOUNTING_EXECUTION",
                "DIRECT_EXPLICIT",
            ),
        )

    def test_statistical_primary_does_not_prove_causal_effect(self):
        self.assertEqual(
            "CANDIDATE",
            allowed_evidence_status(
                "STATISTICAL_PRIMARY",
                "CAUSAL_EFFECT",
                "DIRECT_EXPLICIT",
            ),
        )

    def test_analytical_inference_never_auto_proven(self):
        record = evidence(
            role="ACCOUNTING_EXECUTION_PRIMARY",
            domain="ACCOUNTING_EXECUTION",
            kind="ANALYTICAL_INFERENCE",
            status="PROVEN",
        )
        with self.assertRaisesRegex(
            EvidenceSemanticsStop,
            "STATUS_EXCEEDS_SOURCE_OR_KIND_CAPABILITY",
        ):
            validate_semantic_evidence(record)

    def test_deterministic_derivation_requires_inputs_and_reproducibility(self):
        record = evidence(
            role="ACCOUNTING_EXECUTION_PRIMARY",
            domain="ACCOUNTING_EXECUTION",
            kind="DETERMINISTIC_DERIVATION",
            status="PROVEN",
        )
        with self.assertRaisesRegex(EvidenceSemanticsStop, "DERIVATION_INPUT_REQUIRED"):
            validate_semantic_evidence(record)
        record["input_evidence_ids"] = ["EVIDENCE:BASE"]
        with self.assertRaisesRegex(
            EvidenceSemanticsStop,
            "DERIVATION_REPRODUCIBILITY_REQUIRED",
        ):
            validate_semantic_evidence(record)
        record["reproducible"] = True
        validated = validate_semantic_evidence(record)
        self.assertEqual("PROVEN", validated["maximum_allowed_status"])

    def test_negative_search_observation_can_only_prove_search_result(self):
        record = evidence(
            role="ADMINISTRATIVE_PRIMARY",
            domain="ACCOUNTING_EXECUTION",
            kind="NEGATIVE_SEARCH_OBSERVATION",
            status="CANDIDATE",
        )
        record["negative_search_id"] = "SEARCH:001"
        with self.assertRaisesRegex(EvidenceSemanticsStop, "NEGATIVE_OBSERVATION_DOMAIN"):
            validate_semantic_evidence(record)

        record["claim_domain"] = "SEARCH_RESULT"
        record["requested_status"] = "PROVEN"
        validated = validate_semantic_evidence(record)
        self.assertEqual("PROVEN", validated["maximum_allowed_status"])

    def test_no_match_is_scoped_absence_not_nonexistence(self):
        negative = validate_negative_evidence(
            {
                "search_id": "SEARCH:001",
                "target": "explicit EITI action",
                "scope": {"document": "PPA", "pages": [15, 16]},
                "method": {"terms": ["EITI", "tempo integral"]},
                "coverage": {"rows_checked": 27},
                "result": "NO_MATCH",
                "exhaustive": True,
            }
        )
        self.assertEqual(
            "ABSENCE_OBSERVED_WITHIN_DECLARED_SEARCH_SCOPE_ONLY",
            negative["interpretation"],
        )
        self.assertFalse(negative["proves_nonexistence"])

    def test_secondary_aggregator_never_directly_proves_accounting_execution(self):
        self.assertEqual(
            "CORROBORATED",
            source_role_max_status(
                "SECONDARY_AGGREGATOR",
                "ACCOUNTING_EXECUTION",
            ),
        )
        self.assertFalse(
            can_evidence_support_status(
                evidence(
                    role="SECONDARY_AGGREGATOR",
                    domain="ACCOUNTING_EXECUTION",
                    status="CORROBORATED",
                ),
                "PROVEN",
            )
        )

    def test_contract_fails_if_negative_evidence_is_promoted_to_nonexistence(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        data["negative_evidence"]["proves_nonexistence"] = True
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "contract.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(
                EvidenceSemanticsStop,
                "NEGATIVE_OVERREACH",
            ):
                load_source_role_contract(path)


if __name__ == "__main__":
    unittest.main()
