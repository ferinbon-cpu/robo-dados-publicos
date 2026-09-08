from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.productization.natural_language_router import (  # noqa: E402
    Task207RouteStop,
    route_and_render,
    route_natural_language,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Roteia uma pergunta em português para as 38 perguntas canônicas do Observatório "
            "e, quando o gate é claro, renderiza a resposta auditável offline."
        )
    )
    parser.add_argument("--ask", required=True, help="Pergunta em linguagem comum.")
    parser.add_argument(
        "--route-only",
        action="store_true",
        help="Mostra somente o resultado de roteamento em JSON; não renderiza a resposta.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        route = route_natural_language(args.ask)
        if args.route_only:
            sys.stdout.write(json.dumps(route, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            return 0 if route["state"] == "ROUTED" else 2

        if route["state"] != "ROUTED":
            print(
                json.dumps(
                    {
                        "state": route["state"],
                        "input_text": route["input_text"],
                        "top_score": route["top_score"],
                        "second_score": route["second_score"],
                        "margin": route["margin"],
                        "candidates": route["candidates"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 2

        result = route_and_render(args.ask)
    except Task207RouteStop as exc:
        print(f"STOP_TASK207:{exc}", file=sys.stderr)
        return 2

    route = result["route"]
    sys.stdout.write(
        f"<!-- route_state={route['state']} route_mode={route['route_mode']} "
        f"question_ids={','.join(route['selected_question_ids'])} "
        f"confidence={route['confidence']} route_sha256={route['route_result_sha256']} -->\n\n"
    )
    for index, answer in enumerate(result["answers"]):
        if index:
            sys.stdout.write("\n\n---\n\n")
        sys.stdout.write(answer["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
