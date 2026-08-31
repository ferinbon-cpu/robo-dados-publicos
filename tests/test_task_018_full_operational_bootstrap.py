import hashlib, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

from robo_dados_publicos.operational.bootstrap_batch import BootstrapBatch, Budget, deduplicate_discovery, validate_canonical_projection
from robo_dados_publicos.operational.bootstrap_adapters import JornalSourceAdapter, JournalProcessorAdapter, DriveCreateOnlyStore

ROOT=Path(__file__).resolve().parents[1]; CONFIG=json.loads((ROOT/'config/operational_bootstrap.full.v1.json').read_text())

def auth(identity='b'*40):
 a=json.loads((ROOT/'docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json').read_text()); a.update({'authorized':True,'status':'AUTHORIZED','single_batch_authorized':True,'implementation_merge_sha':'a'*40,'authorization_sha':identity})
 for k in ('source_read_authorized','drive_read_authorized','drive_create_only_authorized','processing_authorized','reconciliation_read_authorized','product_generation_authorized','product_publication_create_only_authorized'): a[k]=True
 return a

def row(key, host='ecrie.com.br', url=None): return {'source_id':'LIMEIRA_JO_'+key.upper(),'logical_key':key,'url':url or f'https://{host}/{key}.pdf','allowed_hosts':['ecrie.com.br','limeira.sp.gov.br','www.limeira.sp.gov.br'],'publication_date':'2026-08-01','source_page_url':'https://www.limeira.sp.gov.br/jornaloficial','archive_class':'modern','edition':7311}
class Ocr(Exception): status='STOP_OCR_REQUIRED'
class Source:
 def __init__(self,rows,telemetry=None): self.rows,self.gets,self.discoveries=rows,[],[]; self.telemetry=telemetry or {'robots_get_count':1,'index_get_count':1}
 def discover(self,family,maximum_pages): self.discoveries.append(family['source_family']); return self.rows,self.telemetry
 def get(self,url,maximum_bytes): self.gets.append(url); data=b'bad' if 'bad' in url else b'%PDF synthetic '+url.encode(); host=url.split('/')[2]; return data,{'https':True,'final_host':host,'content_type':'application/pdf'}
class Store:
 def __init__(self): self.objects={}; self.creates=[]; self.readbacks=[]
 def lookup(self,destination,logical_key,suffix=''):
  name=logical_key.replace('/','_')+suffix; value=self.objects.get((destination,name)); return dict(value) if value else None
 def create(self,destination,name,data,metadata):
  digest=hashlib.sha256(data).hexdigest(); key=(destination,name)
  if key in self.objects:
   if self.objects[key]['sha256']!=digest: raise RuntimeError('STOP_CREATE_ONLY_INVARIANT')
   status='REUSED_IDENTICAL'
  else: self.objects[key]={'data':data,'sha256':digest,'bytes':len(data),**metadata}; self.creates.append((destination,name)); status='CREATED'
  self.readback(destination,name); return {'status':status,'sha256':digest,'bytes':len(data),'name':name}
 def readback(self,destination,name):
  self.readbacks.append((destination,name)); value=self.objects.get((destination,name))
  if not value: raise RuntimeError('STOP_MANIFEST_INTEGRITY')
  return {'name':name,'sha256':value['sha256'],'bytes':value['bytes']}
class Processor:
 def __init__(self,fail_once=None,tasks=None,many=0): self.fail_once=fail_once; self.calls=[]; self.tasks=tasks or []; self.many=many
 def process(self,item,data):
  self.calls.append(item['logical_key'])
  if self.fail_once==item['logical_key']: self.fail_once=None; raise Ocr()
  layers={'Silver':[(item['source_id']+'_silver.jsonl',b'{}')],'Gold':[],'RAG':[(item['source_id']+'_rag.jsonl',b'{}')],'Documentos':[]}
  if self.many: layers={'Silver':[(f'{item["source_id"]}_{i}.json',b'{}') for i in range(self.many)]}
  return {'layers':layers,'tasks':list(self.tasks),'metrics':{'status':'PASS_PROCESSING'}}
class Reconciler:
 def __init__(self): self.calls=[]
 def execute(self,task,work_dir,maximum_requests): self.calls.append(task['task_id']); return {'task_id':task['task_id'],'status':'MATCH_CANDIDATE'},1

