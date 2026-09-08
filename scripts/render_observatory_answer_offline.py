from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.analytics.current_observatory_answerability import (  # noqa: E402
    current_answerability_config,
)
from robo_dados_publicos.analytics.current_observatory_bundle import (  # noqa: E402
    build_current_products,
)
from robo_dados_publicos.productization.human_answer_renderer import (  # noqa: E402
    Task205AnswerStop,
    build_answer_card,
    build_human_answer_bundle,
    render_answer_card_markdown,
)


CONTRACT_PATH = ROOT / "config/task206_offline_answer_cli_qa.v1.json"


class Task206CliStop(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task206CliStop(code)


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(data.get("schema") == "TASK206_OFFLINE_ANSWER_CLI_QA_V1", "TASK206_SCHEMA")
    _require(data.get("issue") == 656, "TASK206_ISSUE")
    _require(
        data.get("base_main_sha") == "5256b47df47bb22c43be771eed2ef8d6cb2ffd66",
        "TASK206_BASE",
    )
    _require(
        data.get("mode") == "T0_OFFLINE_STDOUT_OBSERVATORY_ANSWER_CLI_AND_QA",
        "TASK206_MODE",
    )
    _require(all(v is False for v in data["remote_effects"].values()), "TASK206_REMOTE")
    return data


def canonical_questions() -> list[dict[str, str]]:
    config = current_answerability_config()
    rows = [
        {
            "question_id": str(row["id"]),
            "question": str(row["text"]),
            "domain_id": str(row["domain_id"]),
        }
        for row in config["questions"]
    ]
    rows.sort(key=lambda x: x["question_id"])
    _require(len(rows) == 38, "TASK206_QUESTION_COUNT")
    _require(len({x["question_id"] for x in rows}) == 38, "TASK206_QUESTION_DUPLICATE")
    return rows


def _runtime_values() -> tuple[str, str]:
    contract = load_contract()
    generated_at = str(contract["default_generated_at"])
    software_version = str(contract["default_software_version"])
    _require(generated_at != "", "TASK206_GENERATED_AT")
    _require(software_version != "", "TASK206_SOFTWARE_VERSION")
    return generated_at, software_version


def build_single_answer(question_id: str) -> dict[str, Any]:
    allowed = {row["question_id"] for row in canonical_questions()}
    _require(question_id in allowed, "TASK206_UNKNOWN_QUESTION")
    generated_at, software_version = _runtime_values()
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    card = build_answer_card(question_id, products)
    return render_answer_card_markdown(card)


def build_all_answers() -> dict[str, Any]:
    generated_at, software_version = _runtime_values()
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    bundle = build_human_answer_bundle(products)
    renders = sorted(bundle["renders"], key=lambda x: x["question_id"])
    _require(len(renders) == 38, "TASK206_ALL_RENDER_COUNT")
    markdown = "\n\n---\n\n".join(row["markdown"].rstrip() for row in renders).rstrip() + "\n"
    return {
        "schema": "TASK206_ALL_ANSWERS_STDOUT_V1",
        "question_count": 38,
        "bundle_sha256": bundle["bundle_sha256"],
        "markdown": markdown,
        "markdown_sha256": __import__("hashlib").sha256(markdown.encode("utf-8")).hexdigest(),
        "llm_used": False,
        "remote_effects_performed": False,
    }


def render_question_list() -> str:
    lines = ["QUESTION_ID\tDOMAIN_ID\tQUESTION"]
    for row in canonical_questions():
        lines.append(f"{row['question_id']}\t{row['domain_id']}\t{row['question']}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Renderiza respostas auditáveis do Observatório inteiramente offline."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--question-id",
        help="ID canônico de uma das 38 perguntas, por exemplo ACC_Q1.",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Renderiza as 38 respostas em ordem canônica de ID.",
    )
    group.add_argument(
        "--list-questions",
        action="store_true",
        help="Lista os 38 IDs, domínios e textos sem renderizar respostas.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.list_questions:
            sys.stdout.write(render_question_list())
            return 0
        if args.all:
            sys.stdout.write(build_all_answers()["markdown"])
            return 0
        rendered = build_single_answer(str(args.question_id))
        sys.stdout.write(rendered["markdown"])
        return 0
    except (Task206CliStop, Task205AnswerStop) as exc:
        print(f"STOP_TASK206:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
