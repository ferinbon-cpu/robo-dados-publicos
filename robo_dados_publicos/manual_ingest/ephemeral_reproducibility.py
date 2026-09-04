from __future__ import annotations

from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

from robo_dados_publicos.release import SOFTWARE_VERSION


DIGEST_PASS = "PASS_EPHEMERAL_RUNTIME_DIGEST_NOT_PERSISTED"
OBSERVATION_SCHEMA = "EPHEMERAL_DIGEST_OBSERVATION_V1"
REPORT_SCHEMA = "EPHEMERAL_DIGEST_REPRODUCIBILITY_REPORT_V1"


class ReproducibilityStop(RuntimeError):
    """Fail-closed structural error; historical drift itself is not an exception."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ReproducibilityStop(code)


def canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def runtime_fingerprint() -> dict[str, Any]:
    try:
        pypdf_version = package_version("pypdf")
    except PackageNotFoundError:
        pypdf_version = "NOT_INSTALLED"

    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "pypdf": pypdf_version,
        "project_version": SOFTWARE_VERSION,
        "runner_os": os.environ.get("RUNNER_OS"),
        "runner_image_os": os.environ.get("ImageOS"),
        "runner_image_version": os.environ.get("ImageVersion"),
    }


def _validate_candidate_file(record: dict[str, Any], *, source_key: str) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK092_CANDIDATE_RECORD")
    name = str(record.get("name") or "")
    digest = str(record.get("sha256") or "")
    size = record.get("bytes")
    _require(name != "", f"TASK092_CANDIDATE_NAME_{source_key}")
    _require(isinstance(size, int) and size >= 0, f"TASK092_CANDIDATE_BYTES_{source_key}")
    _require(
        len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest),
        f"TASK092_CANDIDATE_SHA256_{source_key}",
    )
    return {"name": name, "bytes": size, "sha256": digest}


def capture_digest_observation(
    digest_result: dict[str, Any],
    *,
    fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _require(isinstance(digest_result, dict), "TASK092_DIGEST_RESULT_OBJECT")
    _require(digest_result.get("status") == DIGEST_PASS, "TASK092_DIGEST_NOT_PASS")
    _require(digest_result.get("persistence_authorized") is False, "TASK092_PERSISTENCE_AUTHORIZED")

    items = digest_result.get("items")
    _require(isinstance(items, list) and items, "TASK092_ITEMS")

    observed_items: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for item in items:
        _require(isinstance(item, dict), "TASK092_ITEM_OBJECT")
        source_key = str(item.get("source_key") or "")
        _require(source_key != "", "TASK092_SOURCE_KEY")
        _require(source_key not in seen_keys, "TASK092_DUPLICATE_SOURCE_KEY")
        seen_keys.add(source_key)

        source_sha = str(item.get("source_sha256") or "")
        _require(
            len(source_sha) == 64 and all(ch in "0123456789abcdef" for ch in source_sha),
            f"TASK092_SOURCE_SHA256_{source_key}",
        )
        source_bytes = item.get("source_bytes")
        _require(
            isinstance(source_bytes, int) and source_bytes > 0,
            f"TASK092_SOURCE_BYTES_{source_key}",
        )
        counts: dict[str, int] = {}
        for field in ("silver_rows", "gold_rows", "rag_rows"):
            value = item.get(field)
            _require(isinstance(value, int) and value >= 0, f"TASK092_COUNT_{field}_{source_key}")
            counts[field] = value

        candidate_files = item.get("candidate_files")
        _require(
            isinstance(candidate_files, list) and candidate_files,
            f"TASK092_CANDIDATE_FILES_{source_key}",
        )
        candidates = [
            _validate_candidate_file(record, source_key=source_key)
            for record in candidate_files
        ]

        observed_items.append(
            {
                "source_key": source_key,
                "family": str(item.get("family") or ""),
                "source_sha256": source_sha,
                "source_bytes": source_bytes,
                "counts": counts,
                "candidate_files": candidates,
            }
        )

    fp = dict(fingerprint if fingerprint is not None else runtime_fingerprint())
    _require(fp, "TASK092_RUNTIME_FINGERPRINT")

    core = {
        "schema": OBSERVATION_SCHEMA,
        "digest_status": DIGEST_PASS,
        "digest_result_sha256": str(digest_result.get("result_sha256") or ""),
        "processor_git_blob_sha": str(digest_result.get("processor_git_blob_sha") or ""),
        "candidate_set_sha256": str(digest_result.get("candidate_set_sha256") or ""),
        "input_count": digest_result.get("input_count"),
        "candidate_file_count": digest_result.get("candidate_file_count"),
        "items": observed_items,
        "runtime_fingerprint": fp,
        "persistence_authorized": False,
    }
    return {
        **core,
        "observation_sha256": sha256(canonical_bytes(core)).hexdigest(),
    }


def _expected_item_map(expectation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    _require(isinstance(expectation, dict), "TASK092_EXPECTATION_OBJECT")
    _require(
        expectation.get("schema") == "EPHEMERAL_DIGEST_HISTORICAL_EXPECTATION_V1",
        "TASK092_EXPECTATION_SCHEMA",
    )
    items = expectation.get("items")
    _require(isinstance(items, list) and items, "TASK092_EXPECTATION_ITEMS")
    mapping: dict[str, dict[str, Any]] = {}
    for item in items:
        _require(isinstance(item, dict), "TASK092_EXPECTATION_ITEM_OBJECT")
        source_key = str(item.get("source_key") or "")
        _require(source_key and source_key not in mapping, "TASK092_EXPECTATION_SOURCE_KEY")
        expected_counts = item.get("counts")
        _require(isinstance(expected_counts, dict), f"TASK092_EXPECTED_COUNTS_{source_key}")
        for field in ("silver_rows", "gold_rows", "rag_rows"):
            _require(
                isinstance(expected_counts.get(field), int) and expected_counts[field] >= 0,
                f"TASK092_EXPECTED_{field}_{source_key}",
            )
        mapping[source_key] = item
    return mapping


def compare_historical_observation(
    observation: dict[str, Any],
    expectation: dict[str, Any],
) -> dict[str, Any]:
    _require(observation.get("schema") == OBSERVATION_SCHEMA, "TASK092_OBSERVATION_SCHEMA")
    _require(observation.get("digest_status") == DIGEST_PASS, "TASK092_OBSERVATION_DIGEST_STATUS")
    expected = _expected_item_map(expectation)

    observed_by_key = {item["source_key"]: item for item in observation["items"]}
    mismatches: list[dict[str, Any]] = []

    for source_key in sorted(set(observed_by_key) | set(expected)):
        observed = observed_by_key.get(source_key)
        wanted = expected.get(source_key)
        if observed is None:
            mismatches.append(
                {"source_key": source_key, "field": "source_presence", "expected": True, "observed": False}
            )
            continue
        if wanted is None:
            mismatches.append(
                {"source_key": source_key, "field": "source_presence", "expected": False, "observed": True}
            )
            continue

        for field in ("silver_rows", "gold_rows", "rag_rows"):
            observed_value = observed["counts"][field]
            expected_value = wanted["counts"][field]
            if observed_value != expected_value:
                mismatches.append(
                    {
                        "source_key": source_key,
                        "field": field,
                        "expected": expected_value,
                        "observed": observed_value,
                    }
                )

        expected_source_sha = wanted.get("source_sha256")
        if expected_source_sha is not None and observed["source_sha256"] != expected_source_sha:
            mismatches.append(
                {
                    "source_key": source_key,
                    "field": "source_sha256",
                    "expected": expected_source_sha,
                    "observed": observed["source_sha256"],
                }
            )

        expected_candidates = wanted.get("candidate_sha256_by_name")
        if expected_candidates is not None:
            _require(
                isinstance(expected_candidates, dict),
                f"TASK092_EXPECTED_CANDIDATE_MAP_{source_key}",
            )
            observed_candidates = {
                record["name"]: record["sha256"] for record in observed["candidate_files"]
            }
            if observed_candidates != expected_candidates:
                mismatches.append(
                    {
                        "source_key": source_key,
                        "field": "candidate_sha256_by_name",
                        "expected": expected_candidates,
                        "observed": observed_candidates,
                    }
                )

    reproduction_status = (
        "HISTORICAL_REPRODUCTION_MATCH"
        if not mismatches
        else "HISTORICAL_REPRODUCTION_DRIFT"
    )
    core = {
        "schema": REPORT_SCHEMA,
        "digest_status": observation["digest_status"],
        "observation_sha256": observation["observation_sha256"],
        "historical_reproduction_status": reproduction_status,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "digest_pass_preserved_on_historical_drift": True,
    }
    return {
        **core,
        "report_sha256": sha256(canonical_bytes(core)).hexdigest(),
    }


def _write_create_only_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise ReproducibilityStop("TASK092_CREATE_ONLY_PATH_EXISTS") from exc


def persist_observation_then_compare(
    digest_result: dict[str, Any],
    expectation: dict[str, Any],
    *,
    observation_path: str | Path,
    report_path: str | Path,
    fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist local observation before comparison so drift cannot erase observed facts."""
    observation = capture_digest_observation(digest_result, fingerprint=fingerprint)
    observation_path = Path(observation_path)
    report_path = Path(report_path)
    _require(observation_path != report_path, "TASK092_OUTPUT_PATH_COLLISION")

    _write_create_only_json(observation_path, observation)
    report = compare_historical_observation(observation, expectation)
    _write_create_only_json(report_path, report)

    return {
        "status": "PASS_TASK092_OBSERVATION_PERSISTED_BEFORE_HISTORICAL_COMPARISON",
        "digest_status": observation["digest_status"],
        "historical_reproduction_status": report["historical_reproduction_status"],
        "observation_sha256": observation["observation_sha256"],
        "report_sha256": report["report_sha256"],
    }
