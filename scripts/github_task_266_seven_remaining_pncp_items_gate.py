#!/usr/bin/env python3
from robo_dados_publicos.research.task266_seven_remaining_pncp_items import *
def main():
 c=load_config();e=load_evidence();assert len(c["targets"])==7;assert e["already_queried_control"].endswith("000645/2026");print("PASS_TASK266_SEVEN_ITEMS_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
