from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.ppa_2018_ontology_search import (
    Task113Stop,
    load_and_validate_task113_contract,
    validate_task113_contract,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"config/task113_ppa2018_ontology_lexical.v1.json"

class TestTask113OntologyLexicalContract(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_contract_passes_offline(self):
        result=load_and_validate_task113_contract(CONTRACT)
        self.assertEqual("PASS_TASK113_ONTOLOGY_LEXICAL_CONTRACT",result["status"])
        self.assertEqual(3,result["family_count"])
        self.assertEqual(29,result["term_count"])
        self.assertFalse(result["live_authorized"])
        self.assertEqual(0,result["remote_effects"])

    def test_source_sha_drift_fails_closed(self):
        data=copy.deepcopy(self.data)
        data["source_identity"]["sha256"]="0"*64
        with self.assertRaisesRegex(Task113Stop,"SOURCE_SHA"):
            validate_task113_contract(data)

    def test_financing_or_accounting_family_cannot_enter_search(self):
        for family in ("D_FINANCING_AND_INDUCTION_SIGNALS","E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS"):
            data=copy.deepcopy(self.data)
            data["families"][family]=[{"term":"FUNDEB","strength":"STRONG","requires_companion":False}]
            with self.assertRaisesRegex(Task113Stop,"FAMILY_SET"):
                validate_task113_contract(data)

    def test_weak_terms_require_companion(self):
        for entries in self.data["families"].values():
            for entry in entries:
                if entry["strength"] in {"WEAK","WEAK_SHORT_FORM","WEAK_NUMERIC"}:
                    self.assertTrue(entry["requires_companion"],entry)

    def test_fuzzy_or_automatic_promotion_cannot_be_enabled(self):
        data=copy.deepcopy(self.data)
        data["fuzzy_edit_distance"]=True
        with self.assertRaisesRegex(Task113Stop,"NO_FUZZY"):
            validate_task113_contract(data)
        data=copy.deepcopy(self.data)
        data["promotion"]["automatic_primary_planning_proof"]=True
        with self.assertRaisesRegex(Task113Stop,"PROMOTION"):
            validate_task113_contract(data)

    def test_live_gate_stays_unauthed(self):
        data=copy.deepcopy(self.data)
        data["future_live_gate"]["authorized_now"]=True
        with self.assertRaisesRegex(Task113Stop,"LIVE_NOT_AUTHORIZED"):
            validate_task113_contract(data)

if __name__=="__main__":
    unittest.main()
