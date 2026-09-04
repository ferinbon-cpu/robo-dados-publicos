from __future__ import annotations

from typing import Any

from robo_dados_publicos.research.ppa_2018_ocr import bounded_excerpt, normalize_ocr


def ontology_candidates_for_page(
    *,
    page_result: dict[str, Any],
    lexical_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    normalized_text = page_result["normalized_text"]
    companions = [
        normalize_ocr(term)
        for term in lexical_contract.get("companion_context_terms") or []
    ]
    candidates: list[dict[str, Any]] = []
    limit = int((lexical_contract.get("future_live_gate") or {}).get("max_candidates_per_page", 20))

    for family, entries in (lexical_contract.get("families") or {}).items():
        for entry in entries:
            term = str(entry["term"])
            normalized_term = normalize_ocr(term)
            if normalized_term not in normalized_text:
                continue
            companion_hits = [item for item in companions if item and item in normalized_text]
            if entry.get("requires_companion") and not companion_hits:
                continue
            candidates.append(
                {
                    "family": family,
                    "term": term,
                    "normalized_term": normalized_term,
                    "strength": entry["strength"],
                    "requires_companion": entry["requires_companion"],
                    "companion_hits": companion_hits[:10],
                    "page": page_result["page"],
                    "coordinate_system": page_result["coordinate_system"],
                    "rendered_page_sha256": page_result["rendered_page_sha256"],
                    "ocr_tsv_sha256": page_result["ocr_tsv_sha256"],
                    "confidence_count": page_result["confidence_count"],
                    "confidence_min": page_result["confidence_min"],
                    "confidence_max": page_result["confidence_max"],
                    "confidence_mean": page_result["confidence_mean"],
                    "excerpt": bounded_excerpt(page_result["raw_text"], term),
                }
            )
            if len(candidates) >= limit:
                return candidates
    return candidates
