from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
import json
import re
import shutil
from typing import Iterable

from robo_dados_publicos.reconciliation.planner import ReconciliationPlanner


_PII_PATTERNS = {
    "CPF": re.compile(r"(?i)\bCPF\s*(?:n[ºo°.]?\s*)?[:\-]?\s*(?:\*{2,3}|\d{2,3})[.\s-]?(?:\*{2,3}|\d{3})[.\s-]?(?:\*{2,3}|\d{3})[-\s]?(?:\*{2}|\d{2})\b"),
    "RG": re.compile(r"(?i)\bR\.?G\.?\s*(?:n[ºo°.]?\s*)?[:\-]?\s*[0-9Xx*.\-]{5,20}\b"),
    "EMAIL": re.compile(r"(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b"),
    "PHONE": re.compile(r"(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?[\s.-]*)?(?:9\d{4}|\d{4})[\s.-]?\d{4}(?!\d)"),
}

_ORG_PATTERNS = [
    re.compile(r"(?i)\bSECRETARIA\s+MUNICIPAL\s+DE\s+[^\n:]{2,100}"),
    re.compile(r"(?i)\bCÂMARA\s+MUNICIPAL\s+DE\s+LIMEIRA\b"),
    re.compile(r"(?i)\bCEPROSOM\b"),
    re.compile(r"(?i)\bIPML\b"),
    re.compile(r"(?i)\bPREFEITURA\s+MUNICIPAL\s+DE\s+LIMEIRA\b"),
]

# Event starts are intentionally conservative. A missing event is preferable to
# hallucinating one from ordinary prose. Patterns can be extended under regression tests.
_EVENT_STARTS: list[tuple[str, re.Pattern[str]]] = [
    ("TERMO_ADITIVO_CONTRATO", re.compile(r"(?i)^(?:(?:PRIMEIRO|SEGUNDO|TERCEIRO|QUARTO|QUINTO|SEXTO|SÉTIMO|SETIMO|OITAVO|NONO|DÉCIMO|DECIMO)|\d+[ºªo])\s+TERMO\s+(?:DE\s+)?ADITIVO\s+AO\s+CONTRATO\b")),
    ("APOSTILAMENTO", re.compile(r"(?i)^(?:(?:PRIMEIRO|SEGUNDO|TERCEIRO|QUARTO|QUINTO)|\d+[ºªo])\s+TERMO\s+DE\s+APOSTILAMENTO\b")),
    ("CONTRATO", re.compile(r"(?i)^CONTRATO\s+N[ºO°.]?\s*:?\s*\S+")),
    ("ATA_REGISTRO_PRECOS", re.compile(r"(?i)^ATA\s+N[ºO°.]?\s*:?\s*\S+")),
    ("CONVENIO", re.compile(r"(?i)^TERMO\s+DE\s+CONV[ÊE]NIO\b")),
    ("DECRETO", re.compile(r"(?i)^DECRETO\s+(?:N[ºO°.]?\s*)?\d")),
    ("PORTARIA", re.compile(r"(?i)^PORTARIA\s+(?:N[ºO°.]?\s*)?\d")),
    ("LEI", re.compile(r"(?i)^LEI\s+(?:N[ºO°.]?\s*)?\d")),
    ("RESOLUCAO", re.compile(r"(?i)^RESOLU[ÇC][ÃA]O\s+(?:N[ºO°.]?\s*)?\d")),
    ("EDITAL", re.compile(r"(?i)^EDITAL\s*(?:N[ºO°.]?\s*)?:?\s*\d")),
    ("AVISO_LICITACAO", re.compile(r"(?i)^AVISO\s+(?:DE\s+)?LICITA[ÇC][ÃA]O\b")),
]

