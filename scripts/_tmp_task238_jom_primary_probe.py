from __future__ import annotations

# Ephemeral read-only probe. This comment intentionally triggers the corrected
# branch workflow after PYTHONPATH was fixed; it does not alter probe semantics.
import argparse
import hashlib
import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from robo_dados_publicos.operational.bootstrap_adapters import JornalSourceAdapter


TARGETS = {
    7142: {"year": 2025, "month": 12, "trigger": "08/2025"},
    7151: {"year": 2026, "month": 1, "trigger": "08/2025"},
    7168: {"year": 2026, "month": 1, "trigger": "formação"},
}

ALLOWED_HOSTS = ["ecrie.com.br", "www.limeira.sp.gov.br", "limeira.sp.gov.br"]
MAXIMUM_BYTES = 80_000_000

SEARCH_TERMS = [
    "08/2025",
    "formação",
    "Linguagens e Tecnologias",
    "Linguagens",
    "Tecnologias",
    "PSS 04/2025",
    "Resolução SME",
    "Resolução nº 08",
    "Resolução 08/2025",
    "primeiro semestre",
    "parágrafo 5º",
    "Secretaria Municipal de Educação",
]


def norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"\s*/\s*", "/", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def excerpt(text: str, needle: str, radius: int = 420) -> str:
    ntext = norm(text)
    nneedle = norm(needle)
    at = ntext.find(nneedle)
    if at < 0:
        return ""
    start = max(0, at - radius)
    end = min(len(ntext), at + len(nneedle) + radius)
    return ntext[start:end]


def extract_pdf(data: bytes) -> tuple[int, list[dict], list[str]]:
    reader = PdfReader(BytesIO(data), strict=False)
    pages = []
    errors = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # item-local and fail-closed in output
            text = ""
            errors.append(f"page_{index}:{type(exc).__name__}:{exc}")
        pages.append({"pdf_page": index, "text": text})
    return len(reader.pages), pages, errors


def discover_targets(adapter: JornalSourceAdapter) -> tuple[dict[int, dict], dict]:
    rows_by_edition: dict[int, dict] = {}
    telemetry = {}
    for year, month in ((2025, 12), (2026, 1)):
        family = {"year": year, "month": month, "allowed_hosts": ALLOWED_HOSTS}
        rows, tel = adapter.discover(family, maximum_pages=8)
        telemetry[f"{year:04d}-{month:02d}"] = tel
        for row in rows:
            edition = int(row["edition"])
            if edition in TARGETS:
                rows_by_edition[edition] = row
    return rows_by_edition, telemetry


def inspect_one(adapter: JornalSourceAdapter, edition: int, row: dict) -> dict:
    out = {
        "edition": edition,
        "publication_date": row.get("publication_date"),
        "document_url": row.get("url"),
        "source_page_url": row.get("source_page_url"),
        "trigger": TARGETS[edition]["trigger"],
        "status": "PENDING",
    }
    try:
        data, fetch = adapter.get(row["url"], maximum_bytes=MAXIMUM_BYTES)
        out["fetch"] = fetch
        out["bytes"] = len(data)
        out["sha256"] = hashlib.sha256(data).hexdigest()
        if len(data) > MAXIMUM_BYTES:
            out["status"] = "STOP_OVERSIZE"
            return out
        if not data.startswith(b"%PDF"):
            out["status"] = "STOP_NOT_PDF_MAGIC"
            return out
        page_count, pages, extraction_errors = extract_pdf(data)
        out["pdf_page_count"] = page_count
        out["extraction_errors"] = extraction_errors[:50]
        hits = []
        for term in SEARCH_TERMS:
            for page in pages:
                if norm(term) in norm(page["text"]):
                    hits.append(
                        {
                            "term": term,
                            "pdf_page": page["pdf_page"],
                            "excerpt_normalized": excerpt(page["text"], term),
                            "page_text": page["text"][:20000],
                        }
                    )
        out["hits"] = hits
        trigger_hits = [h for h in hits if norm(h["term"]) == norm(TARGETS[edition]["trigger"])]
        out["trigger_hit_count"] = len(trigger_hits)
        out["status"] = "PASS_PRIMARY_INSPECTION" if not extraction_errors else "PASS_WITH_PAGE_EXTRACTION_ERRORS"
        return out
    except Exception as exc:
        out["status"] = "STOP_FETCH_OR_EXTRACT"
        out["error"] = f"{type(exc).__name__}:{exc}"
        return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    adapter = JornalSourceAdapter()
    result = {
        "schema": "TASK238_JOM_PRIMARY_PROBE_WAVE3_V1",
        "mode": "READ_ONLY_EPHEMERAL_GITHUB_ACTIONS_PROBE",
        "target_editions": sorted(TARGETS),
        "maximum_bytes_per_document": MAXIMUM_BYTES,
        "drive_write": False,
        "repository_write": False,
        "absence_inference_allowed": False,
    }
    try:
        rows, telemetry = discover_targets(adapter)
        result["discovery_telemetry"] = telemetry
        result["discovered_target_editions"] = sorted(rows)
        missing = sorted(set(TARGETS) - set(rows))
        result["missing_target_editions"] = missing
        inspections = []
        for edition in sorted(TARGETS):
            if edition not in rows:
                inspections.append({"edition": edition, "status": "STOP_TARGET_NOT_DISCOVERED"})
            else:
                inspections.append(inspect_one(adapter, edition, rows[edition]))
        result["inspections"] = inspections
        statuses = [x["status"] for x in inspections]
        result["status"] = (
            "PASS_PROBE_ALL_TARGETS_INSPECTED"
            if all(s.startswith("PASS_") for s in statuses)
            else "PARTIAL_PROBE_TARGET_FAILURE"
        )
    except Exception as exc:
        result["status"] = "STOP_DISCOVERY_OR_RUNTIME"
        result["error"] = f"{type(exc).__name__}:{exc}"

    target = out_dir / "task238_jom_primary_probe_wave3.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(target)}, ensure_ascii=False))
    # Preserve the report even when the probe is partial; the workflow remains
    # successful so artifact upload always occurs. Evidence semantics stay in JSON.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
