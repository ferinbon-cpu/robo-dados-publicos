from __future__ import annotations

import ast
from hashlib import sha1, sha256
import inspect
import json
import os
from pathlib import Path
import re
import shutil
import stat
from typing import Any

from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.manual_ingest.source_family_maturity import (
    execution_maturity,
    validate_maturity_registry,
)


class EphemeralDigestStop(RuntimeError):
    """Fail-closed stop raised by the local-only digest executor."""


REMOTE_EFFECT_KEYS = (
    "source_network_calls",
    "drive_network_calls",
    "bronze_writes",
    "silver_writes",
    "gold_writes",
    "rag_writes",
    "state_registry_writes",
    "queue_writes",
    "serving_writes",
    "publication_writes",
    "overwrite",
    "delete",
    "move",
    "schedule",
    "recurrence",
)


def _stop(code: str, detail: str | None = None) -> None:
    suffix = f":{detail}" if detail else ""
    raise EphemeralDigestStop(f"STOP_EPHEMERAL_DIGEST_{code}{suffix}")


def canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _safe_relative_path(value: object, *, code: str) -> Path:
    text = str(value or "").strip()
    if not text:
        _stop(code, "MISSING")
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        _stop(code, text)
    return path


def _beneath(root: Path, candidate: Path, *, code: str) -> Path:
    root_resolved = root.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        _stop(code, str(candidate))
    return resolved


def _read_regular_file_beneath(
    root: Path, relative: Path, *, max_bytes: int
) -> tuple[Path, int]:
    candidate = root / relative
    try:
        st = os.lstat(candidate)
    except FileNotFoundError:
        _stop("INPUT_MISSING", str(relative))
    if stat.S_ISLNK(st.st_mode):
        _stop("INPUT_SYMLINK", str(relative))
    if not stat.S_ISREG(st.st_mode):
        _stop("INPUT_NOT_REGULAR", str(relative))
    resolved = _beneath(root, candidate, code="INPUT_ESCAPE")
    size = int(st.st_size)
    if size <= 0:
        _stop("INPUT_EMPTY", str(relative))
    if size > max_bytes:
        _stop("INPUT_TOO_LARGE", f"{relative}:{size}")
    return resolved, size


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return sha1(header + raw).hexdigest()


def _validate_processor_source(contract: dict[str, Any]) -> str:
    source_cfg = contract["adapters"]["JORNAL_OFICIAL"]["processor_source"]
    source_name = inspect.getsourcefile(JournalPdfProcessor)
    if not source_name:
        _stop("PROCESSOR_SOURCE_MISSING")
    source_path = Path(source_name)
    try:
        st = os.lstat(source_path)
    except FileNotFoundError:
        _stop("PROCESSOR_SOURCE_MISSING")
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        _stop("PROCESSOR_SOURCE_NOT_REGULAR")

    expected_parts = Path(source_cfg["module_path"]).parts
    if tuple(source_path.parts[-len(expected_parts):]) != tuple(expected_parts):
        _stop("PROCESSOR_SOURCE_PATH", str(source_path))

    raw = source_path.read_bytes()
    observed = _git_blob_sha(raw)
    if observed != source_cfg["expected_git_blob_sha"]:
        _stop(
            "PROCESSOR_BLOB_DRIFT",
            f"expected={source_cfg['expected_git_blob_sha']};observed={observed}",
        )

    try:
        tree = ast.parse(raw.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError):
        _stop("PROCESSOR_SOURCE_PARSE")
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = set(source_cfg["forbidden_import_roots"])
    unexpected = sorted(imports & forbidden)
    if unexpected:
        _stop("PROCESSOR_FORBIDDEN_IMPORT", ",".join(unexpected))
    return observed


