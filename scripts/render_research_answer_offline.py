from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
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


CONFIG_DIR = ROOT / "config"
REGISTRY_PATH = CONFIG_DIR / "research_dataset_registry.v1.json"
QUERY_SPEC_DIR = CONFIG_DIR / "research_queries"
DEFAULT_SPEC = "eiti_limeira_policy_status.v1.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ResearchAnswerCliStop(RuntimeError):
    """Fail-closed generic offline research-answer assembly error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ResearchAnswerCliStop(code)


def _read_json(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ResearchAnswerCliStop(f"TASK102_INPUT_READ:{path.name}") from exc

    if expected_sha256 is not None:
        _require(bool(_SHA256_RE.fullmatch(expected_sha256)), "TASK102_EXPECTED_SHA256")
        observed = sha256(raw).hexdigest()
        _require(observed == expected_sha256, f"TASK102_INPUT_SHA256_MISMATCH:{path.name}")

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchAnswerCliStop(f"TASK102_INPUT_JSON:{path.name}") from exc
    _require(isinstance(data, dict), f"TASK102_INPUT_OBJECT:{path.name}")
    return data


def _bounded_config_path(raw_path: str) -> Path:
    _require(isinstance(raw_path, str) and raw_path.strip() != "", "TASK102_SOURCE_PATH")
    _require("\\" not in raw_path, "TASK102_SOURCE_PATH_BACKSLASH")
    pure = PurePosixPath(raw_path)
    _require(not pure.is_absolute(), "TASK102_SOURCE_PATH_ABSOLUTE")
    _require(".." not in pure.parts, "TASK102_SOURCE_PATH_TRAVERSAL")
    _require(pure.parts and pure.parts[0] == "config", "TASK102_SOURCE_PATH_OUTSIDE_CONFIG")
    candidate = ROOT.joinpath(*pure.parts).resolve()
    config_root = CONFIG_DIR.resolve()
    _require(candidate == config_root or config_root in candidate.parents, "TASK102_SOURCE_PATH_BOUNDARY")
    return candidate


def _validate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    _require(registry.get("schema") == "RESEARCH_DATASET_REGISTRY_V1", "TASK102_REGISTRY_SCHEMA")
    _require(registry.get("version") == 1, "TASK102_REGISTRY_VERSION")
    _require(
        registry.get("query_spec_directory") == "config/research_queries",
        "TASK102_REGISTRY_QUERY_DIR",
    )
    remote = registry.get("remote_effects")
    _require(isinstance(remote, dict) and remote, "TASK102_REGISTRY_REMOTE_EFFECT_OBJECT")
    _require(all(value is False for value in remote.values()), "TASK102_REGISTRY_REMOTE_EFFECT")

    datasets = registry.get("datasets")
    _require(isinstance(datasets, list) and datasets, "TASK102_REGISTRY_DATASETS")
    seen: set[str] = set()
    normalized = []
    for dataset in datasets:
        _require(isinstance(dataset, dict), "TASK102_DATASET_OBJECT")
        dataset_id = str(dataset.get("dataset_id") or "").strip()
        subject_id = str(dataset.get("subject_id") or "").strip()
        _require(dataset_id.startswith("DATASET:"), "TASK102_DATASET_ID")
        _require(dataset_id not in seen, "TASK102_DATASET_DUPLICATE")
        _require(subject_id != "", "TASK102_DATASET_SUBJECT")
        seen.add(dataset_id)

        source = dataset.get("research_source")
        _require(isinstance(source, dict), "TASK102_RESEARCH_SOURCE")
        _bounded_config_path(str(source.get("path") or ""))
        _require(bool(_SHA256_RE.fullmatch(str(source.get("sha256") or ""))), "TASK102_RESEARCH_SOURCE_SHA")
        _require(bool(str(source.get("research_bundle_key") or "").strip()), "TASK102_RESEARCH_BUNDLE_KEY")
        _require(
            bool(str(source.get("institutionalization_matrix_key") or "").strip()),
            "TASK102_MATRIX_KEY",
        )

        historical = dataset.get("historical_source")
        if historical is not None:
            _require(isinstance(historical, dict), "TASK102_HISTORICAL_SOURCE")
            _bounded_config_path(str(historical.get("path") or ""))
            _require(
                bool(_SHA256_RE.fullmatch(str(historical.get("sha256") or ""))),
                "TASK102_HISTORICAL_SOURCE_SHA",
            )

        allowed = dataset.get("allowed_query_types")
        _require(isinstance(allowed, list) and allowed, "TASK102_DATASET_QUERY_TYPES")
        _require(len(allowed) == len(set(allowed)), "TASK102_DATASET_QUERY_TYPE_DUPLICATE")
        _require(all(item in QUERY_TYPES for item in allowed), "TASK102_DATASET_QUERY_TYPE")
        normalized.append(dataset)

    return {**registry, "datasets": normalized}


def _load_registry() -> dict[str, Any]:
    return _validate_registry(_read_json(REGISTRY_PATH))


def _spec_path(spec_name: str) -> Path:
    _require(isinstance(spec_name, str) and spec_name.strip() != "", "TASK102_SPEC_NAME")
    _require("/" not in spec_name and "\\" not in spec_name, "TASK102_SPEC_PATH_FORBIDDEN")
    _require(PurePosixPath(spec_name).name == spec_name, "TASK102_SPEC_BASENAME")
    _require(spec_name.endswith(".json"), "TASK102_SPEC_EXTENSION")
    return QUERY_SPEC_DIR / spec_name


def _load_query_spec(spec_name: str) -> dict[str, Any]:
    spec = _read_json(_spec_path(spec_name))
    _require(spec.get("schema") == "RESEARCH_QUERY_SPEC_V1", "TASK102_SPEC_SCHEMA")
    _require(spec.get("version") == 1, "TASK102_SPEC_VERSION")
    _require(str(spec.get("spec_id") or "").startswith("SPEC:"), "TASK102_SPEC_ID")
    _require(str(spec.get("dataset_id") or "").startswith("DATASET:"), "TASK102_SPEC_DATASET")
    _require(bool(str(spec.get("query_id") or "").strip()), "TASK102_SPEC_QUERY_ID")
    _require(spec.get("query_type") in QUERY_TYPES, "TASK102_SPEC_QUERY_TYPE")
    _require(bool(str(spec.get("subject_id") or "").strip()), "TASK102_SPEC_SUBJECT")
    _require(isinstance(spec.get("include_evidence"), bool), "TASK102_SPEC_INCLUDE_EVIDENCE")
    _require(
        isinstance(spec.get("include_unknown_gaps"), bool),
        "TASK102_SPEC_INCLUDE_UNKNOWN_GAPS",
    )
    _require(spec.get("output_format") == "MARKDOWN", "TASK102_SPEC_OUTPUT_FORMAT")
    _require(spec.get("output_channel") == "STDOUT", "TASK102_SPEC_OUTPUT_CHANNEL")
    forbidden = {"source_path", "source_url", "url", "prompt", "question", "free_form"}
    _require(not forbidden.intersection(spec), "TASK102_SPEC_FORBIDDEN_FIELD")
    return spec


def _dataset_for(registry: dict[str, Any], dataset_id: str) -> dict[str, Any]:
    matches = [item for item in registry["datasets"] if item["dataset_id"] == dataset_id]
    _require(len(matches) == 1, "TASK102_DATASET_NOT_FOUND")
    return matches[0]


def build_research_answer(*, spec_name: str = DEFAULT_SPEC) -> dict[str, Any]:
    registry = _load_registry()
    spec = _load_query_spec(spec_name)
    dataset = _dataset_for(registry, spec["dataset_id"])

    _require(spec["subject_id"] == dataset["subject_id"], "TASK102_SUBJECT_MISMATCH")
    _require(
        spec["query_type"] in dataset["allowed_query_types"],
        "TASK102_QUERY_TYPE_NOT_ALLOWED_FOR_DATASET",
    )

    source_meta = dataset["research_source"]
    source = _read_json(
        _bounded_config_path(source_meta["path"]),
        expected_sha256=source_meta["sha256"],
    )
    bundle = source.get(source_meta["research_bundle_key"])
    matrix = source.get(source_meta["institutionalization_matrix_key"])
    _require(isinstance(bundle, dict), "TASK102_RESEARCH_BUNDLE")
    _require(isinstance(matrix, dict), "TASK102_INSTITUTIONALIZATION_MATRIX")

    historical = None
    historical_meta = dataset.get("historical_source")
    if historical_meta is not None:
        historical = _read_json(
            _bounded_config_path(historical_meta["path"]),
            expected_sha256=historical_meta["sha256"],
        )

    query_spec = {
        "query_id": spec["query_id"],
        "query_type": spec["query_type"],
        "subject_id": spec["subject_id"],
        "include_evidence": spec["include_evidence"],
        "include_unknown_gaps": spec["include_unknown_gaps"],
    }
    if "allowed_claim_statuses" in spec:
        query_spec["allowed_claim_statuses"] = spec["allowed_claim_statuses"]

    packet = execute_research_query(
        bundle,
        query_spec,
        institutionalization_matrix=matrix,
        historical_planning=historical,
    )
    return render_research_answer_markdown(packet)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Renderiza offline uma consulta de pesquisa versionada contra um dataset "
            "registrado e SHA-256-pinado."
        )
    )
    parser.add_argument(
        "--spec",
        default=DEFAULT_SPEC,
        help="Nome de arquivo de uma query spec versionada em config/research_queries.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = build_research_answer(spec_name=args.spec)
    except (ResearchAnswerCliStop, ResearchQueryStop, ResearchAnswerRenderStop) as exc:
        print(f"STOP_TASK102:{exc}", file=sys.stderr)
        return 2

    sys.stdout.write(rendered["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
