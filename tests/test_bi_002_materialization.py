import json
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from openpyxl import load_workbook
from robo_dados_publicos.analytics.bi_materialization import (
    BIMaterializationError, build_manifest, build_plan, future_preflight, load_policy,
    plan_serving, render_xlsx, validate_future_root, validate_manifest)
from robo_dados_publicos.analytics.bi_model import load_contract

ROOT=Path(__file__).resolve().parents[1]
FIX=json.loads((ROOT/'tests/fixtures/bi_002_materialization_input.json').read_text())

class TestBI002(unittest.TestCase):
 def setUp(self): self.contract=load_contract(); self.rows=FIX['datasets']
 def stop(self, code, fn, *a, **kw):
  with self.assertRaisesRegex(BIMaterializationError, code): fn(*a, **kw)
 def test_contract_boundary_and_six_datasets(self):
  p=load_policy(); self.assertEqual(p['future_drive_root'],'13_BI'); self.assertEqual(len(p['dataset_allowlist']),6); self.assertEqual(set(p['dataset_allowlist']),set(self.rows)); self.assertEqual(FIX['classification'],'SYNTHETIC_SANITIZED_TEST_ONLY')
 def test_reserved_roots(self):
  for root in load_policy()['reserved_roots']: self.stop('STOP_BI_RESERVED_ROOT',validate_future_root,root)
  self.stop('STOP_BI_RESERVED_ROOT',validate_future_root,'09_SCRIPTS')
 def test_all_datasets_and_xlsx_semantics(self):
  for dataset,rows in self.rows.items():
   plan=build_plan(dataset,rows); data=render_xlsx(plan); wb=load_workbook(BytesIO(data),data_only=False)
   self.assertEqual(wb.sheetnames,[dataset[:31]]); ws=wb.active
   self.assertEqual(ws.max_row,plan.row_count+1); self.assertEqual(ws.max_column,len(plan.ordered_columns)); self.assertEqual(tuple(c.value for c in ws[1]),plan.ordered_columns)
   self.assertFalse(ws.merged_cells); self.assertTrue(all(c.data_type!='f' for row in ws for c in row))
   manifest=build_manifest(plan,data); self.assertEqual(validate_manifest(plan,manifest,data),'PASS_BI_MATERIALIZATION_PLAN_OFFLINE')
 def test_order_hash_and_filename_determinism(self):
  row=self.rows['BI_SIOPE_SERIES'][0]; other={**row,'year':2017,'annual_period':'P6','source_sha256':'c'*64}
  a=build_plan('BI_SIOPE_SERIES',[other,row]); b=build_plan('BI_SIOPE_SERIES',[row,other])
  self.assertEqual((a.rows,a.canonical_matrix_sha256,a.snapshot_id,a.proposed_snapshot_filename),(b.rows,b.canonical_matrix_sha256,b.snapshot_id,b.proposed_snapshot_filename))
  changed={**other,'metric_value':999}; self.assertNotEqual(a.canonical_matrix_sha256,build_plan('BI_SIOPE_SERIES',[row,changed]).canonical_matrix_sha256)
  self.assertEqual(render_xlsx(a),render_xlsx(b))
 def test_duplicate_unknown_privacy_fail_closed(self):
  ds='BI_JORNAL_EVENTOS'; row=self.rows[ds][0]
  self.stop('STOP_BI_DUPLICATE_PRIMARY_KEY',build_plan,ds,[row,row])
  self.stop('STOP_BI_INVALID_SCHEMA',build_plan,ds,[{**row,'invented':1}])
  self.stop('STOP_BI_INVALID_SCHEMA',build_plan,ds,[{**row,'refresh_token':'x'}])
  self.stop('STOP_BI_UNKNOWN_DATASET',build_plan,'BI_ALERTAS',[])
 def test_siope_boundaries(self):
  row=self.rows['BI_SIOPE_SERIES'][0]
  self.assertEqual(build_plan('BI_SIOPE_SERIES',[row]).row_count,1)
  for values in ({'annual_period':'P6'},{'year':2025,'annual_period':'P6'},{'year':2017,'annual_period':'P1'}):
   self.stop('STOP_BI_INVALID_SCHEMA',build_plan,'BI_SIOPE_SERIES',[{**row,**values}])
  for year in range(2017,2025): self.assertEqual(build_plan('BI_SIOPE_SERIES',[{**row,'year':year,'annual_period':'P6'}]).row_count,1)
 def test_candidate_never_identity(self):
  row=self.rows['BI_RECONCILIACAO'][0]
  self.assertFalse(build_plan('BI_RECONCILIACAO',[row]).rows[0][14])
  self.stop('STOP_BI_INVALID_SCHEMA',build_plan,'BI_RECONCILIACAO',[{**row,'financial_identity_proven':True}])
 def test_manifest_mismatch_and_snapshot_mismatch(self):
  p=build_plan('BI_DICIONARIO',self.rows['BI_DICIONARIO']); x=render_xlsx(p); m=build_manifest(p,x)
  self.stop('STOP_BI_MANIFEST_MISMATCH',validate_manifest,p,{**m,'row_count':99},x)
  self.stop('STOP_BI_SNAPSHOT_ID_MISMATCH',future_preflight,p,{**m,'snapshot_id':'bad'})
 def test_future_boundaries(self):
  p=build_plan('BI_DICIONARIO',self.rows['BI_DICIONARIO']); m=build_manifest(p,render_xlsx(p))
  self.stop('STOP_BI_REMOTE_COLLISION_REQUIRES_READBACK',future_preflight,p,m,remote_collision=True)
  self.stop('STOP_BI_T2_NOT_AUTHORIZED',future_preflight,p,m)
  self.stop('STOP_BI_SERVING_MUTATION_NOT_AUTHORIZED',plan_serving,snapshot_validated=True)
  self.stop('STOP_BI_LOOKER_NOT_AUTHORIZED',plan_serving,snapshot_validated=True,t3_authorized=True)
 def test_zero_network_transport_publication(self):
  import robo_dados_publicos.analytics.bi_materialization as mod
  source=Path(mod.__file__).read_text(); forbidden=('requests','googleapiclient','socket','DriveService','schedule','recurrence')
  self.assertTrue(all(word not in source for word in forbidden)); self.assertFalse(load_policy()['remote_execution_authorized'])
  with patch('socket.socket',side_effect=AssertionError('network')): build_plan('BI_DICIONARIO',self.rows['BI_DICIONARIO'])

if __name__=='__main__': unittest.main()
