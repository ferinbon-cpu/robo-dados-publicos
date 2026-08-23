import json
import unittest
from pathlib import Path


class TestM4EPromotion(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def load_json(self, relative_path):
        return json.loads((self.root / relative_path).read_text(encoding='utf-8'))

    def test_candidate_evidence_is_preserved_after_promotion(self):
        candidate = self.load_json('release_manifest_v01_0.5.8.json')
        active = self.load_json('release_manifest_v01_0.5.8_active.json')
        self.assertEqual('CANDIDATE', candidate['status'])
        self.assertEqual('ACTIVE', active['status'])
        self.assertEqual('0.5.8', active['promoted_from_candidate'])

    def test_promotion_keeps_financial_identity_fail_closed(self):
        active = self.load_json('release_manifest_v01_0.5.8_active.json')
        self.assertEqual('PROHIBITED', active['safety']['financial_identity_auto_promotion'])
        self.assertEqual('CANDIDATE_ONLY', active['safety']['reconciliation_matches'])

    def test_tda_remains_blocked_and_production_collection_opt_in(self):
        active = self.load_json('release_manifest_v01_0.5.8_active.json')
        discovery = self.load_json('config/limeira_sources_discovery.json')
        tda = next(x for x in discovery['surfaces'] if x['source_id'] == 'LIMEIRA_TDA_PORTAL')
        journal = next(x for x in discovery['surfaces'] if x['source_id'] == 'LIMEIRA_JORNAL_OFICIAL')
        self.assertEqual('BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN', active['open_gates']['tda_limeira'])
        self.assertEqual('BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN', tda['status'])
        self.assertFalse(tda['production_collection_enabled'])
        self.assertFalse(journal['production_collection_enabled'])


if __name__ == '__main__':
    unittest.main()
