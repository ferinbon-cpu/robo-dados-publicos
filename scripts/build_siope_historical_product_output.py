#!/usr/bin/env python3
"""Build the M8 SIOPE historical product bundle from nine local Gold payloads.

The command is offline: it does not call FNDE/SIOPE, Google Drive, or any other
network service. Publication remains a separate gated action.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.product import build_product_report, write_product_bundle
from robo_dados_publicos.product.siope_historical import build_siope_historical_answers


def _load(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"GOLD_OBJECT_REQUIRED: {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", action="append", required=True, help="Local Gold JSON; repeat for 2016–2024")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--generated-at", required=True, help="Offset-aware ISO-8601 timestamp")
    parser.add_argument("--report-id", default="SIOPE_LIMEIRA_HISTORICAL_2016_2024")
    parser.add_argument("--title", default="SIOPE Limeira — série histórica 2016–2024")
    args = parser.parse_args()

    answers = build_siope_historical_answers(_load(path) for path in args.gold)
    report = build_product_report(
        answers,
        report_id=args.report_id,
        title=args.title,
        scope="FNDE/SIOPE Dados_Gerais_Siope — Limeira/SP — Gold aritmético validado — 2016–2024",
        generated_at=args.generated_at,
        limitations=(
            "Não constitui auditoria fiscal nem conclusão de cumprimento de MDE/Fundeb.",
            "Valores por habitante não são deflacionados neste adaptador.",
            "A apresentação não substitui os Gold e suas proveniências.",
        ),
        notes="2016 usa período anual P1; 2017–2024 usam P6.",
        software_version="0.8.0",
    )
    manifest = write_product_bundle(report, args.output_dir)
    print(
        json.dumps(
            {
                "status": "PASS_M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_LOCAL",
                "year_count": 9,
                "metric_rows": len(answers),
                "report_status": report["report_card"]["status"],
                "publication_status": manifest["publication_status"],
                "drive_target": manifest["drive_target"],
                "source_network_called": False,
                "drive_network_called": False,
                "mutation_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
