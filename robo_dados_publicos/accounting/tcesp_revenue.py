from __future__ import annotations

import csv
import hashlib
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task186_tcesp_revenue_2026.v1.json"


class Task186RevenueStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task186RevenueStop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _amount(value: str) -> str:
    text = str(value or "").strip()
    _stop(bool(text), "TASK186_REVENUE_AMOUNT_EMPTY")
    try:
        parsed = Decimal(text.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise Task186RevenueStop("TASK186_REVENUE_AMOUNT_INVALID") from exc
    return format(parsed, "f")


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK186_TCESP_REVENUE_2026_V1", "TASK186_REVENUE_SCHEMA")
    _stop(obj.get("mode") == "OWNER_SUPPLIED_OFFICIAL_ZIP_OFFLINE", "TASK186_REVENUE_MODE")
    _stop(obj["source"]["fiscal_year"] == 2026, "TASK186_REVENUE_YEAR")
    _stop(obj["source"]["months_expected"] == [1, 2, 3, 4, 5, 6, 7], "TASK186_REVENUE_MONTHS")
    _stop(obj["remote_effects"]["source_network"] is False, "TASK186_REVENUE_NETWORK")
    return obj


def parse_csv_bytes(payload: bytes, *, contract_path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, str]]:
    contract = load_contract(contract_path)
    try:
        text = payload.decode(contract["source"]["csv_encoding"])
    except UnicodeDecodeError as exc:
        raise Task186RevenueStop("TASK186_REVENUE_ENCODING") from exc
    reader = csv.DictReader(io.StringIO(text), delimiter=contract["source"]["delimiter"])
    _stop(reader.fieldnames == contract["source"]["required_headers"], "TASK186_REVENUE_HEADERS")
    rows = [dict(row) for row in reader]
    _stop(bool(rows), "TASK186_REVENUE_EMPTY")
    ids: set[str] = set()
    observed_months: set[int] = set()
    for row in rows:
        _stop(all(str(row.get(h) or "").strip() for h in contract["source"]["required_headers"]), "TASK186_REVENUE_REQUIRED_FIELD")
        rid = str(row["id_rec_arrec_detalhe"]).strip()
        _stop(rid not in ids, "TASK186_REVENUE_DUPLICATE_ID")
        ids.add(rid)
        _stop(row["ano_exercicio"] == "2026", "TASK186_REVENUE_ROW_YEAR")
        _stop(row["ds_municipio"] == "Limeira", "TASK186_REVENUE_MUNICIPALITY")
        month = int(row["mes_referencia"])
        _stop(month in contract["source"]["months_expected"], "TASK186_REVENUE_MONTH")
        observed_months.add(month)
        _amount(row["vl_arrecadacao"])
    _stop(sorted(observed_months) == contract["source"]["months_expected"], "TASK186_REVENUE_MONTH_COVERAGE")
    return rows


def normalize_revenue_row(row: Mapping[str, Any]) -> dict[str, Any]:
    rid = str(row.get("id_rec_arrec_detalhe") or "").strip()
    _stop(bool(rid), "TASK186_REVENUE_ID")
    month = int(row["mes_referencia"])
    application_fixed = str(row["ds_cd_aplicacao_fixo"]).strip()
    application_variable = str(row["ds_cd_aplicacao_variavel"]).strip()
    revenue_d2 = str(row["ds_dd2"]).strip()
    revenue_d3 = str(row["ds_d3"]).strip()
    revenue_type = str(row["ds_tipo"]).strip()
    semantic_text = " | ".join(
        [application_fixed, application_variable, revenue_d2, revenue_d3, revenue_type]
    ).upper()
    education = any(
        token in semantic_text
        for token in (
            "EDUCAÇÃO",
            "ENSINO FUNDAMENTAL",
            "ENSINO MÉDIO",
            "PNAE",
            "PNATE",
            "SALÁRIO EDUCAÇÃO",
        )
    )
    fundeb = "FUNDEB" in semantic_text
    eti = "FOMENTO A MATRÍCULAS ETI" in application_variable.upper()
    direct_eti_transfer = eti and revenue_d2.startswith("17155300")
    eti_financial_remuneration = eti and revenue_d2.startswith("13210100")
    raw = {str(k): str(v or "") for k, v in row.items()}
    source_record_hash = _sha(raw)
    observation_id = f"TCESP_REV_2026_{rid}"
    return {
        "revenue_observation_id": observation_id,
        "source_record_id": rid,
        "fiscal_year": 2026,
        "revenue_month": month,
        "month_name": str(row["mes_ref_extenso"]).strip(),
        "municipality": "Limeira",
        "entity_name": str(row["ds_orgao"]).strip(),
        "government_power": str(row["ds_poder"]).strip(),
        "funding_source": str(row["ds_fonte_recurso"]).strip(),
        "application_fixed": application_fixed,
        "application_variable": application_variable,
        "revenue_category": str(row["ds_categoria"]).strip(),
        "revenue_subcategory": str(row["ds_subcategoria"]).strip(),
        "revenue_source": str(row["ds_fonte"]).strip(),
        "revenue_d1": str(row["ds_d1"]).strip(),
        "revenue_d2": revenue_d2,
        "revenue_d3": revenue_d3,
        "revenue_type": revenue_type,
        "amount_brl": _amount(str(row["vl_arrecadacao"])),
        "education_application": education,
        "fundeb_classification": fundeb,
        "eti_classification": eti,
        "eti_direct_transfer": direct_eti_transfer,
        "eti_financial_remuneration": eti_financial_remuneration,
        "evidence_status": "OFFICIAL_TCESP_REVENUE_RECORD",
        "source_record_hash": source_record_hash,
    }


def normalize_csv_bytes(payload: bytes, *, contract_path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    return [normalize_revenue_row(row) for row in parse_csv_bytes(payload, contract_path=contract_path)]
