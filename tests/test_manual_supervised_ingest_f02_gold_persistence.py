from __future__ import annotations
import copy, unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_persistence import (
    F02GoldPersistenceStop, build_and_verify_candidate, validate_persistence_contract,
)
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import load_json

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config/manual_supervised_ingest_f02_gold_persistence.v1.json"

class F02GoldPersistenceTests(unittest.TestCase):
    def test_exact_contract_and_candidate_preflight(self):
        config=load_json(CONFIG)
        self.assertEqual(validate_persistence_contract(config)["status"],"PASS_F02_GOLD_PERSISTENCE_CONTRACT")
        rendered,result=build_and_verify_candidate(config,root=ROOT)
        self.assertEqual(len(rendered),4231)
        self.assertEqual(result["logical_sha256"],"38232ab8e02a3afc5444d3ef8f6276f056f29a001d62b2b2dc1d571a0a79e90d")
        self.assertEqual(result["rendered_sha256"],"e2ef3f4eef403730f54c8f8ddfd5dcbf3facd5131a6cedd0cb356ffce7354fe1")
        self.assertFalse(result["gold_remote_write_performed"])
    def test_write_targets_are_create_only_and_bounded(self):
        base=load_json(CONFIG)
        for target in ("gold_target","manifest_target"):
            for field,value in (("create_only",False),("overwrite",True),("max_creates",2),("readback_required",False)):
                c=copy.deepcopy(base); c[target][field]=value
                with self.assertRaises(F02GoldPersistenceStop): validate_persistence_contract(c)
    def test_every_forbidden_effect_must_remain_forbidden(self):
        base=load_json(CONFIG)
        for key in base["forbidden"]:
            c=copy.deepcopy(base); c["forbidden"][key]=False
            with self.assertRaises(F02GoldPersistenceStop): validate_persistence_contract(c)
    def test_deepseek_blocker_or_candidate_hash_drift_stops(self):
        base=load_json(CONFIG)
        c=copy.deepcopy(base); c["prerequisite"]["required_deepseek_blocking_findings"]=1
        with self.assertRaises(F02GoldPersistenceStop): build_and_verify_candidate(c,root=ROOT)
        c=copy.deepcopy(base); c["candidate"]["logical_sha256"]="0"*64
        with self.assertRaises(F02GoldPersistenceStop): build_and_verify_candidate(c,root=ROOT)
    def test_gate_sequence_is_pinned(self):
        base=load_json(CONFIG)
        for field,value in (("contract_materialization_gate",8),("remote_persistence_gate",9)):
            c=copy.deepcopy(base); c["owner_authorization"][field]=value
            with self.assertRaises(F02GoldPersistenceStop): validate_persistence_contract(c)

if __name__=="__main__": unittest.main()
