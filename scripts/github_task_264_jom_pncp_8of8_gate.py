#!/usr/bin/env python3
from robo_dados_publicos.research.task264_jom_pncp_8of8_canonization import validate
def main():
    r=validate();assert r["count"]==8
    print(r["status"]);return 0
if __name__=="__main__": raise SystemExit(main())
