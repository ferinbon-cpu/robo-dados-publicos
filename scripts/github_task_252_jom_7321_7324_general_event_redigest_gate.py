#!/usr/bin/env python3
from robo_dados_publicos.research.task252_jom_7321_7324_general_event_redigest import (
    load_canonical_evidence,
    load_config,
    validate_canonical_evidence,
    validate_config,
)


def main() -> int:
    config = load_config()
    evidence = load_canonical_evidence()
    evidence_result = validate_canonical_evidence(evidence)
    config_result = validate_config(config, evidence)
    assert evidence_result["status"] == "PASS_TASK252_CANONICAL_EVIDENCE"
    assert config_result == {"status": "PASS_TASK252_CONFIG", "targets": 4}
    print("PASS_TASK252_JOM_7321_7324_GENERAL_EVENT_REDIGEST_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
