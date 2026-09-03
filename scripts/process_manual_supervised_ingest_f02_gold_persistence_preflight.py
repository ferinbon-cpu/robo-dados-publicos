#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_persistence import build_and_verify_candidate  # noqa: E402
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import load_json  # noqa: E402
CONFIG=ROOT/"config/manual_supervised_ingest_f02_gold_persistence.v1.json"
def main()->int:
    _,result=build_and_verify_candidate(load_json(CONFIG),root=ROOT)
    print(json.dumps(result,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
