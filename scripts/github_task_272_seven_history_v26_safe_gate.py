#!/usr/bin/env python3
from robo_dados_publicos.research.task272_seven_history_v26_safe import load_config,load_evidence
c=load_config();e=load_evidence();assert len(c["targets"])==7;assert e["live_state"]=="NOT_EXECUTED";print("PASS_TASK272_SEVEN_HISTORY_SAFE_CARRIER_GATE")
