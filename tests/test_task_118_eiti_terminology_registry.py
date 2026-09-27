from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.eiti_terminology_registry import (
    EitiTerminologyRegistryStop,
    load_terminology_registry,
    validate_terminology_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "eiti_research_terminology.v2.json"


class TestTask118EitiTerminologyRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_terminology_registry(REGISTRY_PATH, root=ROOT)

    def test_base_63_is_preserved_and_active_vocabulary_is_64(self):
        result = validate_terminology_registry(deepcopy(self.registry), root=ROOT)
        self.assertEqual("PASS_TASK118_TERMINOLOGY_REGISTRY_V2", result["status"])
        self.assertEqual(63, result["base_term_count"])
        self.assertEqual(1, result["discovered_alias_count"])
        self.assertEqual(64, result["active_distinct_term_count"])

    def test_fomento_eti_is_provenanced_composite_alias(self):
        alias = self.registry["discovered_aliases"][0]
        self.assertEqual("FOMENTO ETI", alias["term"])
        self.assertEqual("STRONG_POLICY_FINANCE_REPORTING_ALIAS", alias["classification"])
        self.assertEqual(
            {"POLICY_SIGNAL", "FINANCING_SIGNAL", "REPORTING_BUCKET_ALIAS"},
            set(alias["semantic_roles"]),
        )
        self.assertEqual("FINANCIAL_REPORTING_ONLY", alias["policy_signal_scope"])

    def test_composite_alias_does_not_prove_transaction_identity(self):
        alias = self.registry["discovered_aliases"][0]
        self.assertFalse(alias["transaction_identity"])
        self.assertFalse(alias["generic_policy_financial_identity"])
        self.assertFalse(alias["amount_alone_sufficient"])
        self.assertTrue(alias["stable_accounting_key_still_required_for_transaction_bridge"])

    def test_alias_source_blob_drift_fails_closed(self):
        data = deepcopy(self.registry)
        data["discovered_aliases"][0]["provenance"]["git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(EitiTerminologyRegistryStop, "ALIAS_SOURCE_BLOB"):
            validate_terminology_registry(data, root=ROOT)

    def test_alias_cannot_be_silently_reclassified(self):
        data = deepcopy(self.registry)
        data["discovered_aliases"][0]["classification"] = "GENERIC_ALIAS"
        with self.assertRaisesRegex(EitiTerminologyRegistryStop, "ALIAS_CLASS"):
            validate_terminology_registry(data, root=ROOT)

    def test_transaction_identity_cannot_be_enabled(self):
        data = deepcopy(self.registry)
        data["discovered_aliases"][0]["transaction_identity"] = True
        with self.assertRaisesRegex(EitiTerminologyRegistryStop, "TRANSACTION_IDENTITY"):
            validate_terminology_registry(data, root=ROOT)

    def test_remote_effects_cannot_be_enabled(self):
        data = deepcopy(self.registry)
        data["remote_effects"]["drive_write"] = True
        with self.assertRaisesRegex(EitiTerminologyRegistryStop, "REMOTE_EFFECT"):
            validate_terminology_registry(data, root=ROOT)


if __name__ == "__main__":
    unittest.main()
