from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import hashlib
import json
import re
import unicodedata

from pypdf import PdfReader


REQUIRED_FINANCIAL_IDENTITY_CHAIN = (
    "indicator_or_target",
    "program",
    "explicit_action_or_subaction",
    "budget_unit",
    "funding_source_or_destination",
    "expense_nature",
    "appropriation",
    "committed",
    "liquidated",
    "paid",
)


class ManualIngestStop(ValueError):
    """Fail-closed stop raised when a supervised ingest contract is not met."""


@dataclass(frozen=True)
class ManualSourceContract:
    source_id: str
    family: str
    legal_number: str
    reference_period: str
    expected_sha256: str
    expected_bytes: int
    expected_pages: int
    source_type: str = "SOURCE"
    ingestion_method: str = "MANUAL_SUPERVISED"

    @classmethod
    def from_mapping(cls, raw: dict) -> "ManualSourceContract":
        required = (
            "source_id",
            "family",
            "legal_number",
            "reference_period",
            "expected_sha256",
            "expected_bytes",
            "expected_pages",
        )
        missing = [key for key in required if raw.get(key) in (None, "")]
        if missing:
            raise ManualIngestStop(
                "STOP_MANUAL_CONTRACT_MISSING_FIELDS: " + ", ".join(missing)
            )

        family = str(raw["family"]).upper().strip()
        if family not in {"PPA", "LDO", "LOA"}:
            raise ManualIngestStop(f"STOP_MANUAL_CONTRACT_BAD_FAMILY: {family}")

        digest = str(raw["expected_sha256"]).lower().strip()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ManualIngestStop(
                f"STOP_MANUAL_CONTRACT_BAD_SHA256: {raw['source_id']}"
            )

        try:
            expected_bytes = int(raw["expected_bytes"])
            expected_pages = int(raw["expected_pages"])
        except (TypeError, ValueError) as exc:
            raise ManualIngestStop(
                f"STOP_MANUAL_CONTRACT_BAD_SIZE_OR_PAGES: {raw['source_id']}"
            ) from exc
        if expected_bytes <= 0 or expected_pages <= 0:
            raise ManualIngestStop(
                f"STOP_MANUAL_CONTRACT_BAD_SIZE_OR_PAGES: {raw['source_id']}"
            )

        source_type = str(raw.get("source_type", "SOURCE")).upper().strip()
        if source_type != "SOURCE":
            raise ManualIngestStop(
                f"STOP_MANUAL_SOURCE_MUST_BE_SOURCE: {raw['source_id']}"
            )
        ingestion_method = str(
            raw.get("ingestion_method", "MANUAL_SUPERVISED")
        ).upper().strip()
        if ingestion_method != "MANUAL_SUPERVISED":
            raise ManualIngestStop(
                f"STOP_MANUAL_BAD_INGESTION_METHOD: {raw['source_id']}"
            )

        return cls(
            source_id=str(raw["source_id"]).strip(),
            family=family,
            legal_number=str(raw["legal_number"]).strip(),
            reference_period=str(raw["reference_period"]).strip(),
            expected_sha256=digest,
            expected_bytes=expected_bytes,
            expected_pages=expected_pages,
            source_type=source_type,
            ingestion_method=ingestion_method,
        )


@dataclass(frozen=True)
class SourceValidationResult:
    source_id: str
    status: str
    sha256: str
    bytes: int
    pages: int


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return ascii_text.upper().replace("\u00a0", " ")


def _number(value: str) -> float | int:
    raw = value.strip().replace(" ", "")
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    number = float(raw)
    return int(number) if number.is_integer() else number


