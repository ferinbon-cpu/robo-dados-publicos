"""Fail-closed, offline inspector for a future local SIOPE metadata package."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

TARGET_ALIASES = (
    "NUM_POPU",
    "VAL_RECE_PREV_ATUA", "VAL_RECE_REAL", "VAL_DESP_DOTA_ATUA",
    "VAL_DESP_EMPE", "VAL_DESP_LIQU", "VAL_DESP_PAGA",
    "VL_DESP_DOTA_ATUA_EDU", "VL_DESP_EMPE_EDU", "VL_DESP_LIQU_EDU",
    "VL_DESP_PAGA_EDU",
)
ALLOWED_SUFFIXES = {".csv", ".json", ".txt", ".xml"}
ACTIVE_SUFFIXES = {
    ".bat", ".cmd", ".com", ".dll", ".exe", ".hta", ".jar", ".js", ".jse",
    ".lnk", ".msi", ".ps1", ".py", ".scr", ".sh", ".vbs", ".xlsm", ".docm",
}
EXECUTABLE_MAGICS = (b"MZ", b"\x7fELF", b"#!")
SEMANTIC_STATES = ("PROVEN", "PARTIAL", "NOT_FOUND", "AMBIGUOUS", "NOT_APPLICABLE")


class InspectionError(RuntimeError):
    """A deterministic STOP raised before unsafe or inconclusive processing."""


@dataclass(frozen=True)
class InspectionLimits:
    max_entries: int = 256
    max_entry_size: int = 8 * 1024 * 1024
    max_total_size: int = 32 * 1024 * 1024
    max_depth: int = 8
    max_compression_ratio: float = 100.0

    def __post_init__(self) -> None:
        if min(self.max_entries, self.max_entry_size, self.max_total_size, self.max_depth) <= 0:
            raise ValueError("inspection limits must be positive")
        if self.max_compression_ratio < 1:
            raise ValueError("compression ratio must be at least 1")


def _stop(code: str) -> None:
    raise InspectionError(f"STOP_TASK_010A_{code}")


def _safe_name(raw_name: str, limits: InspectionLimits) -> PurePosixPath:
    normalized = raw_name.replace("\\", "/")
    path = PurePosixPath(normalized)
    win = PureWindowsPath(raw_name)
    if not raw_name or "\x00" in raw_name:
        _stop("INVALID_PATH")
    if path.is_absolute() or win.is_absolute() or win.drive:
        _stop("ABSOLUTE_PATH")
    if any(part in {"", ".", ".."} for part in path.parts):
        _stop("PATH_TRAVERSAL")
    if len(path.parts) > limits.max_depth:
        _stop("DEPTH_LIMIT")
    return path


def _real_type(data: bytes) -> str:
    if data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "zip"
    if data.startswith(EXECUTABLE_MAGICS):
        return "executable"
    return "unknown"


def _decode_metadata(data: bytes) -> str:
    if data.startswith(EXECUTABLE_MAGICS):
        _stop("ACTIVE_CONTENT_MAGIC")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        _stop("NON_UTF8_METADATA")


def _semantic_matrix(documents: list[tuple[str, str]]) -> list[dict]:
    matrix = []
    for alias in TARGET_ALIASES:
        occurrences: list[tuple[str, str | None]] = []
        pattern = re.compile(rf"(?m)^\s*{re.escape(alias)}\s*(?:[,:=|;-]\s*(.+?))?\s*$")
        for source, text in documents:
            for match in pattern.finditer(text):
                definition = (match.group(1) or "").strip() or None
                occurrences.append((source, definition))
        definitions = sorted({definition for _, definition in occurrences if definition})
        if not occurrences:
            state = "NOT_FOUND"
        elif not definitions:
            state = "PARTIAL"
        elif len(definitions) > 1:
            state = "AMBIGUOUS"
        else:
            state = "PROVEN"
        matrix.append({
            "field": alias,
            "presence": state if state == "NOT_FOUND" else "PROVEN",
            "definition": state,
            "source": sorted({source for source, _ in occurrences}),
            "temporal_rule": "NOT_APPLICABLE",
            "conceptual_bridge": "NOT_APPLICABLE",
            "decision": state,
            "synthetic_only": True,
        })
    return matrix


def inspect(path: Path, limits: InspectionLimits = InspectionLimits()) -> dict:
    """Inspect one local ZIP without writing or executing its contents."""
    try:
        original = path.read_bytes()
    except OSError as exc:
        raise InspectionError("STOP_TASK_010A_UNREADABLE_INPUT") from exc
    digest = hashlib.sha256(original).hexdigest()
    real_type = _real_type(original)
    if real_type != "zip":
        _stop("UNSUPPORTED_SIGNATURE")

    entries: list[dict] = []
    documents: list[tuple[str, str]] = []
    total_size = 0
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > limits.max_entries:
                _stop("ENTRY_COUNT_LIMIT")
            for info in infos:
                safe_path = _safe_name(info.filename, limits)
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    _stop("SYMLINK")
                if info.is_dir():
                    continue
                suffix = safe_path.suffix.lower()
                if suffix in ACTIVE_SUFFIXES:
                    _stop("ACTIVE_CONTENT_EXTENSION")
                if suffix not in ALLOWED_SUFFIXES:
                    _stop("NON_ALLOWLISTED_TYPE")
                if info.file_size > limits.max_entry_size:
                    _stop("ENTRY_SIZE_LIMIT")
                total_size += info.file_size
                if total_size > limits.max_total_size:
                    _stop("TOTAL_SIZE_LIMIT")
                ratio = info.file_size / max(info.compress_size, 1)
                if ratio > limits.max_compression_ratio:
                    _stop("COMPRESSION_RATIO_LIMIT")
                data = archive.read(info)
                if len(data) != info.file_size:
                    _stop("SIZE_MISMATCH")
                text = _decode_metadata(data)
                documents.append((safe_path.as_posix(), text))
                entries.append({
                    "path": safe_path.as_posix(), "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "sha256": hashlib.sha256(data).hexdigest(),
                })
    except InspectionError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise InspectionError("STOP_TASK_010A_CORRUPT_ARCHIVE") from exc

    entries.sort(key=lambda item: item["path"])
    return {
        "schema": "SIOPE_2025_METADATA_OFFLINE_INSPECTION_V1",
        "status": "INSPECTED_SYNTHETIC_NOT_EVIDENCE",
        "input": {"sha256": digest, "detected_type": real_type, "size": len(original)},
        "limits": asdict(limits),
        "entries": entries,
        "semantic_states": list(SEMANTIC_STATES),
        "semantic_matrix": _semantic_matrix(sorted(documents)),
        "canonical_state_changed": False,
        "remote_effects": 0,
    }


def dumps(result: dict) -> str:
    """Return a stable, sanitized JSON representation."""
    return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
