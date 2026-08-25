from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_public_runtime_route_contract_review import run_review


CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_route_contract_review.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_review(CONFIG, args.evidence)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
