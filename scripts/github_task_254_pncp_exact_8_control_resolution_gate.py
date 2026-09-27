#!/usr/bin/env python3
import json
from pathlib import Path

from robo_dados_publicos.research.task254_pncp_exact_8_control_resolution import (
    ROOT,
    build_url,
    load_config,
    validate_task253_inputs,
)


def main() -> int:
    cfg = load_config()
    validate_task253_inputs(cfg)
    evidence_path = ROOT / "docs/evidence/TASK_254_PNCP_EXACT_8_CONTROL_RESOLUTION_CARRIER_0.8.0.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["schema"] == "TASK254_PNCP_EXACT_8_CONTROL_RESOLUTION_CARRIER_V1"
    assert evidence["status"] == "READY_INERT_EXACT_8_PNCP_DETAIL_CARRIER_LIVE_NOT_AUTHORIZED"
    assert evidence["base_main_sha"] == cfg["base_main_sha"]
    assert evidence["next_gate"] == cfg["next_gate"]
    assert evidence["request_contract"]["detail_gets_max"] == 8
    assert evidence["request_contract"]["total_remote_gets_max"] == 8
    assert evidence["effects"]["live_pncp_gets_authorized_by_this_evidence"] is False
    assert evidence["effects"]["source_network_before_new_owner_authorization"] is False
    expected = [
        {"control": target["control"], "url": build_url(cfg, target)}
        for target in cfg["targets"]
    ]
    assert evidence["exact_targets"] == expected
    print("PASS_TASK254_PNCP_EXACT_8_CONTROL_RESOLUTION_CARRIER_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