_FIELD_PATTERNS = {
    "contract_number": re.compile(r"(?i)\bCONTRATO\s+N[ºO°.]?\s*:?\s*([0-9A-Za-z./-]+)"),
    "process_number": re.compile(r"(?i)\bPROCESSO(?:\s+ADMINISTRATIVO)?\s+N[ºO°.]?\s*:?\s*([0-9A-Za-z./-]+)"),
    "edital_number": re.compile(r"(?i)\bEDITAL\s*(?:N[ºO°.]?\s*)?:?\s*([0-9A-Za-z./-]+)"),
    "cnpj": re.compile(r"(?i)\bCNPJ\s*(?:N[ºO°.]?\s*)?[:\-]?\s*([0-9 .\-/]{14,22})"),
    "bidding": re.compile(r"(?i)\b(PREG[ÃA]O\s+ELETR[ÔO]NICO|PREG[ÃA]O|DISPENSA|INEXIGIBILIDADE|CONCORR[ÊE]NCIA(?:\s+P[ÚU]BLICA)?|CHAMAMENTO\s+P[ÚU]BLICO)\s+N[ºO°.]?\s*:?\s*([0-9A-Za-z./-]+)"),
    "signature_date": re.compile(r"(?i)\b(?:DATA\s+DA\s+ASSINATURA|ASSINATURA)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})"),
}

_LABELS = (
    "OBJETO", "CONTRATADA", "CONTRATANTE", "EMPRESA DETENTORA DA ATA", "VALOR TOTAL",
    "VALOR", "DATA DA ASSINATURA", "ASSINATURA", "PRAZO", "VIGÊNCIA", "VIGENCIA",
    "FUNDAMENTAÇÃO LEGAL", "FUNDAMENTACAO LEGAL", "EDITAL", "PROCESSO", "CONTRATO",
    "PREGÃO ELETRÔNICO", "PREGAO ELETRONICO", "DISPENSA", "INEXIGIBILIDADE",
)


@dataclass(frozen=True)
class RedactionResult:
    text: str
    counts: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str
    char_count: int


@dataclass(frozen=True)
class JournalEvent:
    event_id: str
    source_id: str
    edition: int
    publication_date: str | None
    page_number: int
    start_line: int
    end_line: int
    event_type: str
    organ: str | None
    act_number: str | None
    contract_number: str | None
    process_number: str | None
    edital_number: str | None
    bidding_modality: str | None
    bidding_number: str | None
    contractor: str | None
    cnpj: str | None
    object_text: str | None
    value_brl: str | None
    signature_date: str | None
    source_url: str | None
    source_sha256: str
    excerpt_redacted: str
    pii_redactions: int

    def to_dict(self) -> dict:
        return asdict(self)


def sha256_file(path: str | Path) -> str:
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    lines = []
    for raw in text.split("\n"):
        line = " ".join(raw.split())
        if line:
            lines.append(line)
    return "\n".join(lines)


def redact_personal_identifiers(text: str) -> RedactionResult:
    out = text
    counts: dict[str, int] = {}
    for label, pattern in _PII_PATTERNS.items():
        out, n = pattern.subn(f"[{label}_REDACTED]", out)
        counts[label] = n
    return RedactionResult(text=out, counts=counts)


def _clean_cnpj(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) == 14 else None


def _brl_to_decimal_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.replace("R$", "").strip().replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    try:
        return f"{Decimal(cleaned):.2f}"
    except (InvalidOperation, ValueError):
        return None


def _extract_label_value(block: str, label: str) -> str | None:
    # Capture a field until the next known uppercase label or end-of-block.
    labels = "|".join(re.escape(x) for x in _LABELS if x != label)
    pattern = re.compile(
        rf"(?is)\b{re.escape(label)}\s*:?\s*(.+?)(?=\s+(?:{labels})\s*:?|$)"
    )
    m = pattern.search(block)
    if not m:
        return None
    value = " ".join(m.group(1).split()).strip(" ,;.-")
    return value or None


def _extract_value_brl(block: str) -> str | None:
    m = re.search(r"(?i)\bVALOR(?:\s+TOTAL)?\s*:?\s*R\$\s*([0-9.]+,\d{2})", block)
    return _brl_to_decimal_text(m.group(1)) if m else None


