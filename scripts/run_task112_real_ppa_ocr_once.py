#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pypdf import PdfReader  # noqa: E402
from robo_dados_publicos.research.ppa_2018_ocr import (  # noqa: E402
    ExactSourceClient,
    Task112Stop,
    bounded_excerpt,
    load_contract,
    normalize_ocr,
    render_and_ocr_page,
)

CONTRACT = ROOT / "config/task112_real_ppa_2018_2021_ocr.v1.json"
RUNTIME = ROOT / "runtime/task112"
RESULT = ROOT / "runtime/task112_result.json"


def canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return sha256(raw.encode("utf-8")).hexdigest()


def main() -> int:
    contract = load_contract(CONTRACT)
    source = contract["source"]
    document = contract["document"]

    RUNTIME.mkdir(parents=True, exist_ok=True)
    pdf_path = RUNTIME / "ppa-2018-2021.pdf"
    client = ExactSourceClient(
        initial_url=source["url"],
        allowed_host=source["allowed_host"],
        max_requests=source["max_http_requests_total"],
    )

    try:
        raw, final_url, content_type = client.get()
        if not raw.startswith(b"%PDF"):
            raise Task112Stop("TASK112_NOT_PDF_BYTES")
        pdf_path.write_bytes(raw)
        source_sha = sha256(raw).hexdigest()
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        if not (1 <= page_count <= document["max_pdf_pages"]):
            raise Task112Stop("TASK112_PAGE_COUNT_BOUND")

        extracted_text_chars = sum(len((page.extract_text() or "").strip()) for page in reader.pages)

        signal_norm = normalize_ocr(document["expected_signal"])
        law_norm = normalize_ocr(document["law_number"])
        signal_match = None
        law_match = None
        pages_scanned = 0

        for page in range(1, page_count + 1):
            page_result = render_and_ocr_page(pdf_path, page, RUNTIME)
            pages_scanned += 1
            text_norm = page_result["normalized_text"]
            if law_match is None and law_norm in text_norm:
                law_match = page_result
            if signal_match is None and signal_norm in text_norm:
                signal_match = page_result
            if law_match is not None and signal_match is not None:
                break

        if signal_match is None:
            status = "NO_MATCH_TASK112_EXPECTED_PLANNING_SIGNAL_NOT_FOUND"
        elif law_match is None:
            status = "PARTIAL_TASK112_SIGNAL_FOUND_LAW_IDENTITY_NOT_OCR_CONFIRMED"
        else:
            status = "PASS_TASK112_PRIMARY_PLANNING_EVIDENCE"

        result = {
            "schema": "TASK112_REAL_PPA_2018_2021_OCR_RESULT_V1",
            "task": "TASK_112_REAL_PPA_2018_2021_OCR",
            "status": status,
            "source": {
                "requested_url": source["url"],
                "final_url": final_url,
                "content_type": content_type,
                "source_bytes": len(raw),
                "source_sha256": source_sha,
                "request_count": len(client.request_log),
                "requests": client.request_log,
            },
            "document": {
                "period": document["period"],
                "law_number": document["law_number"],
                "page_count": page_count,
                "pypdf_extracted_text_chars": extracted_text_chars,
                "pages_ocr_scanned": pages_scanned,
            },
            "law_identity": None if law_match is None else {
                "page": law_match["page"],
                "coordinate_system": law_match["coordinate_system"],
                "rendered_page_sha256": law_match["rendered_page_sha256"],
                "ocr_tsv_sha256": law_match["ocr_tsv_sha256"],
                "confidence_count": law_match["confidence_count"],
                "confidence_min": law_match["confidence_min"],
                "confidence_max": law_match["confidence_max"],
                "confidence_mean": law_match["confidence_mean"],
                "excerpt": bounded_excerpt(law_match["raw_text"], document["law_number"]),
            },
            "planning_signal": None if signal_match is None else {
                "signal": document["expected_signal"],
                "page": signal_match["page"],
                "coordinate_system": signal_match["coordinate_system"],
                "rendered_page_sha256": signal_match["rendered_page_sha256"],
                "ocr_tsv_sha256": signal_match["ocr_tsv_sha256"],
                "confidence_count": signal_match["confidence_count"],
                "confidence_min": signal_match["confidence_min"],
                "confidence_max": signal_match["confidence_max"],
                "confidence_mean": signal_match["confidence_mean"],
                "excerpt": bounded_excerpt(signal_match["raw_text"], document["expected_signal"]),
            },
            "hard_boundaries": contract["hard_boundaries"],
            "retry_performed": False,
            "recurrence": False,
            "schedule": False,
            "future_execution_authorized": False,
        }
    except Task112Stop as exc:
        result = {
            "schema": "TASK112_REAL_PPA_2018_2021_OCR_RESULT_V1",
            "task": "TASK_112_REAL_PPA_2018_2021_OCR",
            "status": "STOP_TASK112",
            "error": str(exc),
            "source": {
                "requested_url": source["url"],
                "request_count": len(client.request_log),
                "requests": client.request_log,
            },
            "hard_boundaries": contract["hard_boundaries"],
            "retry_performed": False,
            "recurrence": False,
            "schedule": False,
            "future_execution_authorized": False,
        }

    result["result_canonical_sha256"] = canonical_sha256(result)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "request_count": result["source"]["request_count"],
        "result_canonical_sha256": result["result_canonical_sha256"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
