#!/usr/bin/env python3
"""Build the 0.7.0 minimal product bundle locally.

This command does not access Google Drive and does not publish anything. The
resulting table.csv is the future import source for a Google Sheet in 08_OUTPUTS.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.product import build_product_report, write_product_bundle


def _value(item: dict, lower: str, upper: str) -> str:
    value = item.get(lower, item.get(upper, ""))
    return "" if value is None else str(value)


def _answers(payload) -> list[AnswerContract]:
    items = payload.get("answers", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("ANSWERS_LIST_REQUIRED")
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("ANSWER_MAPPING_REQUIRED")
        sources = item.get("fontes", item.get("FONTES", []))
        if isinstance(sources, str):
            sources = [sources]
        if not isinstance(sources, list):
            raise ValueError("FONTES_LIST_OR_STRING_REQUIRED")
        out.append(
            AnswerContract(
                status=_value(item, "status", "status"),
                dado=_value(item, "dado", "DADO"),
                calculo=_value(item, "calculo", "CÁLCULO"),
                correspondencia=_value(item, "correspondencia", "CORRESPONDÊNCIA"),
                interpretacao=_value(item, "interpretacao", "INTERPRETAÇÃO"),
                cautela=_value(item, "cautela", "CAUTELA"),
                fontes=tuple(str(x) for x in sources),
            )
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON array or object with an answers array")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--generated-at")
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    generated_at = args.generated_at or datetime.now(timezone.utc).isoformat()
    report = build_product_report(
        _answers(payload),
        report_id=args.report_id,
        title=args.title,
        scope=args.scope,
        generated_at=generated_at,
        limitations=args.limitation,
        notes=args.notes,
    )
    manifest = write_product_bundle(report, args.output_dir)
    print(
        json.dumps(
            {
                "status": "PASS_PRODUCT_BUNDLE",
                "report_status": report["report_card"]["status"],
                "rows": report["report_card"]["row_count"],
                "output_dir": str(args.output_dir),
                "files": len(manifest["files"]) + 1,
                "publication_status": manifest["publication_status"],
                "drive_target": manifest["drive_target"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
