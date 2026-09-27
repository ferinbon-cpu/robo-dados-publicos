#!/usr/bin/env python3
from robo_dados_publicos.research.task267_pncp_items_8of8_canonization import validate
def main():
    r=validate();assert r["controls"]==8 and r["item_rows"]==40
    print(r["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
