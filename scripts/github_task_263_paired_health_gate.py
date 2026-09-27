#!/usr/bin/env python3
from robo_dados_publicos.research.task263_paired_health_645_vs_648 import *
def main():
 c=load_config();e=load_evidence();assert c["targets"][0]["role"]=="HEALTH_CONTROL";assert c["targets"][1]["control"].endswith("000648/2026")
 assert e["adjudication"]["648_absence_proven"] is False;print("PASS_TASK263_PAIRED_HEALTH_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
