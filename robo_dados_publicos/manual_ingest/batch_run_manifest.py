from __future__ import annotations
import hashlib, json


def metadata_snapshot_sha256(records):
    payload=json.dumps(records,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

def validate_batch_manifest(m):
    counters=m.get('counters',{})
    if any((not isinstance(v,int) or v<0) for v in counters.values()): raise ValueError('STOP_BAD_BATCH_COUNTER')
    if len(m.get('item_decisions',[])) != counters.get('metadata_records',0): raise ValueError('STOP_BATCH_DECISION_COUNT_MISMATCH')
    writes=sum(counters.get(k,0) for k in ('drive_writes','bronze_writes','silver_writes','gold_writes','serving_writes','publications'))
    reads=counters.get('source_content_reads',0)+counters.get('hash_reads',0)
    if (writes or reads) and not m.get('authorization_id'): raise ValueError('STOP_BATCH_EFFECT_WITHOUT_AUTHORIZATION')
    if writes and m.get('final_readback_verified') is not True: raise ValueError('STOP_BATCH_WRITE_WITHOUT_READBACK')
    if not m.get('git_sha'): raise ValueError('STOP_BATCH_GIT_SHA_MISSING')
    return True
