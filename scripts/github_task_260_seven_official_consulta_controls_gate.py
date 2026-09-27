#!/usr/bin/env python3
from robo_dados_publicos.research.task260_seven_official_consulta_controls import *
def main():
 c=load_config();e=load_evidence();assert [t["sequencial"] for t in c["targets"]]==[639,645,648,655,653,654,69];assert e["first_control_excluded_from_batch"];print("PASS_TASK260_SEVEN_OFFICIAL_CONSULTA_CONTROLS_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
