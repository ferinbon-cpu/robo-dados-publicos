#!/usr/bin/env python3
from robo_dados_publicos.research.task270_pncp_history_v26_safe_645 import load_config,load_evidence
def main():
 c=load_config();e=load_evidence();assert "usuarioNome" not in c["safe_projection"];assert e["live_state"]=="NOT_AUTHORIZED_NOT_EXECUTED";print("PASS_TASK270_HISTORY_V26_SAFE_CARRIER_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
