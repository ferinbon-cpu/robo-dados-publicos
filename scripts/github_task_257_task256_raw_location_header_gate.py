#!/usr/bin/env python3
from robo_dados_publicos.research.task257_task256_raw_location_header import build_curl_command,load_config,load_evidence,parse_location_headers
def main():
    c=load_config(); e=load_evidence(); p=c["probe"]
    cmd=build_curl_command(p["requested_url"],"/tmp/x.headers",connect_timeout=15,max_time=75)
    assert "--location" not in cmd
    assert cmd[cmd.index("--retry")+1]=="0"
    assert cmd[cmd.index("--output")+1]=="/dev/null"
    assert parse_location_headers("Location: /x\nlocation: https://x/y\n")==["/x","https://x/y"]
    assert e["task256"]["source_get_count"]==1
    print("PASS_TASK257_TASK256_RAW_LOCATION_HEADER_GATE")
    return 0
if __name__=="__main__": raise SystemExit(main())
