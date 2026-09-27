from __future__ import annotations

import hashlib
from dataclasses import dataclass

@dataclass(frozen=True)
class DedupeDecision:
    state: str
    content_identity: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare_content(*, incoming_sha256: str, existing_sha256: str | None, same_title: bool=False, same_size: bool=False) -> DedupeDecision:
    if existing_sha256 and incoming_sha256 == existing_sha256:
        return DedupeDecision("DUPLICATE_CONTENT_REUSE_IDENTITY", incoming_sha256)
    if existing_sha256 and incoming_sha256 != existing_sha256:
        return DedupeDecision("DISTINCT_CONTENT_KEEP_BOTH", incoming_sha256)
    return DedupeDecision("NEW_CONTENT_CREATE_ONLY_BRONZE_ELIGIBLE", incoming_sha256)


def validate_sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())
