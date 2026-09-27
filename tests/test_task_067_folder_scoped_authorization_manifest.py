import copy, json, unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.folder_authorization import is_authorized, load_authorization, validate_manifest
ROOT=Path(__file__).resolve().parents[1]
class Task067Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.t=load_authorization(ROOT/'config/folder_authorization_manifest.v1.json')
 def active(self):
  x=copy.deepcopy(self.t); x['enabled']=True; x['scope']['folder_ids']=['F']; x['scope']['families']=['JORNAL_OFICIAL']; x['allowed_effects']=['CONTENT_READ_FOR_HASH_AND_INGEST']; x['control']['owner_authorization_ref']='OWNER_TOKEN'; return x
 def test_template_disabled(self): self.assertFalse(is_authorized(self.t,folder_id='F',family='JORNAL_OFICIAL',effect='CONTENT_READ_FOR_HASH_AND_INGEST',maturity_ready=True))
 def test_exact_scope_can_authorize(self): self.assertTrue(is_authorized(self.active(),folder_id='F',family='JORNAL_OFICIAL',effect='CONTENT_READ_FOR_HASH_AND_INGEST',maturity_ready=True))
 def test_wrong_family_blocks(self): self.assertFalse(is_authorized(self.active(),folder_id='F',family='FUNDEB',effect='CONTENT_READ_FOR_HASH_AND_INGEST',maturity_ready=True))
 def test_maturity_blocks(self): self.assertFalse(is_authorized(self.active(),folder_id='F',family='JORNAL_OFICIAL',effect='CONTENT_READ_FOR_HASH_AND_INGEST',maturity_ready=False))
 def test_revocation_blocks(self):
  x=self.active(); x['control']['revoked']=True; self.assertFalse(is_authorized(x,folder_id='F',family='JORNAL_OFICIAL',effect='CONTENT_READ_FOR_HASH_AND_INGEST',maturity_ready=True))
 def test_enabled_requires_owner_ref(self):
  x=self.active(); x['control']['owner_authorization_ref']=None
  with self.assertRaises(ValueError): validate_manifest(x)
if __name__=='__main__': unittest.main()
