from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.productization.mixed_context_planner import (  # noqa: E402
    Task212PlannerStop,
    build_remaining_question_planning_matrix,
    plan_contextual_query,
)


TASK206 = ROOT / "config/task206_offline_answer_cli_qa.v1.json"


def _runtime_values() -> tuple[str, str]:
    obj = json.loads(TASK206.read_text(encoding="utf-8"))
    return str(obj["default_generated_at"]), str(obj["default_software_version"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Planeja deterministicamente receitas contextuais ainda não executáveis, "
            "sem calcular resposta numérica."
        )
    )
    parser.add_argument("--ask", help="Pergunta em português.")
    parser.add_argument(
        "--remaining-matrix",
        action="store_true",
        help="Imprime a matriz baseline das 18 perguntas restantes.",
    )
    parser.add_argument(
        "--reference-date",
        help="Data ISO YYYY-MM-DD para expressões relativas.",
    )
    parser.add_argument(
        "--school-code",
        help="Código INEP explícito para referência pessoal à escola.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at, software_version = _runtime_values()

    if args.remaining_matrix:
        if args.ask:
            print("STOP_TASK212:ASK_AND_MATRIX_ARE_MUTUALLY_EXCLUSIVE", file=sys.stderr)
            return 2
        try:
            payload = build_remaining_question_planning_matrix(
                generated_at=generated_at,
                software_version=software_version,
            )
        except Task212PlannerStop as exc:
            print(f"STOP_TASK212:{exc}", file=sys.stderr)
            return 2
        sys.stdout.write(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        return 0

    if not args.ask:
        print("STOP_TASK212:ASK_REQUIRED", file=sys.stderr)
        return 2

    try:
        payload = plan_contextual_query(
            args.ask,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=args.reference_date,
            context_school_code=args.school_code,
        )
    except Task212PlannerStop as exc:
        print(f"STOP_TASK212:{exc}", file=sys.stderr)
        return 2

    sys.stdout.write(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return 0 if payload["planning_state"] not in {"ROUTE_STOP_PROPAGATED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
