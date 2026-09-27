import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/evidence/TASK_074_PERSIST_JOURNAL_DERIVED_LAYERS_0.8.0.json'

def test_task074_all_nine_readbacks_match():
    e=json.loads(E.read_text(encoding='utf-8'))
    assert len(e['items'])==9
    assert e['aggregate']['drive_writes']==9
    assert e['aggregate']['readbacks']==9
    assert e['aggregate']['readback_matches']==9
    assert all(x['readback_match'] is True and len(x['sha256'])==64 for x in e['items'])
    assert {x['layer'] for x in e['items']}=={'SILVER','GOLD','RAG'}

def test_task074_no_overwrite_or_publication():
    e=json.loads(E.read_text(encoding='utf-8'))
    assert e['transport']['overwrite'] is False
    assert all(v==0 for v in e['hard_boundaries'].values())
    assert e['aggregate']['silver_pages']==817
    assert e['aggregate']['gold_events']==52
    assert e['aggregate']['rag_chunks']==1519
