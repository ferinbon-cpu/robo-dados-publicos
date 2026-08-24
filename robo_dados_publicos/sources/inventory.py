from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import json
import re


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    url: str
    logical_key: str
    file_name: str
    enabled: bool = True
    expected_content_types: tuple[str, ...] = ()
    expected_sha256: str | None = None
    expected_bytes: int | None = None
    cadence: str = "manual"
    notes: str = ""

    @classmethod
    def from_mapping(cls, raw: dict, *, allow_insecure_localhost: bool = False) -> "SourceSpec":
        required = ["source_id", "url", "logical_key", "file_name"]
        missing = [k for k in required if not str(raw.get(k, "")).strip()]
        if missing:
            raise ValueError("SOURCE_CONTRACT_MISSING_FIELDS: " + ", ".join(missing))

        source_id = str(raw["source_id"]).strip()
        if not source_id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"SOURCE_CONTRACT_BAD_ID: {source_id}")

        url = str(raw["url"]).strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ValueError(f"SOURCE_CONTRACT_BAD_URL: {source_id}")
        if parsed.scheme != "https":
            localhost = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
            if not (allow_insecure_localhost and localhost):
                raise ValueError(f"SOURCE_CONTRACT_HTTPS_REQUIRED: {source_id}")

        file_name = Path(str(raw["file_name"])).name
        if file_name != str(raw["file_name"]) or file_name in {"", ".", ".."}:
            raise ValueError(f"SOURCE_CONTRACT_BAD_FILE_NAME: {source_id}")

        raw_cts = raw.get("expected_content_types", [])
        if not isinstance(raw_cts, list):
            raise ValueError(f"SOURCE_CONTRACT_CONTENT_TYPES_MUST_BE_LIST: {source_id}")
        cts = tuple(
            str(x).strip().lower()
            for x in raw_cts
            if str(x).strip()
        )
        expected_sha256 = str(raw.get("expected_sha256", "")).strip().lower() or None
        if expected_sha256 and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise ValueError(f"SOURCE_CONTRACT_BAD_SHA256: {source_id}")

        expected_bytes = raw.get("expected_bytes")
        if expected_bytes is not None:
            try:
                expected_bytes = int(expected_bytes)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"SOURCE_CONTRACT_BAD_EXPECTED_BYTES: {source_id}") from exc
            if expected_bytes <= 0:
                raise ValueError(f"SOURCE_CONTRACT_BAD_EXPECTED_BYTES: {source_id}")
        return cls(
            source_id=source_id,
            url=url,
            logical_key=str(raw["logical_key"]).strip(),
            file_name=file_name,
            enabled=bool(raw.get("enabled", True)),
            expected_content_types=cts,
            expected_sha256=expected_sha256,
            expected_bytes=expected_bytes,
            cadence=str(raw.get("cadence", "manual")).strip() or "manual",
            notes=str(raw.get("notes", "")),
        )


@dataclass(frozen=True)
class SourceInventory:
    version: int
    sources: tuple[SourceSpec, ...]

    @property
    def enabled(self) -> tuple[SourceSpec, ...]:
        return tuple(s for s in self.sources if s.enabled)

    def summary(self) -> dict:
        return {
            "version": self.version,
            "count": len(self.sources),
            "enabled": len(self.enabled),
            "source_ids": [s.source_id for s in self.sources],
        }


def load_source_inventory(path: str | Path, *, allow_insecure_localhost: bool = False) -> SourceInventory:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    version = int(raw.get("version", 1))
    items = raw.get("sources")
    if not isinstance(items, list):
        raise ValueError("SOURCE_CONTRACT_SOURCES_MUST_BE_LIST")
    specs = tuple(SourceSpec.from_mapping(x, allow_insecure_localhost=allow_insecure_localhost) for x in items)
    ids = [s.source_id for s in specs]
    duplicates = sorted({x for x in ids if ids.count(x) > 1})
    if duplicates:
        raise ValueError("SOURCE_CONTRACT_DUPLICATE_IDS: " + ", ".join(duplicates))
    return SourceInventory(version=version, sources=specs)
