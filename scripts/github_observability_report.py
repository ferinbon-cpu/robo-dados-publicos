#!/usr/bin/env python3
"""Render sanitized operator-facing observability artifacts from gate evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.observability.report import (
    load_source_card_config,
    render_markdown,
    write_report_bundle,
)


def _resolve(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-card-config")
    parser.add_argument("--github-summary", action="store_true")
    args = parser.parse_args()

    input_path = _resolve(args.input)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    source_card = load_source_card_config(_resolve(args.source_card_config)) if args.source_card_config else None
    report = write_report_bundle(payload, _resolve(args.output_dir), source_card=source_card)

    if args.github_summary:
        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as handle:
                handle.write(render_markdown(report))

    safe = report["overall_health"] != "STOPPED" and report["privacy"]["status"] == "PASS"
    print(
        json.dumps(
            {
                "status": "PASS_OBSERVABILITY_REPORT" if safe else "STOP_OBSERVABILITY_REPORT",
                "overall_health": report["overall_health"],
                "privacy_status": report["privacy"]["status"],
                "output_dir": args.output_dir,
                "secret_values_exposed": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if safe else 16


if __name__ == "__main__":
    raise SystemExit(main())
