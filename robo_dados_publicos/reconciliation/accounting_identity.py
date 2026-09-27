"""Offline, scoped accounting identity. Never attributes expenditure to a purchase."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Mapping, Sequence


class AccountingIdentityStop(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AccountingIdentityStop(code)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True, order=True)
class CommitmentKey:
    municipality: str
    entity: str
    original_year: int
    number: str

    def __post_init__(self) -> None:
        require(bool(self.municipality and self.entity), "MISSING_ACCOUNTING_SCOPE")
        require(self.municipality == self.municipality.strip(), "NON_CANONICAL_SCOPE")
        require(self.entity == self.entity.strip(), "NON_CANONICAL_SCOPE")
        require(type(self.original_year) is int and 1900 <= self.original_year <= 2099,
                "INVALID_ORIGINAL_YEAR")
        require(isinstance(self.number, str) and bool(re.fullmatch(r"[1-9][0-9]*", self.number)),
                "NON_CANONICAL_COMMITMENT_NUMBER")

    def as_dict(self) -> dict:
        return {"municipality": self.municipality, "entity": self.entity,
                "original_year": self.original_year, "number": self.number}


def row_key(row: Mapping[str, str]) -> CommitmentKey:
    """Only the observed TCE number-year syntax; no digit stripping or year guessing."""
    number = str(row.get("nr_empenho") or "").strip()
    match = re.fullmatch(r"([0-9]+)-([12][0-9]{3})", number)
    require(match is not None, "UNSUPPORTED_COMMITMENT_SYNTAX")
    return CommitmentKey(
        str(row.get("ds_municipio") or "").strip(),
        str(row.get("ds_orgao") or "").strip(),
        int(match[2]), str(int(match[1])),
    )


def supplier_fingerprint(row: Mapping[str, str]) -> str:
    """Hash the raw supplier field for consistency checks without persisting the identifier."""
    value = str(row.get("identificador_despesa") or "").strip()
    require(bool(value), "MISSING_SUPPLIER_TOKEN")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


STAGES = {
    "Empenhado": ("COMMITMENT", None),
    "Reforço": ("COMMITMENT", "REINFORCEMENT"),
    "Anulação": ("REVERSAL", "UNSPECIFIED_STAGE"),
    "Valor Liquidado": ("LIQUIDATION", None),
    "Valor Pago": ("PAYMENT", None),
}


def index_rows(rows: Sequence[Mapping[str, str]]) -> dict[CommitmentKey, list[dict]]:
    require(bool(rows), "EMPTY_ACCOUNTING_INPUT")
    index: dict[CommitmentKey, list[dict]] = defaultdict(list)
    record_ids: set[str] = set()
    for row in rows:
        official_id = str(row.get("id_despesa_detalhe") or "").strip()
        require(bool(re.fullmatch(r"[0-9]+", official_id)), "INVALID_OFFICIAL_DETAIL_ID")
        require(official_id not in record_ids, "DUPLICATE_OFFICIAL_DETAIL_ID")
        record_ids.add(official_id)
        key = row_key(row)
        stage = str(row.get("tp_despesa") or "").strip()
        require(stage in STAGES, "UNKNOWN_ACCOUNTING_STAGE")
        ledger_year = str(row.get("ano_exercicio") or "").strip()
        month = str(row.get("mes_referencia") or "").strip()
        require(bool(re.fullmatch(r"[12][0-9]{3}", ledger_year)), "INVALID_LEDGER_YEAR")
        require(month.isdigit() and 1 <= int(month) <= 12, "INVALID_REFERENCE_MONTH")
        require(key.original_year <= int(ledger_year), "COMMITMENT_AFTER_LEDGER_YEAR")
        index[key].append({
            "official_detail_id": official_id,
            "ledger_year": int(ledger_year), "reference_month": int(month),
            "source_stage": stage, "stage": STAGES[stage][0],
            "modifier": STAGES[stage][1],
            "_supplier_fingerprint": supplier_fingerprint(row),
            "source_row_sha256": digest(dict(row)),
        })
    for observations in index.values():
        require(len({r["_supplier_fingerprint"] for r in observations}) == 1,
                "CONFLICTING_SUPPLIER_WITHIN_SCOPED_COMMITMENT")
        observations.sort(key=lambda r: int(r["official_detail_id"]))
    return dict(index)


def resolve_accounting_cohort(
    index: Mapping[CommitmentKey, list[dict]], key: CommitmentKey,
) -> dict:
    require(isinstance(key, CommitmentKey), "EXPLICIT_SCOPED_KEY_REQUIRED")
    observations = index.get(key, [])
    public_observations = [
        {field: value for field, value in observation.items() if not field.startswith("_")}
        for observation in observations
    ]
    return {
        "key": key.as_dict(),
        "accounting_status": "OBSERVED_SCOPED_COHORT" if observations else "UNRESOLVED",
        "observations": public_observations,
        "procurement_identity": "UNRESOLVED",
        "reason": "MISSING_OFFICIAL_PROCUREMENT_TO_COMMITMENT_WITNESS",
        "payment_attribution_authorized": False,
        "individual_liquidation_payment_pairing": "UNRESOLVED",
        "event_date_semantics": "NOT_INFERRED_FROM_DT_EMISSAO_DESPESA",
        "amount_allocation": "NOT_CALCULATED",
    }


def namespace_collisions(index: Mapping[CommitmentKey, list[dict]]) -> list[dict]:
    unscoped: dict[tuple[str, int, str], set[str]] = defaultdict(set)
    for key in index:
        unscoped[(key.municipality, key.original_year, key.number)].add(key.entity)
    return [
        {"municipality": k[0], "original_year": k[1], "number": k[2], "entities": sorted(v)}
        for k, v in sorted(unscoped.items()) if len(v) > 1
    ]
