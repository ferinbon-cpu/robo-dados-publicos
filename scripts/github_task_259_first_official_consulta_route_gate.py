#!/usr/bin/env python3
from robo_dados_publicos.research.task259_first_official_consulta_route import *
def main():
 c=load_config();e=load_evidence();t=c["target"];assert t["url"].startswith("https://pncp.gov.br/api/consulta/v1/")
 x=cmd(t["url"],"/tmp/x",connect_timeout=15,max_time=90,max_body_bytes=1048576);assert "--location" not in x and x[x.index("--retry")+1]=="0"
 assert e["route_template_proven"];print("PASS_TASK259_FIRST_OFFICIAL_CONSULTA_ROUTE_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
