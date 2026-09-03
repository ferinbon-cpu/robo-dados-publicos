import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/evidence/TASK_072_JOURNAL_NATIVE_TEXT_PROCESSABILITY_0.8.0.json'

def test_three_bronze_are_native_text_processable():
    e=json.loads(E.read_text(encoding='utf-8'))
    assert e['summary']['items']==3
    assert e['summary']['pass_text_extraction']==3
    assert e['summary']['stop_ocr_required']==0
    assert e['summary']['page_extract_errors']==0
    assert e['summary']['total_pages']==817
    for item in e['items']:
        assert item['status']=='PASS_TEXT_EXTRACTION'
        assert item['sparse_page_ratio'] < e['thresholds']['sparse_page_ratio_stop']
        assert item['total_extracted_chars'] >= e['thresholds']['min_total_chars']
        assert item['page_extract_errors']==0

def test_task072_has_no_remote_promotion_effects():
    e=json.loads(E.read_text(encoding='utf-8'))
    assert all(v==0 for v in e['hard_boundaries'].values())
