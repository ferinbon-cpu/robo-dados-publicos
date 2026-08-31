import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.analytics.bi_model import BIModelError, build_dataset, deterministic_key, load_contract

ROOT=Path(__file__).resolve().parents[1]

class BI001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=load_contract()
        cls.fixture=json.loads((ROOT/'tests/fixtures/bi_001_sanitized_input.json').read_text())

    def test_all_six_schemas_and_fixture_rows(self):
        self.assertEqual(6,len(self.contract['datasets']))
        for dataset, rows in self.fixture.items(): self.assertEqual(rows,build_dataset(dataset,rows,self.contract))

    def test_key_is_deterministic_and_ids_remain_text(self):
        self.assertEqual(deterministic_key('X',['001',1]),deterministic_key('X',['001',1]))
        self.assertIsInstance(build_dataset('BI_SIOPE_SERIES',self.fixture['BI_SIOPE_SERIES'])[0]['municipality_code'],str)

    def test_duplicate_invalid_date_and_enum_stop(self):
        row=self.fixture['BI_JORNAL_EVENTOS'][0]
        with self.assertRaisesRegex(BIModelError,'DUPLICATE_PRIMARY_KEY'): build_dataset('BI_JORNAL_EVENTOS',[row,row])
        bad=copy.deepcopy(row); bad['publication_date']='31/08/2026'
        with self.assertRaisesRegex(BIModelError,'TYPE'): build_dataset('BI_JORNAL_EVENTOS',[bad])
        bad=copy.deepcopy(row); bad['extraction_status']='MAGIC'
        with self.assertRaisesRegex(BIModelError,'ENUM'): build_dataset('BI_JORNAL_EVENTOS',[bad])

    def test_siope_long_periods_and_2025_closed_boundary(self):
        base=self.fixture['BI_SIOPE_SERIES'][0]
        rows=[]
        for year in range(2016,2025):
            row=copy.deepcopy(base); row.update(year=year,annual_period='P1' if year==2016 else 'P6',metric_id=f'm{year}',provenance_id=f'p{year}') ; rows.append(row)
        self.assertEqual(9,len(build_dataset('BI_SIOPE_SERIES',rows)))
        bad=copy.deepcopy(base); bad.update(year=2025,annual_period='P6')
        with self.assertRaisesRegex(BIModelError,'CLOSED_SERIES'): build_dataset('BI_SIOPE_SERIES',[bad])

    def test_journal_nullable_supplier_and_no_invented_cnpj(self):
        row=build_dataset('BI_JORNAL_EVENTOS',self.fixture['BI_JORNAL_EVENTOS'])[0]
        self.assertIsNone(row['supplier_name']); self.assertIsNone(row['supplier_cnpj'])
        self.assertEqual('LIMEIRA_JO_07315',row['source_id']); self.assertIn('/7315',row['logical_key'])
        self.assertIsInstance(row['value'],float)

    def test_candidate_never_financial_identity_and_blocked_preserved(self):
        base=self.fixture['BI_RECONCILIACAO'][0]
        bad=copy.deepcopy(base); bad['financial_identity_proven']=True
        with self.assertRaisesRegex(BIModelError,'CANDIDATE_FINANCIAL_IDENTITY'): build_dataset('BI_RECONCILIACAO',[bad])
        blocked=copy.deepcopy(base); blocked.update(status='BLOCKED',identity_status='BLOCKED')
        self.assertEqual('BLOCKED',build_dataset('BI_RECONCILIACAO',[blocked])[0]['status'])

    def test_provenance_privacy_unknown_field_and_source_status_fail_closed(self):
        row=copy.deepcopy(self.fixture['BI_JORNAL_EVENTOS'][0]); row['provenance_id']=''
        with self.assertRaisesRegex(BIModelError,'PROVENANCE'): build_dataset('BI_JORNAL_EVENTOS',[row])
        row=copy.deepcopy(self.fixture['BI_JORNAL_EVENTOS'][0]); row['cpf']='00000000000'
        with self.assertRaisesRegex(BIModelError,'PRIVACY'): build_dataset('BI_JORNAL_EVENTOS',[row])
        source=copy.deepcopy(self.fixture['BI_FONTES_STATUS'][0]); source['collection_status']='OPERATIONAL'
        with self.assertRaisesRegex(BIModelError,'ENUM'): build_dataset('BI_FONTES_STATUS',[source])

    def test_contract_is_looker_ready_and_offline(self):
        self.assertTrue(all(x['looker_ready'] for x in self.contract['datasets']))
        self.assertTrue(all(self.contract['remote_effects'][x]==0 for x in self.contract['remote_effects']))
        source=(ROOT/'robo_dados_publicos/analytics/bi_model.py').read_text()
        self.assertNotIn('urlopen',source); self.assertNotIn('googleapiclient',source)

if __name__=='__main__': unittest.main()
