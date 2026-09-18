#!/usr/bin/env python3
from robo_dados_publicos.research.task256_task255_timeout_curl_diagnostic import (
    build_curl_command,
    load_config,
    load_evidence,
)


def main() -> int:
    cfg = load_config()
    ev = load_evidence()
    diag = cfg["diagnostic"]
    cmd = build_curl_command(
        diag["requested_url"],
        connect_timeout=diag["connect_timeout_seconds"],
        max_time=diag["max_time_seconds"],
    )
    assert diag["max_remote_get_count"] == 1
    assert diag["follow_redirects"] is False
    assert diag["retry"] is False
    assert "--location" not in cmd
    assert cmd.count(diag["requested_url"]) == 1
    assert "--retry" in cmd and cmd[cmd.index("--retry") + 1] == "0"
    assert "--output" in cmd and cmd[cmd.index("--output") + 1] == "/dev/null"
    assert ev["task255"]["source_get_count"] == 1
    assert ev["task255"]["transport_error"] == "URL_ERROR:TimeoutError"
    assert len(ev["untouched_targets"]) == 7
    print("PASS_TASK256_TASK255_TIMEOUT_CURL_DIAGNOSTIC_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
