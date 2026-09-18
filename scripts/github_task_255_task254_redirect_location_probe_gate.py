#!/usr/bin/env python3
from robo_dados_publicos.research.task255_task254_redirect_location_probe import load_config, load_evidence

def main() -> int:
    cfg=load_config()
    ev=load_evidence()
    assert cfg["probe"]["max_remote_get_count"] == 1
    assert cfg["probe"]["follow_redirects"] is False
    assert ev["task254"]["source_get_count"] == 1
    assert ev["task254"]["stop_code"] == "TASK254_REDIRECT_STATUS_OBSERVED"
    assert len(ev["untouched_targets"]) == 7
    print("PASS_TASK255_TASK254_REDIRECT_LOCATION_PROBE_GATE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
