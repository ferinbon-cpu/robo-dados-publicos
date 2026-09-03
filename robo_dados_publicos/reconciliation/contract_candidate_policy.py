from __future__ import annotations

import re


def _ascii(value) -> str:
    import unicodedata

    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def _digits(value) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _contract_stem(value) -> str | None:
    if not value:
        return None
    match = re.search(r"\d+", str(value))
    return match.group(0) if match else str(value).strip() or None


def fail_closed_contract_candidate_rows(rows: list[list[str]], keys: dict) -> list[dict]:
    """Return municipal contract candidates only after available strong keys agree.

    Contract numbers are not globally unique across municipal document classes.  A
    `number/year` hit is therefore only a search result, not enough to promote a
    candidate when the originating task already carries a stronger corroborator.

    Rules are intentionally asymmetric and fail-closed:

    * contract full or contract-stem+year remains the primary documentary signal;
    * when an expected CNPJ is present in the task, the row must expose that CNPJ;
    * otherwise, when a supplier name is present alongside a contract key, the row
      must expose that supplier name;
    * CNPJ is matched inside individual cells, never across concatenated table cells;
    * object-text similarity is never used to promote a candidate.

    This function deliberately accepts the same `(rows, keys)` signature as the
    historical resolver hook so existing deterministic call sites remain stable.
    """

    contract_raw = _ascii(keys.get("contract_number"))
    stem = _ascii(_contract_stem(keys.get("contract_number")))
    expected_cnpj = _digits(keys.get("cnpj"))
    supplier = _ascii(keys.get("contractor"))
    year = str(keys.get("year") or "")

    out: list[dict] = []
    for idx, cells in enumerate(rows):
        joined = " | ".join(cells)
        text = _ascii(joined)
        signals: list[str] = []

        if contract_raw and contract_raw in text:
            signals.append("CONTRACT_FULL")
        elif stem and re.search(rf"(?<!\d){re.escape(stem)}(?!\d)", text) and (not year or year in text):
            signals.append("CONTRACT_STEM_PLUS_YEAR")

        cnpj_match = bool(
            expected_cnpj
            and any(expected_cnpj in _digits(cell) for cell in cells)
        )
        if cnpj_match:
            signals.append("CNPJ")

        supplier_match = bool(supplier and supplier in text)
        if supplier_match:
            signals.append("SUPPLIER_NAME")

        contract_signal = bool({"CONTRACT_FULL", "CONTRACT_STEM_PLUS_YEAR"} & set(signals))

        # A supplied CNPJ is a stronger key and must agree.  This is the critical
        # fail-closed guard exposed by TASK 081: number 9/2025 occurred in multiple
        # unrelated municipal document classes, while neither row exposed the
        # originating event's CNPJ.
        if expected_cnpj and not cnpj_match:
            continue

        # If CNPJ is unavailable but the task has both contract and supplier, do
        # not promote a number/year collision with a different supplier.
        if not expected_cnpj and supplier and contract_raw and not supplier_match:
            continue

        # Preserve the historical ability to use an exact CNPJ-only row for tasks
        # whose public search was supplier-based, while never accepting supplier
        # name alone as identity evidence.
        if not contract_signal and not cnpj_match:
            continue

        out.append({"row_index": idx, "cells": cells, "match_signals": signals})

    return out


def install_fail_closed_contract_candidate_policy(resolver_class) -> None:
    """Install the candidate policy on the existing resolver class deterministically."""

    resolver_class._candidate_rows = staticmethod(fail_closed_contract_candidate_rows)
