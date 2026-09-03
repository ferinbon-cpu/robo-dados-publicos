from __future__ import annotations
import json, unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.auto_ingest_dry_run import plan_record, summarize_plan
from robo_dados_publicos.manual_ingest.drive_ingestion_controller import load_controller_contract
from robo_dados_publicos.manual_ingest.source_family_maturity import load_maturity_registry
from robo_dados_publicos.manual_ingest.ingestion_execution_policy import load_execution_policy
ROOT=Path(__file__).resolve().parents[1]

class Task066Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=load_controller_contract(ROOT/'config/drive_ingestion_controller.v2.json'); cls.m=load_maturity_registry(ROOT/'config/source_family_maturity_registry.v1.json'); cls.p=load_execution_policy(ROOT/'config/ingestion_execution_policy.v1.json')
 def plan(self,title,id='x',scope=True): return plan_record({'id':id,'title':title,'mime_type':'application/pdf','in_authorized_scope':True,'content_hydrated':False,'folder_scope_authorized':scope},self.c,self.m,self.p)
 def test_journal_can_be_eligible(self): self.assertEqual(self.plan('JORNAL_OFICIAL_7315.pdf')['plan_state'],'ELIGIBLE')
 def test_fundeb_is_blocked_by_maturity(self): self.assertEqual(self.plan('FUNDEB_2026.pdf')['plan_state'],'BLOCKED_MATURITY')
 def test_ppa_is_review(self): self.assertEqual(self.plan('PPA_2026_2029.pdf')['plan_state'],'REVIEW')
 def test_unknown_quarantines(self): self.assertEqual(self.plan('foto.pdf')['plan_state'],'QUARANTINE')
 def test_missing_folder_execution_scope_blocks_journal(self): self.assertEqual(self.plan('JORNAL_OFICIAL_7315.pdf',scope=False)['plan_state'],'BLOCKED_POLICY')
 def test_summary(self):
  items=[self.plan('JORNAL_OFICIAL_7315.pdf'),self.plan('FUNDEB_2026.pdf'),self.plan('PPA_2026.pdf'),self.plan('foto.pdf')]
  self.assertEqual(sum(summarize_plan(items).values()),4)
if __name__=='__main__': unittest.main()
