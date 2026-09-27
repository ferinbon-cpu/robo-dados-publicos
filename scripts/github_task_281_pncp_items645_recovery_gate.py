#!/usr/bin/env python3
from robo_dados_publicos.research.task281_pncp_items645_recovery import load_config,load_evidence
c=load_config();e=load_evidence();assert e["live_state"]=="NOT_AUTHORIZED_NOT_EXECUTED";print("PASS_TASK281_PNCP_ITEMS645_RECOVERY_CARRIER_GATE")
