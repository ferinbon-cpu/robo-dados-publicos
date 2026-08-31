#!/usr/bin/env python3
"""Offline, fail-closed repository gate for BI-002."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from robo_dados_publicos.analytics.bi_materialization import build_manifest, build_plan, load_policy, render_xlsx, validate_manifest
from robo_dados_publicos.analytics.bi_model import load_contract

def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def main():
 policy=load_policy(); contract=load_contract(); evidence=load('docs/evidence/BI_002_CONTROLLED_MATERIALIZATION_0.8.0.json')
 fixture=load('tests/fixtures/bi_002_materialization_input.json'); ci=(ROOT/'.github/workflows/ci-offline.yml').read_text()
 plans=[]
 for dataset,rows in fixture['datasets'].items():
  plan=build_plan(dataset,rows,contract); xlsx=render_xlsx(plan,contract); manifest=build_manifest(plan,xlsx)
  validate_manifest(plan,manifest,xlsx); plans.append(plan)
 module=(ROOT/'robo_dados_publicos/analytics/bi_materialization.py').read_text()
 expected={'BI_SIOPE_SERIES','BI_JORNAL_EVENTOS','BI_RECONCILIACAO','BI_FONTES_STATUS','BI_EXECUCOES_ROBO','BI_DICIONARIO'}
 checks={
  'tier':policy['tier']==evidence['tier']=='T0_OFFLINE_IMPLEMENTATION_REVIEW',
  'architecture':policy['architecture']==evidence['architecture']=='OPTION_3_CREATE_ONLY_SNAPSHOTS_PLUS_STABLE_SERVING_SHEET',
  'root_planned_only':policy['future_drive_root']==evidence['root']=='13_BI' and evidence['root_created'] is False,
  'reserved_roots':len(policy['reserved_roots'])==13 and policy['reserved_roots'][9]=='09_SCRIPTS',
  'six_datasets':set(policy['dataset_allowlist'])==expected==set(fixture['datasets']) and len(plans)==6,
  'create_only_future':policy['create_only'] and not any(policy[x] for x in ('overwrite','delete','replace')),
  'tier_separation':policy['snapshot_tier']=='T2_CREATE_ONLY' and policy['serving_tier']=='T3_MUTATING_OR_PUBLICATION',
  'no_authorization':not any(policy[x] for x in ('remote_execution_authorized','serving_mutation_authorized','looker_publication_authorized')),
  'deterministic_artifacts':all(p.snapshot_id in p.proposed_snapshot_filename and p.canonical_matrix_sha256.startswith(p.snapshot_id) for p in plans),
  'synthetic_fixture':fixture['classification']=='SYNTHETIC_SANITIZED_TEST_ONLY' and fixture['operational_evidence'] is False,
  'zero_effects':all(evidence[x]==0 for x in ('drive_reads','drive_writes','source_network','looker_api_calls','publication')),
  'no_runtime_transport':all(x not in module for x in ('googleapiclient','requests','DriveService')),
  'no_schedule_recurrence':evidence['schedule'] is False and evidence['recurrence'] is False,
  'release_task_boundaries':evidence['release_boundary_unchanged'] and evidence['task_023_intact'] and not evidence['task_024_authorized'],
  'ci': 'python scripts/github_bi_002_materialization_gate.py' in ci
 }
 failed=[k for k,v in checks.items() if not v]; status='PASS_BI_002_CONTROLLED_MATERIALIZATION_IMPLEMENTATION_OFFLINE' if not failed else 'STOP'
 print(json.dumps({'status':status,'checks':checks,'failed_checks':failed},sort_keys=True)); return bool(failed)
if __name__=='__main__': raise SystemExit(main())
