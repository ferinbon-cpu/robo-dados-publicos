from __future__ import annotations

import re
import unicodedata


def _ascii(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def _digits(value) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _contract_reference(value) -> tuple[int, int] | None:
    """Parse exactly one standalone slash-form contract reference as (number, year).

    Leading zeroes and trailing punctuation are presentation differences only:
    `09/2025.` and `9/2025` normalize to the same reference. The parser is
    intentionally fail-closed: zero or multiple slash-form references return None.
    A match embedded in a date (`17/03/2025`), dotted process number
    (`29.185/2025`) or underscore filename (`contrato_09_2025.pdf`) is rejected.
    Surrounding documentary text such as `Contrato 09/2025 - objeto` is allowed.
    """

    matches = re.findall(
        r"(?<![\d./_])(\d{1,9})\s*/\s*(\d{4})(?!\d)",
        str(value or ""),
    )
    refs = {(int(number), int(year)) for number, year in matches}
    return next(iter(refs)) if len(refs) == 1 else None


def _cell_has_exact_cnpj(cell, expected_cnpj: str) -> bool:
    """Require one individual cell to normalize to exactly the expected CNPJ."""

    return bool(expected_cnpj and _digits(cell) == expected_cnpj)


def fail_closed_contract_candidate_rows(rows: list[list[str]], keys: dict) -> list[dict]:
    """Return municipal contract candidates only after available strong keys agree.

    Contract numbers are not globally unique across municipal document classes. A
    number/year hit is therefore only a search result, not enough to promote a
    candidate when the originating task already carries a stronger corroborator.

    Rules are intentionally asymmetric and fail-closed:

    * when a contract key is present, the same normalized standalone number/year
      must occur in one individual result cell;
    * dates, dotted process numbers and underscore filenames never substitute for a
      contract-number cell;
    * `09/2025.`, `09/2025` and `9/2025` are the same documentary reference;
    * a normalized full-reference hit preserves the legacy `CONTRACT_FULL` signal
      used by the evidence assembler and also emits the explicit normalization signal;
    * when an expected CNPJ is present in the task, it must be a valid 14-digit key
      and one individual result cell must normalize exactly to those 14 digits;
    * whenever a supplier key is also present, supplier mismatch blocks promotion;
    * CNPJ is never reconstructed across cells or accepted as a substring of a cell;
    * object-text similarity is never used to promote a candidate;
    * CNPJ-only promotion is allowed only when the task itself has no contract key,
      and still requires supplier agreement when a supplier key is available.
    """

    contract_value = keys.get("contract_number")
    expected_contract = _contract_reference(contract_value)
    contract_key_present = bool(str(contract_value or "").strip())

    cnpj_value = keys.get("cnpj")
    cnpj_key_present = bool(str(cnpj_value or "").strip())
    expected_cnpj = _digits(cnpj_value)
    if cnpj_key_present and len(expected_cnpj) != 14:
        return []

    supplier = _ascii(keys.get("contractor"))

    out: list[dict] = []
    for idx, cells in enumerate(rows):
        text = _ascii(" | ".join(cells))
        signals: list[str] = []

        contract_match = False
        if expected_contract is not None:
            contract_match = any(_contract_reference(cell) == expected_contract for cell in cells)
            if contract_match:
                # Backward compatibility is semantic, not permissive: CONTRACT_FULL
                # now means a full slash-form number/year reference proven after
                # canonical normalization in one individual result cell.
                signals.extend(["CONTRACT_FULL", "CONTRACT_NUMBER_YEAR_NORMALIZED"])
        elif contract_key_present:
            # Unknown contract syntax stays fail-closed rather than falling back to
            # a loose digit-stem search across the whole row.
            contract_match = False

        cnpj_match = bool(
            expected_cnpj and any(_cell_has_exact_cnpj(cell, expected_cnpj) for cell in cells)
        )
        if cnpj_match:
            signals.append("CNPJ")

        supplier_match = bool(supplier and supplier in text)
        if supplier_match:
            signals.append("SUPPLIER_NAME")

        # If the task carries a contract key, contract agreement is mandatory.
        if contract_key_present and not contract_match:
            continue

        # If the task carries CNPJ, it is a mandatory corroborator, not an
        # alternative path that can override a mismatched/missing contract.
        if cnpj_key_present and not cnpj_match:
            continue

        # A known supplier is also a corroborator. Contradictory supplier evidence
        # stays fail-closed even for a CNPJ-only task.
        if supplier and not supplier_match:
            continue

        # A task with neither a proven contract reference nor expected CNPJ cannot
        # produce a candidate from supplier-name text alone.
        if not contract_match and not cnpj_match:
            continue

        out.append({"row_index": idx, "cells": cells, "match_signals": signals})

    return out
