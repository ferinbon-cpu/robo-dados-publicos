#!/usr/bin/env python3
from robo_dados_publicos.research.task277_linked_contract_http404_diagnostic import load_config,load_evidence
def main():
 c=load_config();e=load_evidence();assert c["target"]["pagina"]==1 and c["target"]["tamanhoPagina"]==50;assert e["source_task276"]["absence_inference"] is False;print("PASS_TASK277_LINKED_CONTRACT_HTTP404_DIAGNOSTIC_CARRIER");return 0
if __name__=="__main__":raise SystemExit(main())