def validate_contract(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("version") != 1:
        _stop("CONTRACT_VERSION")
    if data.get("task") != "TASK_090_EPHEMERAL_RUNTIME_DIGEST_EXECUTOR":
        _stop("CONTRACT_TASK")
    if data.get("mode") != "T0_OFFLINE_EPHEMERAL_RUNTIME_DIGEST":
        _stop("CONTRACT_MODE")

    limits = data.get("limits")
    if not isinstance(limits, dict):
        _stop("CONTRACT_LIMITS")
    max_files = limits.get("max_batch_files")
    max_each = limits.get("max_input_bytes_each")
    max_total = limits.get("max_total_input_bytes")
    if not isinstance(max_files, int) or not 1 <= max_files <= 3:
        _stop("CONTRACT_MAX_FILES")
    if not isinstance(max_each, int) or max_each <= 0 or max_each > 70_000_000:
        _stop("CONTRACT_MAX_EACH")
    if not isinstance(max_total, int) or max_total <= 0 or max_total > 110_000_000:
        _stop("CONTRACT_MAX_TOTAL")
    if max_total < max_each:
        _stop("CONTRACT_TOTAL_LT_EACH")

    candidate_root = _safe_relative_path(
        data.get("candidate_root"), code="CONTRACT_CANDIDATE_ROOT"
    )
    if candidate_root.parts[0] in {".git", ".github"}:
        _stop("CONTRACT_CANDIDATE_ROOT_RESERVED")

    adapters = data.get("adapters")
    if not isinstance(adapters, dict) or set(adapters) != {"JORNAL_OFICIAL"}:
        _stop("CONTRACT_ADAPTER_SET")
    journal = adapters["JORNAL_OFICIAL"]
    required = {
        "required_maturity": "EXECUTION_READY_BOUNDED",
        "processor_contract": "JORNAL_OFICIAL_LIMEIRA_PDF_V01",
        "stage_bronze": False,
        "plan_reconciliation": False,
        "ocr_allowed": False,
        "network_allowed": False,
        "persistent_writes_allowed": False,
    }
    if not isinstance(journal, dict):
        _stop("CONTRACT_JOURNAL_ADAPTER")
    for key, expected in required.items():
        if journal.get(key) != expected:
            _stop("CONTRACT_JOURNAL_ADAPTER", key)
    if journal.get("supported_mime") != ["application/pdf"]:
        _stop("CONTRACT_JOURNAL_MIME")
    source_cfg = journal.get("processor_source")
    if not isinstance(source_cfg, dict):
        _stop("CONTRACT_PROCESSOR_SOURCE")
    if source_cfg.get("module_path") != "robo_dados_publicos/journal/processing.py":
        _stop("CONTRACT_PROCESSOR_PATH")
    if not re.fullmatch(r"[0-9a-f]{40}", str(source_cfg.get("expected_git_blob_sha") or "")):
        _stop("CONTRACT_PROCESSOR_BLOB")
    expected_forbidden = [
        "boto3",
        "ftplib",
        "googleapiclient",
        "http",
        "paramiko",
        "requests",
        "smtplib",
        "socket",
        "subprocess",
        "urllib",
    ]
    if source_cfg.get("forbidden_import_roots") != expected_forbidden:
        _stop("CONTRACT_PROCESSOR_IMPORT_GUARD")
    expected_outputs = [
        "edition_manifest.json",
        "pages_silver.jsonl",
        "events_gold.jsonl",
        "chunks_rag.jsonl",
    ]
    if journal.get("allowed_output_files") != expected_outputs:
        _stop("CONTRACT_JOURNAL_OUTPUTS")

    effects = data.get("automatic_remote_effects")
    if not isinstance(effects, dict) or set(effects) != set(REMOTE_EFFECT_KEYS):
        _stop("CONTRACT_EFFECT_SET")
    if any(effects[key] is not False for key in REMOTE_EFFECT_KEYS):
        _stop("CONTRACT_REMOTE_EFFECT_ENABLED")
    return data


def _validate_manifest(
    manifest: dict[str, Any], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    if manifest.get("schema") != "EPHEMERAL_DIGEST_BATCH_V1":
        _stop("MANIFEST_SCHEMA")
    batch_id = str(manifest.get("batch_id") or "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", batch_id):
        _stop("BATCH_ID")

    effects = manifest.get("remote_effects_authorized")
    if not isinstance(effects, dict) or set(effects) != set(REMOTE_EFFECT_KEYS):
        _stop("MANIFEST_EFFECT_SET")
    if any(effects[key] is not False for key in REMOTE_EFFECT_KEYS):
        _stop("MANIFEST_REMOTE_EFFECT_ENABLED")

    inputs = manifest.get("inputs")
    max_files = contract["limits"]["max_batch_files"]
    if not isinstance(inputs, list) or not 1 <= len(inputs) <= max_files:
        _stop("INPUT_COUNT")
    seen_keys: set[str] = set()
    seen_paths: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in inputs:
        if not isinstance(item, dict):
            _stop("INPUT_RECORD")
        family = str(item.get("family") or "")
        if family not in contract["adapters"]:
            _stop("FAMILY_NOT_ADAPTED", family or "MISSING")
        source_key = str(item.get("source_key") or "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", source_key):
            _stop("SOURCE_KEY", source_key or "MISSING")
        if source_key in seen_keys:
            _stop("DUPLICATE_SOURCE_KEY", source_key)
        seen_keys.add(source_key)
        if item.get("mime_type") not in contract["adapters"][family]["supported_mime"]:
            _stop("UNSUPPORTED_MIME", source_key)
        relative = _safe_relative_path(item.get("relative_path"), code="INPUT_PATH")
        relative_key = relative.as_posix()
        if relative_key in seen_paths:
            _stop("DUPLICATE_INPUT_PATH", relative_key)
        seen_paths.add(relative_key)
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            _stop("INPUT_METADATA", source_key)
        normalized.append(
            {
                "family": family,
                "source_key": source_key,
                "mime_type": item["mime_type"],
                "relative_path": relative,
                "metadata": metadata,
            }
        )
    return normalized


def _journal_metadata(
    metadata: dict[str, Any], *, source_key: str
) -> tuple[int, str | None, str | None]:
    edition = metadata.get("edition")
    if not isinstance(edition, int) or not 1 <= edition <= 99999:
        _stop("JOURNAL_EDITION", source_key)
    publication_date = metadata.get("publication_date")
    if publication_date is not None:
        if not isinstance(publication_date, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", publication_date
        ):
            _stop("JOURNAL_PUBLICATION_DATE", source_key)
    source_url = metadata.get("source_url")
    if source_url is not None and not isinstance(source_url, str):
        _stop("JOURNAL_SOURCE_URL", source_key)
    return edition, publication_date, source_url


def _inventory_outputs(item_dir: Path, allowed: list[str]) -> list[dict[str, Any]]:
    observed = sorted(
        str(path.relative_to(item_dir)).replace("\\", "/")
        for path in item_dir.rglob("*")
        if path.is_file()
    )
    if observed != sorted(allowed):
        _stop("OUTPUT_SET_DRIFT", ",".join(observed))
    records: list[dict[str, Any]] = []
    for name in allowed:
        path = item_dir / name
        st = os.lstat(path)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            _stop("OUTPUT_NOT_REGULAR", name)
        records.append(
            {
                "name": name,
                "bytes": int(st.st_size),
                "sha256": _sha256_file(path),
            }
        )
    return records


def run_ephemeral_digest(
    contract: dict[str, Any],
    manifest: dict[str, Any],
    maturity_registry: dict[str, Any],
    *,
    workspace_root: str | Path,
) -> dict[str, Any]:
    contract = validate_contract(contract)
    maturity_registry = validate_maturity_registry(maturity_registry)
    inputs = _validate_manifest(manifest, contract)
    root = Path(workspace_root)
    try:
        root_stat = os.lstat(root)
    except FileNotFoundError:
        _stop("WORKSPACE_ROOT")
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        _stop("WORKSPACE_ROOT_NOT_REAL_DIRECTORY")
    root = root.resolve(strict=True)
    processor_blob_sha = _validate_processor_source(contract)

    candidate_rel = _safe_relative_path(
        contract["candidate_root"], code="CONTRACT_CANDIDATE_ROOT"
    )
    candidate_parent = root / candidate_rel
    if candidate_parent.exists() or candidate_parent.is_symlink():
        _stop("CANDIDATE_ROOT_NOT_FRESH")
    batch_dir = candidate_parent / manifest["batch_id"]

    max_each = contract["limits"]["max_input_bytes_each"]
    max_total = contract["limits"]["max_total_input_bytes"]
    staged: list[tuple[dict[str, Any], Path, int]] = []
    total_input_bytes = 0
    for item in inputs:
        required_maturity = contract["adapters"][item["family"]]["required_maturity"]
        observed_maturity = execution_maturity(item["family"], maturity_registry)
        if observed_maturity != required_maturity:
            _stop(
                "FAMILY_MATURITY",
                f"{item['family']}:{observed_maturity}",
            )
        path, size = _read_regular_file_beneath(
            root, item["relative_path"], max_bytes=max_each
        )
        total_input_bytes += size
        if total_input_bytes > max_total:
            _stop("BATCH_TOO_LARGE", str(total_input_bytes))
        staged.append((item, path, size))

    batch_dir.mkdir(parents=True, exist_ok=False)
    item_results: list[dict[str, Any]] = []
    candidate_records: list[dict[str, Any]] = []
    try:
        for item, source_path, source_bytes in staged:
            if item["family"] != "JORNAL_OFICIAL":
                _stop("FAMILY_DISPATCH", item["family"])
            edition, publication_date, source_url = _journal_metadata(
                item["metadata"], source_key=item["source_key"]
            )
            item_dir = batch_dir / item["source_key"]
            item_dir.mkdir(parents=False, exist_ok=False)
            processed = JournalPdfProcessor().process(
                source_path,
                edition=edition,
                publication_date=publication_date,
                source_url=source_url,
                out_dir=item_dir,
                stage_bronze=False,
                plan_reconciliation=False,
                emit_semantic_facets=False,
            )
            if processed.get("status") != "PASS_DOCUMENT_PROCESSING":
                _stop(
                    "ADAPTER_STATUS",
                    f"{item['source_key']}:{processed.get('status')}",
                )
            if processed.get("bronze") is not None:
                _stop("BRONZE_EFFECT", item["source_key"])
            if processed.get("reconciliation_tasks") != 0:
                _stop("RECONCILIATION_EFFECT", item["source_key"])

            outputs = _inventory_outputs(
                item_dir,
                contract["adapters"][item["family"]]["allowed_output_files"],
            )
            for output in outputs:
                candidate_records.append(
                    {
                        "source_key": item["source_key"],
                        **output,
                    }
                )
            item_results.append(
                {
                    "source_key": item["source_key"],
                    "family": item["family"],
                    "source_sha256": _sha256_file(source_path),
                    "source_bytes": source_bytes,
                    "adapter_status": processed["status"],
                    "silver_rows": processed["silver_pages"],
                    "gold_rows": processed["gold_events"],
                    "rag_rows": processed["rag_chunks"],
                    "candidate_files": outputs,
                }
            )
    except Exception:
        shutil.rmtree(candidate_parent, ignore_errors=True)
        raise

    candidate_set_sha256 = sha256(canonical_bytes(candidate_records)).hexdigest()
    core = {
        "schema": "EPHEMERAL_DIGEST_RESULT_V1",
        "batch_id": manifest["batch_id"],
        "mode": contract["mode"],
        "input_count": len(item_results),
        "input_bytes": total_input_bytes,
        "processor_git_blob_sha": processor_blob_sha,
        "items": item_results,
        "candidate_root": str(candidate_rel / manifest["batch_id"]).replace("\\", "/"),
        "candidate_file_count": len(candidate_records),
        "candidate_set_sha256": candidate_set_sha256,
        "persistence_authorized": False,
        "effects": {
            **{key: 0 for key in REMOTE_EFFECT_KEYS},
            "local_candidate_files": len(candidate_records),
        },
        "status": "PASS_EPHEMERAL_RUNTIME_DIGEST_NOT_PERSISTED",
    }
    return {
        "result_sha256": sha256(canonical_bytes(core)).hexdigest(),
        **core,
    }
