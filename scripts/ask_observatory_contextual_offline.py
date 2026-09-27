from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.productization.context_aware_execution import (  # noqa: E402
    Task209ExecutionStop,
    execute_contextual_query,
    render_contextual_answer_markdown,
)


TASK206 = ROOT / "config/task206_offline_answer_cli_qa.v1.json"


def _runtime_values() -> tuple[str, str]:
    obj = json.loads(TASK206.read_text(encoding="utf-8"))
    return str(obj["default_generated_at"]), str(obj["default_software_version"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Executa uma pergunta contextual do Observatório em modo offline e fail-closed, "
            "aplicando escola, período, política/serviço e granularidade quando suportados."
        )
    )
    parser.add_argument("--ask", required=True, help="Pergunta em português.")
    parser.add_argument(
        "--reference-date",
        help="Data ISO YYYY-MM-DD para expressões relativas como 'deste ano'.",
    )
    parser.add_argument(
        "--school-code",
        help="Código INEP explícito para referências como 'minha escola'.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o envelope JSON em vez do Markdown.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_at, software_version = _runtime_values()
    try:
        answer = execute_contextual_query(
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
            rendered = render_contextual_answer_markdown(answer)
            sys.stdout.write(rendered["markdown"])
    except Task209ExecutionStop as exc:
        print(f"STOP_TASK209:{exc}", file=sys.stderr)
        return 2

    return 0 if answer["state"] in {
        "ANSWERED_CONTEXTUALLY",
        "EXPLICIT_CONTEXT_GAP",
        "LEGACY_UNCONTEXTUALIZED_PASSTHROUGH",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
