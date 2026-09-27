import unittest
from pathlib import Path
from robo_dados_publicos.manual_ingest.drive_ingestion_controller import load_controller_contract, classify_metadata

ROOT=Path(__file__).resolve().parents[1]
V2=load_controller_contract(ROOT/'config/drive_ingestion_controller.v2.json')
V3=load_controller_contract(ROOT/'config/drive_ingestion_controller.v3.json')

class Task069Tests(unittest.TestCase):
    def rec(self,title,id='x'):
        return {'id':id,'title':title,'mime_type':'application/pdf','in_authorized_scope':True,'content_hydrated':False}
    def test_jom_plus_planning_resolves_primary_journal(self):
        for title in ['SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf','SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf','SOURCE_JOM_7024_2025-07-08_LDO_7141_2025.pdf']:
            d=classify_metadata(self.rec(title),V3)
            self.assertEqual((d.family,d.route),('JORNAL_OFICIAL','AUTO_INGEST'))
            self.assertIn('PRIMARY_FAMILY_RULE_APPLIED',d.reasons)
    def test_manifest_stays_review(self):
        d=classify_metadata(self.rec('MANIFEST_F01_PPA_LDO_LOA_2026_V03'),V3)
        self.assertEqual(d.route,'REVIEW'); self.assertIsNone(d.family)
    def test_standalone_planning_stays_review(self):
        d=classify_metadata(self.rec('SOURCE_PPA_2026_2029_LEI_7213_2025_LIMEIRA.pdf'),V3)
        self.assertEqual((d.family,d.route),('PPA','REVIEW'))
    def test_generic_multi_match_still_review(self):
        d=classify_metadata(self.rec('JOM PPA documento.pdf'),V3)
        self.assertEqual(d.route,'REVIEW')
    def test_v2_legacy_unchanged(self):
        d=classify_metadata(self.rec('SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf'),V2)
        self.assertEqual(d.route,'REVIEW')
    def test_no_remote_effects(self):
        for key in ('content_read_authorized','drive_write_authorized','bronze_write_authorized','silver_write_authorized','gold_write_authorized','serving_authorized','publication_authorized'):
            self.assertFalse(V3[key])

if __name__=='__main__': unittest.main()
