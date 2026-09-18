#!/usr/bin/env python3
from robo_dados_publicos.research.task268_pncp_history_probe_645 import load_config,load_evidence
def main():
    c=load_config();e=load_evidence()
    assert c["target"]["requested_url"]=="https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/645/historico"
    assert e["live_state"]=="NOT_AUTHORIZED_NOT_EXECUTED"
    print("PASS_TASK268_PNCP_HISTORY_645_CARRIER_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
