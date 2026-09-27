#!/usr/bin/env python3
from robo_dados_publicos.research.task275_linked_contract_http400_diagnostic import load_config,load_evidence
def main():
 c=load_config();e=load_evidence();assert c["probe"]["accept_header"]=="*/*";assert e["adjudication"]["http400_is_absence"] is False;print("PASS_TASK275_LINKED_CONTRACT_DIAGNOSTIC_CARRIER");return 0
if __name__=="__main__":raise SystemExit(main())
