#!/usr/bin/env python3
from robo_dados_publicos.research.task276_linked_contract_page1 import load_config,load_evidence
def main():
 c=load_config();e=load_evidence();assert c["target"]["pagina"]==1 and c["target"]["tamanhoPagina"]==50;assert e["source_task275"]["absence_inference"] is False;print("PASS_TASK276_LINKED_CONTRACT_PAGE1_CARRIER");return 0
if __name__=="__main__":raise SystemExit(main())
