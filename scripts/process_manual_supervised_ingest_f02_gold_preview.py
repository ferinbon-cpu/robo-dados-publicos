#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import build_preview,load_json,validate_config
ROOT=Path(__file__).resolve().parents[1]; DEFAULT_CONFIG=ROOT/"config/manual_supervised_ingest_f02_gold_preview.v1.json"
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",default=str(DEFAULT_CONFIG)); p.add_argument("--dry-run",action="store_true"); p.add_argument("--output"); a=p.parse_args(); c=load_json(a.config)
    if a.dry_run: print(json.dumps(validate_config(c),sort_keys=True)); return 0
    candidate,result=build_preview(c,root=ROOT); rendered=json.dumps(candidate,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if a.output: Path(a.output).write_text(rendered,encoding="utf-8")
    else: print(rendered,end="")
    if result["gold_payload_persisted"] or result["drive_write_count"]!=0: raise RuntimeError("STOP_F02_GOLD_PREVIEW_UNEXPECTED_EFFECT")
    return 0
if __name__=="__main__": raise SystemExit(main())