def _extract_act_number(event_type: str, block: str) -> str | None:
    name_map = {
        "DECRETO": "DECRETO",
        "PORTARIA": "PORTARIA",
        "LEI": "LEI",
        "RESOLUCAO": r"RESOLU[ÇC][ÃA]O",
        "EDITAL": "EDITAL",
    }
    target = name_map.get(event_type)
    if not target:
        return None
    m = re.search(rf"(?i)\b{target}\s*(?:N[ºO°.]?\s*)?:?\s*([0-9A-Za-z./-]+)", block)
    return m.group(1) if m else None


def detect_organ(lines: Iterable[str], current: str | None = None) -> str | None:
    found = current
    for line in lines:
        for pattern in _ORG_PATTERNS:
            m = pattern.search(line)
            if m:
                found = " ".join(m.group(0).split()).strip(" :-")
    return found


def _event_start(line: str) -> str | None:
    for event_type, pattern in _EVENT_STARTS:
        if pattern.search(line):
            return event_type
    return None


def _contractor(block: str) -> str | None:
    for label in ("CONTRATADA", "EMPRESA DETENTORA DA ATA"):
        value = _extract_label_value(block, label)
        if value:
            # Some PDFs leave CNPJ in the same captured value. Keep only the name portion.
            value = re.split(r"(?i)\s+CNPJ\b", value, maxsplit=1)[0].strip(" ,;")
            return value or None
    return None


def parse_events_from_page(
    text: str,
    *,
    edition: int,
    publication_date: str | None,
    page_number: int,
    source_url: str | None,
    source_sha256: str,
) -> list[JournalEvent]:
    lines = [x for x in normalize_text(text).split("\n") if x]
    starts: list[tuple[int, str]] = []
    current_org: str | None = None
    org_at_line: dict[int, str | None] = {}
    for idx, line in enumerate(lines):
        current_org = detect_organ([line], current=current_org)
        org_at_line[idx] = current_org
        kind = _event_start(line)
        if kind == "EDITAL" and starts and starts[-1][1] in {"CONTRATO", "TERMO_ADITIVO_CONTRATO", "ATA_REGISTRO_PRECOS"} and idx - starts[-1][0] <= 30:
            # In contract extracts, EDITAL Nº is commonly a field, not a new act.
            kind = None
        if kind:
            starts.append((idx, kind))

    events: list[JournalEvent] = []
    source_id = f"LIMEIRA_JO_{edition:05d}"
    for pos, (start, event_type) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        # Avoid gigantic blocks caused by sparse headings; 120 lines is enough context for one act.
        end = min(end, start + 120)
        block_lines = lines[start:end]
        block = "\n".join(block_lines)
        redaction = redact_personal_identifiers(block)
        compact_excerpt = " ".join(redaction.text.split())[:1200]

        contract_number = (_FIELD_PATTERNS["contract_number"].search(block) or [None, None])[1] if _FIELD_PATTERNS["contract_number"].search(block) else None
        process_number = (_FIELD_PATTERNS["process_number"].search(block) or [None, None])[1] if _FIELD_PATTERNS["process_number"].search(block) else None
        edital_number = (_FIELD_PATTERNS["edital_number"].search(block) or [None, None])[1] if _FIELD_PATTERNS["edital_number"].search(block) else None
        cnpj_match = _FIELD_PATTERNS["cnpj"].search(block)
        cnpj = _clean_cnpj(cnpj_match.group(1)) if cnpj_match else None
        bidding_match = _FIELD_PATTERNS["bidding"].search(block)
        signature_match = _FIELD_PATTERNS["signature_date"].search(block)
        object_text = _extract_label_value(block, "OBJETO")
        if object_text:
            object_text = redact_personal_identifiers(object_text).text[:2000]
        value_brl = _extract_value_brl(block)
        act_number = _extract_act_number(event_type, block)
        identity = "|".join([
            source_id, str(page_number), str(start + 1), event_type,
            act_number or "", contract_number or "", process_number or "",
        ])
        event_id = "JOEV_" + sha256(identity.encode("utf-8")).hexdigest()[:20]
        events.append(JournalEvent(
            event_id=event_id,
            source_id=source_id,
            edition=edition,
            publication_date=publication_date,
            page_number=page_number,
            start_line=start + 1,
            end_line=end,
            event_type=event_type,
            organ=org_at_line.get(start),
            act_number=act_number,
            contract_number=contract_number,
            process_number=process_number,
            edital_number=edital_number,
            bidding_modality=bidding_match.group(1).upper() if bidding_match else None,
            bidding_number=bidding_match.group(2) if bidding_match else None,
            contractor=_contractor(block),
            cnpj=cnpj,
            object_text=object_text,
            value_brl=value_brl,
            signature_date=signature_match.group(1) if signature_match else None,
            source_url=source_url,
            source_sha256=source_sha256,
            excerpt_redacted=compact_excerpt,
            pii_redactions=redaction.total,
        ))
    return events


