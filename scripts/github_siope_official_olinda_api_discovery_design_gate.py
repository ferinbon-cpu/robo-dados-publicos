from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_discovery_design import (  # noqa: E402
    load_json,
    validate_discovery_design,
)

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_discovery_design.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    base_source = load_json(ROOT / config["base_source_config_path"])
    blocked_html = load_json(ROOT / config["blocked_html_track_config_path"])
    research = load_json(ROOT / config["public_research_evidence_path"])
    return validate_discovery_design(config, base_source, blocked_html, research)


def main() -> int:
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
