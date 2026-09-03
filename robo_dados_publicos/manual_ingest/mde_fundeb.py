from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import hashlib
import json
import re
import unicodedata

from pypdf import PdfReader


F02_FAMILIES = ("RREO_MDE", "FUNDEB_LOCAL", "MDE_25_LOCAL")


class F02IngestStop(ValueError):
    """Fail-closed stop for the F02 supervised MDE/FUNDEB adapter."""


@dataclass(frozen=True)
class F02SourceContract:
    source_id: str
    family: str
    role: str
    drive_file_id: str
    expected_sha256: str
    expected_bytes: int
    expected_pages: int
    source_type: str = "SOURCE"
    ingestion_method: str = "MANUAL_SUPERVISED"

    @classmethod
    def from_mapping(cls, raw: dict) -> "F02SourceContract":
        required = (
            "source_id",
            "family",
            "role",
            "drive_file_id",
            "expected_sha256",
            "expected_bytes",
            "expected_pages",
        )
        missing = [key for key in required if raw.get(key) in (None, "")]
        if missing:
            raise F02IngestStop("STOP_F02_CONTRACT_MISSING_FIELDS: " + ", ".join(missing))
        family = str(raw["family"]).upper().strip()
        if family not in F02_FAMILIES:
            raise F02IngestStop(f"STOP_F02_CONTRACT_BAD_FAMILY: {family}")
        digest = str(raw["expected_sha256"]).lower().strip()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise F02IngestStop(f"STOP_F02_CONTRACT_BAD_SHA256: {raw['source_id']}")
        try:
            expected_bytes = int(raw["expected_bytes"])
            expected_pages = int(raw["expected_pages"])
        except (TypeError, ValueError) as exc:
            raise F02IngestStop(f"STOP_F02_CONTRACT_BAD_SIZE_OR_PAGES: {raw['source_id']}") from exc
        if expected_bytes <= 0 or expected_pages <= 0:
            raise F02IngestStop(f"STOP_F02_CONTRACT_BAD_SIZE_OR_PAGES: {raw['source_id']}")
        if str(raw.get("source_type", "SOURCE")).upper().strip() != "SOURCE":
            raise F02IngestStop(f"STOP_F02_SOURCE_MUST_BE_SOURCE: {raw['source_id']}")
        if str(raw.get("ingestion_method", "MANUAL_SUPERVISED")).upper().strip() != "MANUAL_SUPERVISED":
            raise F02IngestStop(f"STOP_F02_BAD_INGESTION_METHOD: {raw['source_id']}")
        return cls(
            source_id=str(raw["source_id"]).strip(),
            family=family,
            role=str(raw["role"]).strip(),
            drive_file_id=str(raw["drive_file_id"]).strip(),
            expected_sha256=digest,
            expected_bytes=expected_bytes,
            expected_pages=expected_pages,
        )


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    value = value.upper().replace("\u00a0", " ")
    return re.sub(r"[ \t]+", " ", value)


def load_f02_contract(path: str | Path) -> tuple[F02SourceContract, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("mode") != "MANUAL_SUPERVISED_INGEST":
        raise F02IngestStop("STOP_F02_CONTRACT_BAD_MODE")
    sources = raw.get("sources")
    if not isinstance(sources, list) or len(sources) != 3:
        raise F02IngestStop("STOP_F02_CONTRACT_EXACTLY_THREE_SOURCES_REQUIRED")
    contracts = tuple(F02SourceContract.from_mapping(item) for item in sources)
    ids = [item.source_id for item in contracts]
    if len(ids) != len(set(ids)):
        raise F02IngestStop("STOP_F02_CONTRACT_DUPLICATE_SOURCE_IDS")
    families = [item.family for item in contracts]
    if sorted(families) != sorted(F02_FAMILIES):
        raise F02IngestStop("STOP_F02_CONTRACT_EXACT_FAMILY_SET_REQUIRED")
    return contracts


def inspect_f02_pdf(payload: bytes) -> dict:
    try:
        reader = PdfReader(BytesIO(payload))
    except Exception as exc:
        raise F02IngestStop("STOP_F02_INVALID_PDF") from exc
    texts = [(page.extract_text() or "") for page in reader.pages]
    nonempty = sum(bool(text.strip()) for text in texts)
    return {
        "pages": len(reader.pages),
        "text_pages": nonempty,
        "text_chars": sum(len(text) for text in texts),
        "has_text_layer": nonempty == len(reader.pages) and nonempty > 0,
        "text": "\n".join(texts),
    }


def validate_f02_source_bytes(contract: F02SourceContract, payload: bytes) -> dict:
    digest = hashlib.sha256(payload).hexdigest()
    pdf = inspect_f02_pdf(payload)
    mismatches = {}
    if digest != contract.expected_sha256:
        mismatches["sha256"] = {"expected": contract.expected_sha256, "observed": digest}
    if len(payload) != contract.expected_bytes:
        mismatches["bytes"] = {"expected": contract.expected_bytes, "observed": len(payload)}
    if pdf["pages"] != contract.expected_pages:
        mismatches["pages"] = {"expected": contract.expected_pages, "observed": pdf["pages"]}
    if not pdf["has_text_layer"]:
        mismatches["text_layer"] = {"expected": "ALL_PAGES_NONEMPTY", "observed": pdf["text_pages"]}
    if mismatches:
        raise F02IngestStop("STOP_F02_SOURCE_IMMUTABLE_MISMATCH: " + json.dumps(mismatches, sort_keys=True))
    return {
        "status": "PASS_F02_SOURCE_BYTES_VERIFIED",
        "source_id": contract.source_id,
        "family": contract.family,
        "sha256": digest,
        "bytes": len(payload),
        "pages": pdf["pages"],
        "text": pdf["text"],
    }


def classify_f02_text(text: str) -> str:
    folded = _fold(text)
    signatures = {
        "RREO_MDE": (
            "RELATORIO RESUMIDO DA EXECUCAO ORCAMENTARIA",
            "DEMONSTRATIVO DAS RECEITAS E DESPESAS COM MANUTENCAO E DESENVOLVIMENTO DO ENSINO",
            "RREO - ANEXO 8",
        ),
        "FUNDEB_LOCAL": (
            "APLICACAO COM RECURSOS DO FUNDEB",
            "RECEITA DO FUNDEB",
            "PROFISSIONAIS DA EDUCACAO BASICA",
        ),
        "MDE_25_LOCAL": (
            "APLICACAO DOS RECURSOS PROPRIOS EM ENSINO - POR DATA",
            "APLICACAO MINIMA CONSTITUCIONAL",
            "DESPESAS PROPRIAS EM EDUCACAO",
        ),
    }
    matched = [family for family, markers in signatures.items() if all(marker in folded for marker in markers)]
    if not matched:
        raise F02IngestStop("STOP_F02_CLASSIFIER_UNKNOWN_DOCUMENT")
    if len(matched) != 1:
        raise F02IngestStop("STOP_F02_CLASSIFIER_AMBIGUOUS_DOCUMENT: " + ",".join(sorted(matched)))
    return matched[0]


def validate_f02_classification(contract: F02SourceContract, text: str) -> dict:
    observed = classify_f02_text(text)
    if observed != contract.family:
        raise F02IngestStop(
            f"STOP_F02_CLASSIFIER_CONTRACT_MISMATCH: expected={contract.family};observed={observed}"
        )
    return {"status": "PASS_F02_CLASSIFICATION", "source_id": contract.source_id, "family": observed}
