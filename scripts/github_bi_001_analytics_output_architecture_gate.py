#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from robo_dados_publicos.analytics.bi_model import build_dataset, load_contract
from robo_dados_publicos.orchestration.cloud_runner import EXPECTED_ROOT_NAMES

def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def run(path): return subprocess.run([sys.executable,str(ROOT/path)],cwd=ROOT,capture_output=True,text=True).returncode==0

def main():
    contract=load_contract(); evidence=load('docs/evidence/BI_001_ANALYTICS_OUTPUT_ARCHITECTURE_0.8.0.json'); fixture=load('tests/fixtures/bi_001_sanitized_input.json')
    ci=(ROOT/'.github/workflows/ci-offline.yml').read_text(encoding='utf-8'); workflows=list((ROOT/'.github/workflows').glob('*bi-001*'))
    ids={x['dataset_id'] for x in contract['datasets']}; effects=contract['remote_effects']
    canonical_layers={name for name in EXPECTED_ROOT_NAMES if name[:2].isdigit()}
    checks={
      'tier_t0':contract['tier']==evidence['tier']=='T0_OFFLINE',
      'six_required_schemas':ids=={'BI_SIOPE_SERIES','BI_JORNAL_EVENTOS','BI_RECONCILIACAO','BI_FONTES_STATUS','BI_EXECUCOES_ROBO','BI_DICIONARIO'},
      'schemas_complete':all(x['primary_key'] and x['fields'] and x['source_layers'] and x['provenance']['required'] and x['update_strategy'] and x['looker_ready'] and x['privacy_class'] and x['semantic_constraints'] for x in contract['datasets']),
      'fixture_valid':all(build_dataset(k,v,contract) for k,v in fixture.items()),
      'zero_remote_effects':all(v==0 for v in effects.values()) and all(evidence[k]==0 for k in ('drive_reads','drive_writes','source_network','looker_api_calls','publication')),
      'no_live_workflow':not workflows and 'schedule:' not in ci,
      'no_authorization':evidence['task_024_authorized'] is False and evidence['bi_002_authorized'] is False and evidence['schedule'] is False and evidence['recurrence'] is False,
      'release_unchanged':evidence['release_boundary_unchanged'] is True,
      'task023_intact':evidence['task_023_intact'] is True and run('scripts/github_task_023_jornal_bounded_live_incremental_proof_implementation_review_gate.py'),
      'ci_only': 'python scripts/github_bi_001_analytics_output_architecture_gate.py' in ci,
      'architecture_governed':evidence['architecture_recommended'].startswith('OPTION_3_') and evidence['governance_status']=='GOVERNANCE_DECISION_REQUIRED',
      'drive_layer_no_collision': contract.get('canonical_drive_layers_reserved') == sorted(canonical_layers) and contract.get('future_drive_location_recommendation') == evidence.get('drive_location_recommended_not_created') == '13_BI' and evidence.get('canonical_drive_layers_00_to_12_reserved') is True and evidence.get('drive_location_collision_check') == 'PASS_13_BI_AFTER_12_SOFTWARE'
    }
    failed=[k for k,v in checks.items() if not v]
    print(json.dumps({'status':'PASS_BI_ANALYTICS_OUTPUT_ARCHITECTURE_OFFLINE' if not failed else 'STOP','checks':checks,'failed_checks':failed},sort_keys=True))
    return bool(failed)
if __name__=='__main__': raise SystemExit(main())
