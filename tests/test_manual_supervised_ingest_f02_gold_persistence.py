from __future__ import annotations
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_persistence import (
    F02GoldPersistenceStop, build_and_verify_candidate, validate_persistence_contract,
    validate_preview_review_evidence,
)
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import load_json

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config/manual_supervised_ingest_f02_gold_persistence.v1.json"
EVIDENCE=ROOT/"docs/evidence/F02_GOLD_DEEPSEEK_ADVERSARIAL_REVIEW_0.8.0.json"

class F02GoldPersistenceTests(unittest.TestCase):
    def test_exact_contract_and_candidate_preflight(self):
        config=load_json(CONFIG)
        self.assertEqual(validate_persistence_contract(config)["status"],"PASS_F02_GOLD_PERSISTENCE_CONTRACT")
        rendered,result=build_and_verify_candidate(config,root=ROOT)
        self.assertEqual(len(rendered),4231)
        self.assertEqual(result["logical_sha256"],"38232ab8e02a3afc5444d3ef8f6276f056f29a001d62b2b2dc1d571a0a79e90d")
        self.assertEqual(result["rendered_sha256"],"e2ef3f4eef403730f54c8f8ddfd5dcbf3facd5131a6cedd0cb356ffce7354fe1")
        self.assertFalse(result["gold_remote_write_performed"])

    def test_exact_target_ids_names_create_only_and_budget(self):
        base=load_json(CONFIG)
        mutations=(
            ("gold_target","folder_drive_id","WRONG"),
            ("gold_target","file_name","wrong.json"),
            ("manifest_target","folder_drive_id","WRONG"),
            ("manifest_target","file_name","wrong.json"),
            ("gold_target","create_only",False),
            ("gold_target","overwrite",True),
            ("gold_target","max_creates",2),
            ("manifest_target","readback_required",False),
        )
        for target,field,value in mutations:
            c=copy.deepcopy(base); c[target][field]=value
            with self.assertRaises(F02GoldPersistenceStop,msg=f"{target}.{field}"):
                validate_persistence_contract(c)

    def test_every_forbidden_effect_must_remain_forbidden(self):
        base=load_json(CONFIG)
        for key in base["forbidden"]:
            c=copy.deepcopy(base); c["forbidden"][key]=False
            with self.assertRaises(F02GoldPersistenceStop): validate_persistence_contract(c)

    def test_preview_review_evidence_identity_and_non_authorization_are_pinned(self):
        config=load_json(CONFIG); evidence=load_json(EVIDENCE); pre=config["prerequisite"]
        self.assertEqual(validate_preview_review_evidence(evidence,pre)["blocking_findings"],0)
        mutations=(
            ("schema","WRONG"),
            ("reviewed_target.pr",373),
            ("reviewed_target.head_sha","0"*40),
            ("deepseek.review_sha256","0"*64),
            ("adjudication.gold_persistence_authorized_by_this_evidence",True),
        )
        for key,value in mutations:
            e=copy.deepcopy(evidence)
            parts=key.split("."); cur=e
            for p in parts[:-1]: cur=cur[p]
            cur[parts[-1]]=value
            with self.assertRaises(F02GoldPersistenceStop,msg=key):
                validate_preview_review_evidence(e,pre)

    def test_missing_review_evidence_stops_with_stable_error(self):
        c=load_json(CONFIG); c["prerequisite"]["preview_review_evidence_path"]="docs/evidence/DOES_NOT_EXIST.json"
        with self.assertRaisesRegex(F02GoldPersistenceStop,"REVIEW_EVIDENCE_UNREADABLE"):
            build_and_verify_candidate(c,root=ROOT)

    def test_candidate_hash_and_gate_drift_stops(self):
        base=load_json(CONFIG)
        c=copy.deepcopy(base); c["candidate"]["logical_sha256"]="0"*64
        with self.assertRaises(F02GoldPersistenceStop): build_and_verify_candidate(c,root=ROOT)
        for field,value in (("contract_materialization_gate",8),("remote_persistence_gate",9)):
            c=copy.deepcopy(base); c["owner_authorization"][field]=value
            with self.assertRaises(F02GoldPersistenceStop): validate_persistence_contract(c)

    def test_cli_nonzero_on_config_drift(self):
        config=load_json(CONFIG); config["gold_target"]["folder_drive_id"]="WRONG"
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"bad.json"; path.write_text(json.dumps(config),encoding="utf-8")
            cp=subprocess.run([sys.executable,"scripts/process_manual_supervised_ingest_f02_gold_persistence_preflight.py","--config",str(path)],cwd=ROOT,text=True,capture_output=True,check=False)
            self.assertNotEqual(cp.returncode,0)
            self.assertIn("STOP_F02_GOLD_PERSISTENCE_TARGET_ID",cp.stderr)

if __name__=="__main__": unittest.main()
