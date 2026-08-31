#!/usr/bin/env python3
"""Offline structural gate that rejects a non-executable TASK 018 skeleton."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from robo_dados_publicos.operational.bootstrap_batch import validate_canonical_projection

def main():
 c=json.loads((ROOT/'config/operational_bootstrap.full.v1.json').read_text()); a=json.loads((ROOT/'docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_OWNER_AUTHORIZATION_0.8.0.json').read_text())
 w=(ROOT/'.github/workflows/task-018-full-operational-bootstrap.yml').read_text(); entry=(ROOT/'scripts/github_task_018_full_operational_bootstrap.py').read_text(); adapters=(ROOT/'robo_dados_publicos/operational/bootstrap_adapters.py').read_text(); engine=(ROOT/'robo_dados_publicos/operational/bootstrap_batch.py').read_text()
 ceilings=c['hard_safety_ceilings']; required={'maximum_runtime_seconds','maximum_total_remote_get_count','maximum_index_discovery_pages','maximum_documents','maximum_bytes_per_document','maximum_aggregate_source_bytes','maximum_drive_create_operations','maximum_live_reconciliation_requests'}
 canonical_refs=('config/limeira_sources_discovery.json','config/sources.jornal_oficial_7310_gate.json','config/automation_policy.v1.json','config/cloud.json','TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING','TASK_015_M8_R3_PUBLICATION_CLOSURE')
 wrong=('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_REFRESH_TOKEN')
 checks={
 'drain_not_one':c['batch_semantic'].startswith('DRAIN_ALL') and ceilings['maximum_documents']>1,
 'canonical_cross_validation':validate_canonical_projection(c) and all(x in engine for x in canonical_refs),
 'proven_host_and_narrow_scope':'ecrie.com.br' in json.dumps(c) and 'DECLARED_LINKS_IN_PROVEN_MODERN_WINDOW_2026_08' in json.dumps(c) and 'LEGACY_DISCOVERY_WINDOWS' not in json.dumps(c),
 'pending_one_shot':a['authorized'] is False and a['implementation_merge_sha'] is None and a['single_batch_authorized'] is False and a['consumed'] is False and a['further_execution_authorized'] is False and a['retry_authorized'] is False,
 'production_adapters':all(x in adapters for x in ('JornalOficialLimeira','JournalPdfProcessor','DriveRESTClient','OAuthCredentials','TokenProvider','CloudLayout','ReconciliationExecutor','LimeiraContractsResolver')) and 'build_drive_store' in entry,
 'no_live_stub':'STOP_CREDENTIAL_CAPABILITY' not in entry and 'build_source_adapter' in entry,
 'real_reconciliation':'.reconciler.execute(' in engine and 'reconciliation_get_count' in engine and 'financial_identity_auto_promotion' in engine,
 'real_readback':'.readback("Outputs"' in engine and 'self.readback(destination, name)' in adapters,
 'real_publication':'self.store.create("Outputs"' in engine and 'manifest.json' in engine and 'PUBLISHED_CREATE_ONLY_READBACK_VERIFIED' in engine,
 'real_telemetry':all(x in engine for x in ('robots_get_count','index_get_count','document_get_count','reconciliation_get_count','total_remote_get_count')),
 'bounded':required<=set(ceilings) and all(isinstance(ceilings[x],int) and ceilings[x]>0 for x in required) and 'before_create()' in engine and 'accept_bytes(' in engine,
 'create_only':c['mutation_policy']=={'create_only':True,'overwrite':False,'replace':False,'delete':False},
 'manual_one_job_handoff':'workflow_dispatch:' in w and w.count('runs-on:')==1 and all(x in w for x in ('T1_DISCOVER_AND_COLLECT','T2_CREATE_ONLY_PERSIST_AND_PROCESS','T3_CREATE_ONLY_PRODUCT_PUBLICATION','--workspace task-018-workspace')),
 'runtime_installed':'setup-python@' in w and 'pip install --disable-pip-version-check -r requirements.txt' in w,
 'correct_secrets':all(x in w for x in ('GOOGLE_DRIVE_CLIENT_ID','GOOGLE_DRIVE_CLIENT_SECRET','GOOGLE_DRIVE_REFRESH_TOKEN')) and not any(x in w for x in wrong),
 'audit_artifact':'task-018-workspace/task-018-audit/' in w and 'task-018-audit' in entry and 'if: always()' in w,
 'manual_no_retry':all(x not in w for x in ('schedule:','cron:','workflow_run:','repository_dispatch:')) and not c['schedule'] and not c['recurrence'] and not c['automatic_retry'],
 }
 print(json.dumps({'gate':'TASK_018_FULL_OPERATIONAL_BOOTSTRAP_DESIGN','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks},indent=2)); return 0 if all(checks.values()) else 1
if __name__=='__main__': raise SystemExit(main())
