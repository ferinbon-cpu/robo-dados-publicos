import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/evidence/TASK_073_JOURNAL_FULL_LOCAL_PROCESSING_0.8.0.json'

def test_task073_candidate_counts_and_hashes():
    e=json.loads(E.read_text(encoding='utf-8'))
    assert e['aggregate']['silver_pages']==817
    assert e['aggregate']['gold_events']==52
    assert e['aggregate']['rag_chunks']==1519
    assert e['candidate_set']['files']==12
    assert e['candidate_set']['bytes']==4698837
    assert len(e['candidate_set']['sha256'])==64
    assert sum(e['aggregate']['event_types'].values())==52
    for item in e['items']:
        assert item['silver_pages']>0
        assert item['gold_events']>0
        assert item['rag_chunks']>0
        for output in item['outputs'].values():
            assert output['bytes']>0
            assert len(output['sha256'])==64

def test_task073_privacy_and_persistence_boundaries():
    e=json.loads(E.read_text(encoding='utf-8'))
    p=e['privacy_audit']
    assert p['silver_raw_pii_regex_matches']==0
    assert p['rag_raw_pii_regex_matches']==0
    assert p['gold_textual_payload_raw_pii_regex_matches']==0
    assert p['synthetic_event_id_phone_regex_false_positives']==3
    assert all(v==0 for v in e['hard_boundaries'].values())
