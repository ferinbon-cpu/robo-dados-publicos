import unittest
from robo_dados_publicos.manual_ingest.batch_run_manifest import metadata_snapshot_sha256, validate_batch_manifest

def base():
 return {'git_sha':'abc','authorization_id':None,'item_decisions':[{'file_id':'x'}],'counters':{'metadata_records':1,'source_content_reads':0,'hash_reads':0,'drive_writes':0,'bronze_writes':0,'silver_writes':0,'gold_writes':0,'serving_writes':0,'publications':0,'stops':0,'warnings':0},'final_readback_verified':False}
class Task068Tests(unittest.TestCase):
 def test_snapshot_deterministic(self): self.assertEqual(metadata_snapshot_sha256([{'b':2,'a':1}]),metadata_snapshot_sha256([{'a':1,'b':2}]))
 def test_no_effect_manifest_valid(self): self.assertTrue(validate_batch_manifest(base()))
 def test_effect_requires_auth(self):
  x=base(); x['counters']['hash_reads']=1
  with self.assertRaises(ValueError): validate_batch_manifest(x)
 def test_write_requires_readback(self):
  x=base(); x['authorization_id']='A'; x['counters']['bronze_writes']=1
  with self.assertRaises(ValueError): validate_batch_manifest(x)
 def test_decision_count_must_match(self):
  x=base(); x['counters']['metadata_records']=2
  with self.assertRaises(ValueError): validate_batch_manifest(x)
if __name__=='__main__': unittest.main()
