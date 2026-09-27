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
    render_and_ocr_page,
)
from robo_dados_publicos.research.ppa_2018_ontology_live import (  # noqa: E402
    ontology_candidates_for_page,
)
from robo_dados_publicos.research.ppa_2018_ontology_search import (  # noqa: E402
    load_and_validate_task113_contract,
)

SOURCE_URL = "https://www.limeira.sp.gov.br/sitenovo/downloads/0fa1a5cc5c9a1823fbf5436def00f01f.pdf"
SOURCE_SHA = "685a621a2f5fa8859e4b7f8518627c1523a2fbc5f3402ff48d4aa7573300113d"
LEXICAL = ROOT / "config/task113_ppa2018_ontology_lexical.v1.json"
RUNTIME = ROOT / "runtime/task114"
RESULT = ROOT / "runtime/task114_result.json"


def canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return sha256(raw.encode("utf-8")).hexdigest()


def main() -> int:
    load_and_validate_task113_contract(LEXICAL)
    lexical = json.loads(LEXICAL.read_text(encoding="utf-8"))

    RUNTIME.mkdir(parents=True, exist_ok=True)
    pdf_path = RUNTIME / "ppa-2018-2021.pdf"
    client = ExactSourceClient(
        initial_url=SOURCE_URL,
        allowed_host="www.limeira.sp.gov.br",
        max_requests=1,
    )

    try:
        raw, final_url, content_type = client.get()
        observed_sha = sha256(raw).hexdigest()
        if observed_sha != SOURCE_SHA:
            raise Task112Stop("TASK114_SOURCE_SHA_MISMATCH")
        if not raw.startswith(b"%PDF"):
            raise Task112Stop("TASK114_NOT_PDF_BYTES")
        pdf_path.write_bytes(raw)
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        if page_count != 80:
            raise Task112Stop("TASK114_PAGE_COUNT_DRIFT")

        candidates: list[dict] = []
        candidate_pages: set[int] = set()
        for page in range(1, page_count + 1):
            page_result = render_and_ocr_page(pdf_path, page, RUNTIME)
            page_candidates = ontology_candidates_for_page(
                page_result=page_result,
                lexical_contract=lexical,
            )
            if page_candidates:
                candidate_pages.add(page)
                candidates.extend(page_candidates)

        result = {
            "schema": "TASK114_PPA2018_ONTOLOGY_OCR_CANDIDATES_V1",
            "task": "TASK_114_ONTOLOGY_AWARE_PPA2018_OCR",
            "status": "CANDIDATES_FOUND" if candidates else "NO_CANDIDATES_FOUND",
            "source": {
                "url": SOURCE_URL,
                "final_url": final_url,
                "content_type": content_type,
                "source_sha256": observed_sha,
                "source_bytes": len(raw),
                "request_count": len(client.request_log),
                "requests": client.request_log,
            },
            "document": {
                "period": "2018-2021",
                "law_number": "5.947",
                "page_count": page_count,
                "document_identity_evidence": "docs/evidence/TASK_112_REAL_PPA_OCR_RESULT_0.8.0.json",
            },
            "search_contract": "config/task113_ppa2018_ontology_lexical.v1.json",
            "candidate_count": len(candidates),
            "candidate_page_count": len(candidate_pages),
            "candidate_pages": sorted(candidate_pages),
            "candidates": candidates,
            "promotion": {
                "primary_planning_status_changed": False,
                "policy_identity_created": False,
                "financial_identity_created": False,
                "transaction_execution_identity_created": False,
                "implementation_proven": False,
                "causal_effect_created": False,
            },
            "retry_performed": False,
            "recurrence": False,
            "schedule": False,
            "future_execution_authorized": False,
        }
    except Task112Stop as exc:
        result = {
            "schema": "TASK114_PPA2018_ONTOLOGY_OCR_CANDIDATES_V1",
            "task": "TASK_114_ONTOLOGY_AWARE_PPA2018_OCR",
            "status": "STOP_TASK114",
            "error": str(exc),
            "source": {
                "url": SOURCE_URL,
                "request_count": len(client.request_log),
                "requests": client.request_log,
            },
            "promotion": {
                "primary_planning_status_changed": False,
                "policy_identity_created": False,
                "financial_identity_created": False,
                "transaction_execution_identity_created": False,
                "implementation_proven": False,
                "causal_effect_created": False,
            },
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
        "candidate_count": result.get("candidate_count", 0),
        "candidate_pages": result.get("candidate_pages", []),
        "request_count": result["source"]["request_count"],
        "result_canonical_sha256": result["result_canonical_sha256"],
    }, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
