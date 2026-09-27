#!/usr/bin/env python3
from robo_dados_publicos.research.task261_three_500_reobserve import *
def main():
 c=load_config();e=load_evidence();assert len(c["targets"])==3;assert e["adjudication"]["three_absent_proven"] is False
 assert scalar_projection({"status":500,"message":"x"*500,"nested":{"x":1}})=={"status":500,"message":"x"*400}
 print("PASS_TASK261_THREE_500_REOBSERVE_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
