import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import F02GoldPreviewStop,build_preview,load_json,validate_config
ROOT=Path(__file__).resolve().parents[1]; CONFIG=ROOT/"config/manual_supervised_ingest_f02_gold_preview.v1.json"
class Tests(unittest.TestCase):
 def test_config(self): self.assertEqual(validate_config(load_json(CONFIG))["observation_count"],4)
 def test_exact_values_and_boundaries(self):
  c,r=build_preview(load_json(CONFIG),root=ROOT); self.assertEqual([x["value"] for x in c["observations"]],["24.27","23.60","88.67","96.99"]); self.assertFalse(r["gold_payload_persisted"]); self.assertEqual(r["drive_write_count"],0)
  by={x["observation_id"]:x for x in c["observations"]}; self.assertEqual(by["MDE_OFFICIAL_PARTIAL_2026_JAN_APR"]["period_end"],"2026-04-30"); self.assertEqual(by["MDE_LOCAL_MONITORING_2026_JAN_MAY"]["period_end"],"2026-05-31")
  for x in c["observations"]: self.assertFalse(x["annual_compliance_claim_authorized"]); self.assertFalse(x["imputation_performed"]); self.assertFalse(x["period_or_authority_collapsed"])
 def test_semantic_permissions_stop(self):
  base=load_json(CONFIG)
  for key in ("allow_imputation","allow_period_collapsing","allow_authority_collapsing","allow_annual_compliance_claim","allow_local_mde_as_official"):
   c=copy.deepcopy(base); c["semantic_policy"][key]=True
   with self.assertRaises(F02GoldPreviewStop): validate_config(c)
 def test_effect_permissions_stop(self):
  base=load_json(CONFIG)
  for key in ("source_network_authorized","drive_network_authorized","gold_persistence_authorized","serving_authorized","publication_authorized","site_mutation_authorized","delete_authorized","move_authorized","overwrite_authorized","recurrence_authorized","schedule_enabled"):
   c=copy.deepcopy(base); c["effects"][key]=True
   with self.assertRaises(F02GoldPreviewStop): validate_config(c)
 def test_tampered_silver_stops(self):
  c=load_json(CONFIG)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for s in c["silver_inputs"]:
    src=ROOT/s["local_snapshot_path"]; dst=root/s["local_snapshot_path"]; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
   target=root/c["silver_inputs"][0]["local_snapshot_path"]; target.write_text(target.read_text(encoding="utf-8")+" ",encoding="utf-8")
   with self.assertRaises(F02GoldPreviewStop): build_preview(c,root=root)
 def test_period_authority_family_drift_stops(self):
  base=load_json(CONFIG)
  for field,value in (("period_end","2026-05-31"),("authority","AUXILIARY_LOCAL_MONITORING"),("source_family","MDE_25_LOCAL")):
   c=copy.deepcopy(base); c["required_observations"][0][field]=value
   with self.assertRaises(F02GoldPreviewStop): build_preview(c,root=ROOT)
 def test_cli(self):
  cp=subprocess.run([sys.executable,"scripts/process_manual_supervised_ingest_f02_gold_preview.py"],cwd=ROOT,text=True,capture_output=True); self.assertEqual(cp.returncode,0,cp.stderr); x=json.loads(cp.stdout); self.assertEqual(x["effects"]["gold_writes"],0); self.assertEqual(x["effects"]["drive_writes"],0)
if __name__=="__main__": unittest.main()
