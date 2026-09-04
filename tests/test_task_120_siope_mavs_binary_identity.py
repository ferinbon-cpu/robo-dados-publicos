from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.siope_mavs_binary_identity import (
    Task120Stop, load_task120_contract, validate_task120_contract
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"config/task120_siope_mavs_binary_identity.v1.json"

class TestTask120BinaryIdentityPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_task120_contract(CONTRACT)

    def test_exact_source_and_budgets(self):
        self.assertEqual("17Fl8opb1pkqdFa485-bkQR3j6LnApnE-",self.data["source"]["drive_file_id"])
        self.assertEqual(1,self.data["request_budget"]["drive_metadata_reads_max"])
        self.assertEqual(1,self.data["request_budget"]["drive_media_reads_max"])
        self.assertEqual(0,self.data["request_budget"]["drive_writes"])

    def test_source_drift_fails_closed(self):
        data=deepcopy(self.data); data["source"]["drive_file_id"]="other"
        with self.assertRaisesRegex(Task120Stop,"FILE_ID"): validate_task120_contract(data)

    def test_search_or_write_enablement_fails_closed(self):
        for key in ("drive_searches","drive_lists","drive_writes"):
            data=deepcopy(self.data); data["request_budget"][key]=1
            with self.assertRaises(Task120Stop): validate_task120_contract(data)

    def test_content_analysis_cannot_be_enabled(self):
        for key in ("text_extraction","ocr","ontology_scan","semantic_reinterpretation","persistent_raw_copy"):
            data=deepcopy(self.data); data["processing"][key]=True
            with self.assertRaises(Task120Stop): validate_task120_contract(data)

    def test_financial_or_transaction_promotion_cannot_be_enabled(self):
        for key in ("financial_identity","transaction_identity","implementation","causal_effect"):
            data=deepcopy(self.data); data["promotion"][key]=True
            with self.assertRaises(Task120Stop): validate_task120_contract(data)

    def test_retry_or_future_cannot_be_enabled(self):
        data=deepcopy(self.data); data["request_budget"]["retry"]=True
        with self.assertRaisesRegex(Task120Stop,"RETRY"): validate_task120_contract(data)
        data=deepcopy(self.data); data["future_execution_authorized"]=True
        with self.assertRaisesRegex(Task120Stop,"FUTURE"): validate_task120_contract(data)

if __name__=="__main__": unittest.main()