def load_manual_ingest_contract(path: str | Path) -> tuple[ManualSourceContract, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("mode") != "MANUAL_SUPERVISED_INGEST":
        raise ManualIngestStop("STOP_MANUAL_CONTRACT_BAD_MODE")
    sources = raw.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ManualIngestStop("STOP_MANUAL_CONTRACT_SOURCES_REQUIRED")
    contracts = tuple(ManualSourceContract.from_mapping(item) for item in sources)
    ids = [item.source_id for item in contracts]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise ManualIngestStop(
            "STOP_MANUAL_CONTRACT_DUPLICATE_SOURCE_IDS: " + ", ".join(duplicates)
        )
    return contracts


def inspect_pdf_text_layer(payload: bytes) -> dict:
    try:
        reader = PdfReader(BytesIO(payload))
    except Exception as exc:
        raise ManualIngestStop("STOP_MANUAL_SOURCE_INVALID_PDF") from exc
    nonempty_pages = 0
    chars = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            nonempty_pages += 1
            chars += len(text)
    return {
        "pages": len(reader.pages),
        "text_pages": nonempty_pages,
        "text_chars": chars,
        "has_text_layer": nonempty_pages > 0,
    }


def validate_source_bytes(
    contract: ManualSourceContract, payload: bytes
) -> SourceValidationResult:
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    observed_bytes = len(payload)
    pdf = inspect_pdf_text_layer(payload)
    mismatches: dict[str, dict[str, object]] = {}
    if observed_sha256 != contract.expected_sha256:
        mismatches["sha256"] = {
            "expected": contract.expected_sha256,
            "observed": observed_sha256,
        }
    if observed_bytes != contract.expected_bytes:
        mismatches["bytes"] = {
            "expected": contract.expected_bytes,
            "observed": observed_bytes,
        }
    if pdf["pages"] != contract.expected_pages:
        mismatches["pages"] = {
            "expected": contract.expected_pages,
            "observed": pdf["pages"],
        }
    if mismatches:
        raise ManualIngestStop(
            "STOP_MANUAL_SOURCE_IMMUTABLE_MISMATCH: "
            + json.dumps(mismatches, ensure_ascii=False, sort_keys=True)
        )
    return SourceValidationResult(
        source_id=contract.source_id,
        status="PASS_SOURCE_BYTES_VERIFIED",
        sha256=observed_sha256,
        bytes=observed_bytes,
        pages=pdf["pages"],
    )


def extract_ppa_eiti_program(text: str) -> dict:
    folded = _fold(text)
    program = re.search(
        r"PROGRAMA\s*:\s*2001\s+([^\n]+)",
        folded,
    )
    responsible = re.search(
        r"ORGAO\s+RESP(?:OSAVEL|ONSAVEL)\s+PRINCIPAL\s*:\s*10\.00\.00\s+([^\n]+)",
        folded,
    )
    indicator = re.search(
        r"INDICE DE ALUNOS EM EDUCACAO INTEGRAL\s*/\s*PERCENTUAL\s+"
        r"([0-9.,]+)\s+([0-9.,]+)\s+([0-9.,]+)\s+([0-9.,]+)\s+([0-9.,]+)\s+([0-9.,]+)",
        folded,
    )
    if not program:
        raise ManualIngestStop("STOP_PPA_PROGRAM_2001_NOT_FOUND")
    if not responsible:
        raise ManualIngestStop("STOP_PPA_RESPONSIBLE_UNIT_NOT_FOUND")
    if not indicator:
        raise ManualIngestStop("STOP_PPA_EITI_INDICATOR_NOT_FOUND")

    values = [_number(value) for value in indicator.groups()]
    if values != [52, 53, 55, 57, 59, 59]:
        raise ManualIngestStop(
            "STOP_PPA_EITI_TARGET_DRIFT: " + json.dumps(values, ensure_ascii=False)
        )

    malformed_medium_transport = "IS.522" in folded
    return {
        "program_code": "2001",
        "program_name": program.group(1).strip(),
        "responsible_unit_code": "10.00.00",
        "responsible_unit_name": responsible.group(1).strip(),
        "indicator": {
            "name": "INDICE DE ALUNOS EM EDUCACAO INTEGRAL",
            "unit": "PERCENTUAL",
            "recent": values[0],
            "2026": values[1],
            "2027": values[2],
            "2028": values[3],
            "2029": values[4],
            "final_ppa": values[5],
        },
        "known_text_extraction_review": (
            "PARSER_REVIEW_REQUIRED_TRANSPORTE_ENSINO_MEDIO"
            if malformed_medium_transport
            else "NONE"
        ),
    }


def parse_ldo_structural_markers(text: str) -> dict:
    folded = _fold(text)
    required = {
        "METAS_FISCAIS": r"DAS METAS FISCAIS",
        "RISCOS_FISCAIS": r"DOS RISCOS FISCAIS",
        "RESERVA_CONTINGENCIA": r"DA RESERVA DE CONTINGENCIA",
        "PESSOAL": r"DESPESA COM PESSOAL",
        "EDUCACAO": r"EDUCACAO",
    }
    found = {key: bool(re.search(pattern, folded)) for key, pattern in required.items()}
    missing = [key for key, present in found.items() if not present]
    if missing:
        raise ManualIngestStop(
            "STOP_LDO_REQUIRED_STRUCTURE_MISSING: " + ", ".join(missing)
        )
    return {
        "status": "PASS_LDO_REQUIRED_STRUCTURE",
        "markers": found,
    }


def validate_financial_identity(evidence: dict) -> dict:
    missing = [key for key in REQUIRED_FINANCIAL_IDENTITY_CHAIN if not evidence.get(key)]
    if missing:
        return {
            "status": "EVIDENCIA_INSUFICIENTE",
            "missing": missing,
            "program_level_bridge_is_financial_identity": False,
        }
    return {
        "status": "FINANCIAL_IDENTITY_PROVEN",
        "missing": [],
        "program_level_bridge_is_financial_identity": False,
    }
