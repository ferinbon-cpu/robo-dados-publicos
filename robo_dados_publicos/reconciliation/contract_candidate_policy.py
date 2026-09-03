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
    """Parse exactly one slash-form contract reference as (number, year).

    Leading zeroes and trailing punctuation are presentation differences only:
    `09/2025.` and `9/2025` normalize to the same reference.  The parser is
    intentionally fail-closed: zero or multiple slash-form references return None.
    Filenames such as `contrato_09_2025.pdf` are not accepted as contract-number
    evidence because they do not expose the documentary `number/year` syntax.
    """

    matches = re.findall(r"(?<!\d)(\d{1,9})\s*/\s*(\d{4})(?!\d)", str(value or ""))
    refs = {(int(number), int(year)) for number, year in matches}
    return next(iter(refs)) if len(refs) == 1 else None


def fail_closed_contract_candidate_rows(rows: list[list[str]], keys: dict) -> list[dict]:
    """Return municipal contract candidates only after available strong keys agree.

    Contract numbers are not globally unique across municipal document classes. A
    number/year hit is therefore only a search result, not enough to promote a
    candidate when the originating task already carries a stronger corroborator.

    Rules are intentionally asymmetric and fail-closed:

    * when a contract key is present, the same normalized number/year must occur in
      one individual result cell;
    * `09/2025.`, `09/2025` and `9/2025` are the same documentary reference;
    * filenames or unrelated text containing a numeric stem never count as a
      contract-number match;
    * when an expected CNPJ is present in the task, the same row must expose it in
      one individual cell;
    * otherwise, when supplier is available alongside contract, supplier must agree;
    * CNPJ is never reconstructed across concatenated cells;
    * object-text similarity is never used to promote a candidate;
    * CNPJ-only promotion is allowed only when the task itself has no contract key.
    """

    contract_value = keys.get("contract_number")
    expected_contract = _contract_reference(contract_value)
    contract_key_present = bool(str(contract_value or "").strip())
    expected_cnpj = _digits(keys.get("cnpj"))
    supplier = _ascii(keys.get("contractor"))

    out: list[dict] = []
    for idx, cells in enumerate(rows):
        text = _ascii(" | ".join(cells))
        signals: list[str] = []

        contract_match = False
        if expected_contract is not None:
            contract_match = any(_contract_reference(cell) == expected_contract for cell in cells)
            if contract_match:
                signals.append("CONTRACT_NUMBER_YEAR_NORMALIZED")
        elif contract_key_present:
            # Unknown contract syntax stays fail-closed rather than falling back to
            # a loose digit-stem search across the whole row.
            contract_match = False

        cnpj_match = bool(expected_cnpj and any(expected_cnpj in _digits(cell) for cell in cells))
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
        if expected_cnpj and not cnpj_match:
            continue

        # Without CNPJ, a known supplier must corroborate a contract-number hit.
        if not expected_cnpj and contract_key_present and supplier and not supplier_match:
            continue

        # A task with neither a proven contract reference nor expected CNPJ cannot
        # produce a candidate from supplier-name text alone.
        if not contract_match and not cnpj_match:
            continue

        out.append({"row_index": idx, "cells": cells, "match_signals": signals})

    return out


def install_fail_closed_contract_candidate_policy(resolver_class) -> None:
    """Install the candidate policy on the existing resolver class deterministically."""

    resolver_class._candidate_rows = staticmethod(fail_closed_contract_candidate_rows)