def chunk_redacted_text(text: str, *, max_chars: int = 1800, overlap_chars: int = 180) -> list[str]:
    if max_chars < 300 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("BAD_CHUNK_CONFIG")
    normalized = normalize_text(text)
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + max_chars)
        if end < len(normalized):
            split = normalized.rfind("\n", start, end)
            if split <= start + max_chars // 3:
                split = normalized.rfind(" ", start, end)
            if split > start:
                end = split
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(end - overlap_chars, start + 1)
    return chunks


class JournalPdfProcessor:
    def __init__(self, *, min_total_chars: int = 120, min_page_chars: int = 20, sparse_page_ratio_stop: float = 0.8):
        self.min_total_chars = min_total_chars
        self.min_page_chars = min_page_chars
        self.sparse_page_ratio_stop = sparse_page_ratio_stop

    @staticmethod
    def _reader(path: Path):
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - explicit runtime guard
            raise RuntimeError("STOP_DEPENDENCY_PYPDF") from exc
        return PdfReader(str(path))

    def extract_pages(self, path: str | Path) -> list[ExtractedPage]:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        reader = self._reader(path)
        pages: list[ExtractedPage] = []
        for idx, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                raise RuntimeError(f"STOP_PDF_TEXT_EXTRACTION_PAGE_{idx}") from exc
            text = normalize_text(text)
            pages.append(ExtractedPage(page_number=idx, text=text, char_count=len(text)))
        return pages

    def text_status(self, pages: list[ExtractedPage]) -> tuple[str, dict]:
        total = sum(p.char_count for p in pages)
        sparse = sum(1 for p in pages if p.char_count < self.min_page_chars)
        ratio = sparse / len(pages) if pages else 1.0
        metrics = {
            "pages": len(pages),
            "total_extracted_chars": total,
            "sparse_pages": sparse,
            "sparse_page_ratio": round(ratio, 4),
        }
        if not pages or total < self.min_total_chars or ratio >= self.sparse_page_ratio_stop:
            return "STOP_OCR_REQUIRED", metrics
        return "PASS_TEXT_EXTRACTION", metrics

    @staticmethod
    def stage_bronze(source_pdf: str | Path, bronze_path: str | Path) -> dict:
        source_pdf = Path(source_pdf)
        bronze_path = Path(bronze_path)
        source_hash = sha256_file(source_pdf)
        bronze_path.parent.mkdir(parents=True, exist_ok=True)
        if bronze_path.exists():
            existing_hash = sha256_file(bronze_path)
            if existing_hash != source_hash:
                raise RuntimeError("STOP_BRONZE_MUTATION_ATTEMPT")
            return {"status": "REUSED_IDENTICAL", "path": str(bronze_path), "sha256": source_hash}
        shutil.copyfile(source_pdf, bronze_path)
        copied_hash = sha256_file(bronze_path)
        if copied_hash != source_hash:
            raise RuntimeError("STOP_BRONZE_HASH_MISMATCH")
        return {"status": "COPIED_IMMUTABLE", "path": str(bronze_path), "sha256": source_hash}

    def process(
        self,
        pdf_path: str | Path,
        *,
        edition: int,
        publication_date: str | None,
        source_url: str | None,
        out_dir: str | Path,
        stage_bronze: bool = True,
        plan_reconciliation: bool = True,
    ) -> dict:
        pdf_path = Path(pdf_path)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        source_id = f"LIMEIRA_JO_{edition:05d}"
        source_hash = sha256_file(pdf_path)
        bronze_report = None
        if stage_bronze:
            bronze_report = self.stage_bronze(pdf_path, out_dir / "bronze" / f"{source_id}.pdf")

        pages = self.extract_pages(pdf_path)
        text_status, metrics = self.text_status(pages)
        manifest = {
            "software_contract": "JORNAL_OFICIAL_LIMEIRA_PDF_V01",
            "source_id": source_id,
            "edition": edition,
            "publication_date": publication_date,
            "source_url": source_url,
            "source_sha256": source_hash,
            "bronze": bronze_report,
            "text_extraction": {"status": text_status, **metrics},
            "privacy_rule": "Derived Silver/Gold/RAG persist redacted text only; original evidence stays in Bronze PDF.",
            "silver_pages": 0,
            "gold_events": 0,
            "rag_chunks": 0,
            "reconciliation_tasks": 0,
        }
        manifest_path = out_dir / "edition_manifest.json"
        if text_status != "PASS_TEXT_EXTRACTION":
            manifest["status"] = text_status
            self._write_json(manifest_path, manifest)
            return manifest

        silver_rows = []
        all_events: list[JournalEvent] = []
        rag_rows = []
        for page in pages:
            redaction = redact_personal_identifiers(page.text)
            organ = detect_organ(redaction.text.split("\n"))
            silver_rows.append({
                "source_id": source_id,
                "edition": edition,
                "publication_date": publication_date,
                "page_number": page.page_number,
                "source_sha256": source_hash,
                "organ_hint": organ,
                "text_redacted": redaction.text,
                "pii_redaction_counts": redaction.counts,
            })
            events = parse_events_from_page(
                page.text,
                edition=edition,
                publication_date=publication_date,
                page_number=page.page_number,
                source_url=source_url,
                source_sha256=source_hash,
            )
            all_events.extend(events)
            chunks = chunk_redacted_text(redaction.text)
            for chunk_index, chunk in enumerate(chunks, start=1):
                rag_rows.append({
                    "chunk_id": f"{source_id}_P{page.page_number:04d}_C{chunk_index:03d}",
                    "source_id": source_id,
                    "edition": edition,
                    "publication_date": publication_date,
                    "page_number": page.page_number,
                    "chunk_index": chunk_index,
                    "source_url": source_url,
                    "source_sha256": source_hash,
                    "organ_hint": organ,
                    "text": chunk,
                    "pii_minimized": True,
                })

        self._write_jsonl(out_dir / "pages_silver.jsonl", silver_rows)
        self._write_jsonl(out_dir / "events_gold.jsonl", [e.to_dict() for e in all_events])
        self._write_jsonl(out_dir / "chunks_rag.jsonl", rag_rows)
        reconciliation_tasks = []
        if plan_reconciliation:
            reconciliation_tasks = ReconciliationPlanner().plan_events([e.to_dict() for e in all_events])
            ReconciliationPlanner.write_jsonl(out_dir / "reconciliation_tasks.jsonl", reconciliation_tasks)
        manifest.update({
            "status": "PASS_DOCUMENT_PROCESSING",
            "silver_pages": len(silver_rows),
            "gold_events": len(all_events),
            "rag_chunks": len(rag_rows),
            "reconciliation_tasks": len(reconciliation_tasks),
        })
        self._write_json(manifest_path, manifest)
        return manifest

    @staticmethod
    def _write_json(path: Path, payload: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")

    @staticmethod
    def _write_jsonl(path: Path, rows: Iterable[dict]):
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                f.write("\n")
