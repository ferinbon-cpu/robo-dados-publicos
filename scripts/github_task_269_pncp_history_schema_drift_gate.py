#!/usr/bin/env python3
from robo_dados_publicos.research.task269_pncp_history_schema_drift import validate
def main():
 r=validate();assert r["event_count"]==3 and r["observed_key_count"]==16;print(r["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
