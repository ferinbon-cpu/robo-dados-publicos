#!/usr/bin/env python3
from robo_dados_publicos.research.task258_task257_json301_body import *
def main():
 c=load_config();e=load_evidence();p=c["probe"];cmd=command(p["requested_url"],"/tmp/x",connect_timeout=15,max_time=75,max_body_bytes=4096)
 assert "--location" not in cmd and cmd[cmd.index("--retry")+1]=="0" and cmd[cmd.index("--max-filesize")+1]=="4096"
 assert project({"message":"x"})=={"message":"x"} and e["task256_context"]["size_download"]==273
 print("PASS_TASK258_TASK257_JSON301_BODY_GATE");return 0
if __name__=="__main__":raise SystemExit(main())
