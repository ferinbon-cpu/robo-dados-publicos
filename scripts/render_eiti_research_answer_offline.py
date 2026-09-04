from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.answer_renderer import (  # noqa: E402
    ResearchAnswerRenderStop,
    render_research_answer_markdown,
)
from robo_dados_publicos.research.query import (  # noqa: E402
    QUERY_TYPES,
    ResearchQueryStop,
    execute_research_query,
)


EITI_PATH = ROOT / "config/eiti_limeira_research_crosswalk.v1.json"
HISTORICAL_PATH = ROOT / "config/eiti_historical_planning_crosswalk.v1.json"
EXPECTED_INPUT_SHA256 = {
    EITI_PATH.name: "34bed580acb84abfe3e8894ed620c87b9918ef52c187716d5d02fa330db26953",
    HISTORICAL_PATH.name: "b34452daf28600d9663a20dbae4e6c091ec65a03ac328313151f1788c45b4d39",
}


class EitiResearchAnswerCliStop(RuntimeError):
    """Fail-closed offline CLI assembly error."""


def _load_json(path: Path, *, expected_sha256: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise EitiResearchAnswerCliStop(f"TASK101_INPUT_READ:{path.name}") from exc

    observed_sha256 = sha256(raw).hexdigest()
    if observed_sha256 != expected_sha256:
        raise EitiResearchAnswerCliStop(f"TASK101_INPUT_SHA256_MISMATCH:{path.name}")

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EitiResearchAnswerCliStop(f"TASK101_INPUT_JSON:{path.name}") from exc
    if not isinstance(data, dict):
        raise EitiResearchAnswerCliStop(f"TASK101_INPUT_OBJECT:{path.name}")
    return data


def build_eiti_research_answer(
    *,
    query_type: str = "POLICY_STATUS_PACKET",
    include_evidence: bool = True,
    include_unknown_gaps: bool = True,
) -> dict[str, Any]:
    if query_type not in QUERY_TYPES:
        raise EitiResearchAnswerCliStop("TASK101_QUERY_TYPE")
    if not isinstance(include_evidence, bool):
        raise EitiResearchAnswerCliStop("TASK101_INCLUDE_EVIDENCE")
    if not isinstance(include_unknown_gaps, bool):
        raise EitiResearchAnswerCliStop("TASK101_INCLUDE_UNKNOWN_GAPS")

    eiti = _load_json(
        EITI_PATH,
        expected_sha256=EXPECTED_INPUT_SHA256[EITI_PATH.name],
    )
    historical = _load_json(
        HISTORICAL_PATH,
        expected_sha256=EXPECTED_INPUT_SHA256[HISTORICAL_PATH.name],
    )

    research_bundle = eiti.get("research_bundle")
    if not isinstance(research_bundle, dict):
        raise EitiResearchAnswerCliStop("TASK101_RESEARCH_BUNDLE")
    matrix = eiti.get("institutionalization_matrix")
    if not isinstance(matrix, dict):
        raise EitiResearchAnswerCliStop("TASK101_INSTITUTIONALIZATION_MATRIX")

    spec = {
        "query_id": f"Q:EITI_CLI_{query_type}",
        "query_type": query_type,
        "subject_id": "POLICY:EITI_LIMEIRA",
        "include_evidence": include_evidence,
        "include_unknown_gaps": include_unknown_gaps,
    }

    packet = execute_research_query(
        research_bundle,
        spec,
        institutionalization_matrix=matrix,
        historical_planning=historical,
    )
    return render_research_answer_markdown(packet)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Renderiza offline uma consulta de pesquisa EITI-Limeira usando somente "
            "evidência já versionada no repositório."
        )
    )
    parser.add_argument(
        "--query-type",
        choices=QUERY_TYPES,
        default="POLICY_STATUS_PACKET",
        help="Tipo determinístico de consulta.",
    )
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="Omite o payload expandido das evidências, preservando seus IDs.",
    )
    parser.add_argument(
        "--no-unknown-gaps",
        action="store_true",
        help="Omite a lista de gaps da matriz quando o query type a suporta.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = build_eiti_research_answer(
            query_type=args.query_type,
            include_evidence=not args.no_evidence,
            include_unknown_gaps=not args.no_unknown_gaps,
        )
    except (EitiResearchAnswerCliStop, ResearchQueryStop, ResearchAnswerRenderStop) as exc:
        print(f"STOP_TASK101:{exc}", file=sys.stderr)
        return 2

    sys.stdout.write(rendered["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