class Task018Tests(unittest.TestCase):
 def run_batch(self,rows,store=None,processor=None,reconciler=None,config=None,authorization=None,validator=lambda c:True,execution=None):
  td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); source=Source(rows); store=store or Store(); batch=BootstrapBatch(config or CONFIG,source,store,processor or Processor(),reconciler=reconciler,canonical_validator=validator); result=batch.run(Path(td.name)/'out',authorization or auth(),execution=execution); return result,source,store,Path(td.name)/'out'
 def test_pending_authorization_zero_effects_and_audit(self):
  r,s,st,out=self.run_batch([row('a')],authorization={'authorized':False}); self.assertEqual('STOP_OWNER_AUTHORIZATION_REQUIRED',r['status']); self.assertEqual([],s.gets); self.assertEqual([],st.creates); self.assertTrue((out.parent/'task-018-audit/operational_result.json').is_file())
 def test_canonical_drift_zero_effects(self):
  r,s,st,_=self.run_batch([row('a')],validator=lambda c:False); self.assertEqual('STOP_CANONICAL_POLICY_DRIFT',r['status']); self.assertEqual(([],[]),(s.gets,st.creates))
 def test_canonical_projection_and_ecrie_proof(self):
  self.assertTrue(validate_canonical_projection(CONFIG)); family=next(x for x in CONFIG['eligibility'] if x['source_family']=='LIMEIRA_JORNAL_OFICIAL'); self.assertIn('ecrie.com.br',family['allowed_hosts']); self.assertEqual('DECLARED_LINKS_IN_PROVEN_MODERN_WINDOW_2026_08',family['scope'])
 def test_unknown_host_blocked_but_ecrie_accepted(self):
  r,_,_,_=self.run_batch([row('good'),row('unknown',host='surprise.example')]); states={x['logical_key']:x['status'] for x in r['items']}; self.assertEqual('PASS_ITEM',states['good']); self.assertEqual('STOP_DOCUMENT_NOT_PDF',states['unknown'])
 def test_duplicate_conflicting_url_is_ambiguity(self):
  accepted,ambiguous=deduplicate_discovery([row('same',url='https://ecrie.com.br/a.pdf'),row('same',url='https://ecrie.com.br/b.pdf')]); self.assertEqual([],accepted); self.assertEqual('STOP_DISCOVERY_AMBIGUITY',ambiguous[0]['status'])
 def test_drain_ocr_continues_and_detailed_summary(self):
  r,s,st,out=self.run_batch([row('a'),row('ocr'),row('z')],processor=Processor(fail_once='ocr')); self.assertEqual('COMPLETE',r['status']); self.assertEqual(3,len(s.gets)); self.assertEqual('STOP_OCR_REQUIRED',{x['logical_key']:x['status'] for x in r['items']}['ocr']); summary=(out/'operational_summary.md').read_text()
  for term in ('families_considered','discovered','bronze_created','processed','derived','quarantine','ocr_required','reconciliation_tasks','budget','checkpoint','publication'): self.assertIn(term,summary)
 def test_all_get_categories_count_and_page_budget(self):
  b=Budget(CONFIG['hard_safety_ceilings']); b.add_gets('robots_get_count',2); b.add_gets('index_get_count',3); b.before_document(); b.add_gets('reconciliation_get_count',4); self.assertEqual(10,b.counts['total_remote_get_count']); self.assertEqual(3,b.counts['index_get_count'])
  cfg=json.loads(json.dumps(CONFIG['hard_safety_ceilings'])); cfg['maximum_index_discovery_pages']=1; b=Budget(cfg); self.assertRaisesRegex(RuntimeError,'PARTIAL',b.add_gets,'index_get_count',2)
 def test_aggregate_and_drive_create_budget_before_effect(self):
  config=json.loads(json.dumps(CONFIG)); config['hard_safety_ceilings']['maximum_drive_create_operations']=2
  r,_,st,_=self.run_batch([row('a')],processor=Processor(many=5),config=config); self.assertEqual('PARTIAL_BATCH_SAFETY_BUDGET_REACHED',r['status']); self.assertLessEqual(len(st.creates),2)
 def test_reconciler_invoked_and_budget_enforced(self):
  tasks=[{'task_id':f't{i}','target_source':'LIMEIRA_CONTRATOS'} for i in range(3)]; rec=Reconciler(); config=json.loads(json.dumps(CONFIG)); config['hard_safety_ceilings']['maximum_live_reconciliation_requests']=2
  r,_,_,_=self.run_batch([row('a')],processor=Processor(tasks=tasks),reconciler=rec,config=config); self.assertEqual('PARTIAL_BATCH_SAFETY_BUDGET_REACHED',r['status']); self.assertEqual(['t0','t1'],rec.calls)
 def test_no_eligible_reconciliation_is_explicit(self):
  r,_,_,_=self.run_batch([row('a')],processor=Processor(tasks=[{'task_id':'x','target_source':'LIMEIRA_TDA_PORTAL'}]),reconciler=Reconciler()); self.assertEqual('NOT_EXECUTED_NO_ELIGIBLE_TASK',r['reconciliation']['status'])
 def test_existing_bronze_resumes_missing_derived_without_duplicate(self):
  st=Store(); data=b'%PDF synthetic https://ecrie.com.br/a.pdf'; st.objects[('Bronze','a.pdf')]={'data':data,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'source_url':'https://ecrie.com.br/a.pdf'}
  r,s,st,_=self.run_batch([row('a')],store=st); self.assertEqual([],s.gets); self.assertEqual('REUSED_IDENTICAL',r['items'][0]['bronze_state']); self.assertIn(('Silver','LIMEIRA_JO_A_silver.jsonl'),st.creates); self.assertNotIn(('Bronze','a.pdf'),st.creates)
 def test_first_processing_stop_then_same_run_resumes_bronze(self):
  st=Store(); first,_,st,_=self.run_batch([row('a')],store=st,processor=Processor(fail_once='a'),execution={'github_run_id':'synthetic-run'})
  self.assertEqual('STOP_OCR_REQUIRED',first['items'][0]['status']); bronze_creates=st.creates.count(('Bronze','a.pdf'))
  second,source,st,_=self.run_batch([row('a')],store=st,execution={'github_run_id':'synthetic-run'})
  self.assertEqual('PASS_ITEM',second['items'][0]['status']); self.assertEqual([],source.gets); self.assertEqual(bronze_creates,st.creates.count(('Bronze','a.pdf')))
 def test_create_only_uses_readback_and_publication_manifest_last(self):
  r,_,st,out=self.run_batch([row('a')]); before=len(st.creates); BootstrapBatch(CONFIG,None,st,None).publish(out,r); published=st.creates[before:]; outputs=[x for x in published if x[0]=='Outputs']; self.assertTrue(outputs[-1][1].endswith('manifest.json')); self.assertTrue(all(('Outputs',name) in st.readbacks for _,name in outputs)); self.assertTrue(r['publication']['final_readback_required'])
 def test_same_authorization_cannot_publish_second_batch(self):
  st=Store(); first,_,st,out=self.run_batch([row('a')],store=st); BootstrapBatch(CONFIG,None,st,None).publish(out,first)
  td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); second=BootstrapBatch(CONFIG,Source([row('a')]),st,Processor(),canonical_validator=lambda c:True).run(Path(td.name)/'out',auth()); self.assertEqual('STOP_BATCH_AUTHORIZATION_CONSUMED',second['status'])
 def test_task017_identities_and_provenance(self):
  r,_,_,_=self.run_batch([row('a')]); self.assertTrue(r['snapshot_id'].startswith('SNAP-')); self.assertTrue(r['run_id'].startswith('RUN-')); self.assertTrue(r['batch_id'].startswith('BATCH-')); self.assertIn('implementation_merge_sha',r); self.assertIn('authorization_evidence_identity',r)
 def test_workflow_runtime_secrets_handoff_and_artifact(self):
  w=(ROOT/'.github/workflows/task-018-full-operational-bootstrap.yml').read_text(); self.assertNotIn('GOOGLE_CLIENT_ID',w)
  for secret in ('GOOGLE_DRIVE_CLIENT_ID','GOOGLE_DRIVE_CLIENT_SECRET','GOOGLE_DRIVE_REFRESH_TOKEN'): self.assertIn(secret,w)
  self.assertIn('pip install --disable-pip-version-check -r requirements.txt',w); self.assertIn('task-018-workspace/task-018-audit/',w); self.assertEqual(1,w.count('jobs:'))
  self.assertLess(w.index('T1_DISCOVER_AND_COLLECT'),w.index('T2_CREATE_ONLY_PERSIST_AND_PROCESS')); self.assertLess(w.index('T2_CREATE_ONLY_PERSIST_AND_PROCESS'),w.index('T3_CREATE_ONLY_PRODUCT_PUBLICATION'))
 def test_production_adapters_reuse_mature_components(self):
  from robo_dados_publicos.journal.official import JornalOficialLimeira
  from robo_dados_publicos.journal.processing import JournalPdfProcessor
  self.assertIsInstance(JornalSourceAdapter().journal,JornalOficialLimeira); self.assertIsInstance(JournalProcessorAdapter().processor,JournalPdfProcessor); self.assertTrue(hasattr(DriveCreateOnlyStore,'from_environment'))
 def test_fixture_disclaimer_and_policy(self):
  text=(ROOT/'tests/fixtures/task_018_bootstrap/README.txt').read_text(); [self.assertIn(x,text) for x in ('SYNTHETIC','NOT FROM LIVE SOURCES','NO REAL PERSONAL DATA','NO PROMOTION EFFECT')]
  self.assertFalse(CONFIG['schedule']); self.assertFalse(CONFIG['recurrence']); self.assertFalse(CONFIG['automatic_retry']); self.assertEqual('PROHIBITED',CONFIG['reconciliation']['financial_identity_auto_promotion'])
if __name__=='__main__': unittest.main()
