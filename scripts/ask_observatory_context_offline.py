from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.productization.contextual_slot_binder import (  # noqa: E402
    Task208ContextStop,
    bind_and_render,
    bind_context,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extrai rota, período, escola, política/serviço e granularidade "
            "de uma pergunta do Observatório sem transformar texto em verdade de dados."
        )
    )
    parser.add_argument("--ask", required=True, help="Pergunta em português.")
    parser.add_argument(
        "--reference-date",
        help="Data ISO YYYY-MM-DD exigida para expressões relativas como 'deste ano'.",
    )
    parser.add_argument(
        "--school-code",
        help="Código INEP de contexto para referências pessoais como 'minha escola'.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help=(
            "Tenta renderizar apenas quando nenhum filtro contextual incompatível "
            "precisaria ser descartado."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.render:
            result = bind_and_render(
                args.ask,
                reference_date=args.reference_date,
                context_school_code=args.school_code,
            )
        else:
            result = bind_context(
                args.ask,
                reference_date=args.reference_date,
                context_school_code=args.school_code,
            )
    except Task208ContextStop as exc:
        print(f"STOP_TASK208:{exc}", file=sys.stderr)
        return 2

    sys.stdout.write(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    if args.render:
        return 0
    return 0 if result["state"] == "CONTEXT_BOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())
