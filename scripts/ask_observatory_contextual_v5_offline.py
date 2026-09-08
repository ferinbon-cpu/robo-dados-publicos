from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.productization.custody_ledger_projection_execution import (  # noqa: E402
    Task214ExecutionStop,
    execute_contextual_query_v5,
    load_contract,
    render_contextual_answer_v5,
    validate_contract,
)


TASK206 = ROOT / "config/task206_offline_answer_cli_qa.v1.json"


def _runtime_values() -> tuple[str, str]:
    obj = json.loads(TASK206.read_text(encoding="utf-8"))
    return str(obj["default_generated_at"]), str(obj["default_software_version"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Executa a camada contextual V5 offline, incluindo quatro receitas "
            "contabeis/fiscais derivadas de projeções bounded reidratadas de custodia."
        )
    )
    parser.add_argument("--ask", help="Pergunta em português.")
    parser.add_argument(
        "--task214-status",
        action="store_true",
        help="Imprime contrato/validação e os conjuntos promovido/bloqueado.",
    )
    parser.add_argument(
        "--reference-date",
        help="Data ISO YYYY-MM-DD para expressões relativas.",
    )
    parser.add_argument(
        "--school-code",
        help="Código INEP explícito para referência pessoal à escola.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o envelope JSON em vez do Markdown.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.task214_status:
        if args.ask:
            print("STOP_TASK214:ASK_AND_STATUS_ARE_MUTUALLY_EXCLUSIVE", file=sys.stderr)
            return 2
        contract = load_contract()
        payload = {
            "validation": validate_contract(),
            "promoted_questions": contract["promoted_questions"],
            "semantic_blockers": contract["semantic_blockers"],
            "mode": contract["mode"],
        }
        sys.stdout.write(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        return 0

    if not args.ask:
        print("STOP_TASK214:ASK_REQUIRED", file=sys.stderr)
        return 2

    generated_at, software_version = _runtime_values()
    try:
        answer = execute_contextual_query_v5(
            args.ask,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=args.reference_date,
            context_school_code=args.school_code,
        )
        if args.json:
            sys.stdout.write(
                json.dumps(answer, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            )
        else:
            sys.stdout.write(render_contextual_answer_v5(answer)["markdown"])
    except Task214ExecutionStop as exc:
        print(f"STOP_TASK214:{exc}", file=sys.stderr)
        return 2

    return 0 if answer["state"] in {
        "ANSWERED_CONTEXTUALLY",
        "EXPLICIT_CONTEXT_GAP",
        "LEGACY_UNCONTEXTUALIZED_PASSTHROUGH",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
