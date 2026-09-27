#!/usr/bin/env python3
from robo_dados_publicos.research.task253_jom_pncp_explicit_control_canonization import validate_committed_outputs


def main() -> int:
    result = validate_committed_outputs()
    assert result["status"] == "PASS_TASK253_JOM_PNCP_EXPLICIT_CONTROL_CANONIZATION"
    assert result["strong_anchor_rows"] == 20
    assert result["strong_unique_identities"] == 18
    assert result["explicit_pncp_controls"] == 8
    assert result["new_strong_identities_vs_prior_99"] == 14
    assert result["projected_103_unique_identities"] == 317
    print("PASS_TASK253_JOM_PNCP_EXPLICIT_CONTROL_CANONIZATION_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
