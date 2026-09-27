import copy,json,unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.drive_ingestion_controller import load_controller_contract
from robo_dados_publicos.manual_ingest.source_family_maturity import load_maturity_registry
from robo_dados_publicos.manual_ingest.ingestion_execution_policy import load_execution_policy
from robo_dados_publicos.manual_ingest.folder_authorization import load_authorization,authorize_record
from robo_dados_publicos.manual_ingest.auto_ingest_dry_run import plan_record,summarize_plan

ROOT=Path(__file__).resolve().parents[1]
C=load_controller_contract(ROOT/'config/drive_ingestion_controller.v3.json')
M=load_maturity_registry(ROOT/'config/source_family_maturity_registry.v1.json')
P=load_execution_policy(ROOT/'config/ingestion_execution_policy.v1.json')
A=load_authorization(ROOT/'config/authorizations/10_inbox_jornal_oficial_auto_ingest.v1.json')
ROOT_ID='16lvKYsbW96JLoLbRGuTUohjyzndrR9r8'; PEND='1ofFcveMY7kzYsYujo5hfSM-iv6pzzcMY'; F01='1CdL4T1CVIPqNph3f5xHbiU8KgxgPpkl5'

def rec(id,title): return {'id':id,'title':title,'mime_type':'application/pdf','in_authorized_scope':True,'content_hydrated':False,'parent_ids':[F01],'ancestor_folder_ids':[PEND,ROOT_ID],'unresolved_duplicate_signal':False}
REAL=[
rec('1bRpmMxacX16P1tJBvam-55OOPTYuQnIA','SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf'),
rec('1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj','SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf'),
rec('1U_E1I1Lbrq5WvedrDPygFuEfQj-ouOex','SOURCE_JOM_7024_2025-07-08_LDO_7141_2025.pdf'),
rec('1TNaam6RfJoucnwrV7iaJZH5eBdrLMjcjBJZnX784I-4','MANIFEST_F01_PPA_LDO_LOA_2026_V03'),
rec('1zoG37Ao-h5GSzxkwlvwki8LDHzuD_DmT','SOURCE_LOA_2026_LEI_7223_2025_LIMEIRA.pdf'),
rec('1EyoQ69aaPx7u4_w7xkSg7-oWCx_vkJlX','SOURCE_LDO_2026_LEI_7141_2025_LIMEIRA.pdf'),
rec('1_rTVwimxhSXPJ-iMslSOwLWMq3r61-7vkEhXc_pgFNg','MANIFEST_F01_PPA_LDO_LOA_2026_V02'),
rec('1btfxebkUxkjjVIrdsTT_W6WOSSbGCEbq','SOURCE_PPA_2026_2029_LEI_7213_2025_LIMEIRA.pdf'),
rec('1Um3vUSJ579HMrKnrDYarjolexNzmVQknjboQMzulDR4','MANIFEST_F01_PPA_LDO_LOA_2026_V01')]

class Task070Tests(unittest.TestCase):
 def test_real_inbox_plan_is_three_eligible_six_review(self):
  plans=[plan_record(x,C,M,P,A) for x in REAL]; s=summarize_plan(plans)
  self.assertEqual(s,{'ELIGIBLE':3,'REVIEW':6,'QUARANTINE':0,'BLOCKED_MATURITY':0,'BLOCKED_POLICY':0})
  self.assertTrue(all(x['family']=='JORNAL_OFICIAL' for x in plans[:3]))
 def test_outside_root_is_blocked(self):
  x=rec('x','SOURCE_JOM_8000_2026-09-02_PPA_9999_2026.pdf'); x['ancestor_folder_ids']=['elsewhere']; x['parent_ids']=['elsewhere']
  p=plan_record(x,C,M,P,A); self.assertEqual(p['plan_state'],'BLOCKED_POLICY'); self.assertIn('FOLDER_NOT_AUTHORIZED',p['authorization_reasons'])
 def test_revocation_blocks_immediately(self):
  a=copy.deepcopy(A); a['control']['revoked']=True
  p=plan_record(REAL[0],C,M,P,a); self.assertEqual(p['plan_state'],'BLOCKED_POLICY'); self.assertIn('AUTH_REVOKED',p['authorization_reasons'])
 def test_authorization_has_forbidden_promotions(self):
  self.assertTrue({'SILVER_PROMOTION','GOLD_PROMOTION','SERVING_WRITE','PUBLICATION','FINANCIAL_IDENTITY_AUTO_PROMOTION'}.issubset(set(A['forbidden_effects'])))
 def test_no_content_read_is_performed_by_planner(self):
  self.assertNotIn('content',plan_record(REAL[0],C,M,P,A))

if __name__=='__main__': unittest.main()
