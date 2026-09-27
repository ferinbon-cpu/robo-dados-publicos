from __future__ import annotations

import json
import math
import unicodedata
from pathlib import Path
from typing import Any


class Task166Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task166Stop(code)


def fold(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_record(record: dict[str, Any], expected_cnpj: str) -> dict[str, Any]:
    org = record.get("orgaoEntidade") or {}
    unit = record.get("unidadeOrgao") or {}
    cnpj = str(org.get("cnpj") or record.get("cnpj") or "")
    _stop(cnpj == expected_cnpj, "TASK166_ENTITY_IDENTITY_MISMATCH")

    return {
        "anoCompra": record.get("anoCompra"),
        "sequencialCompra": record.get("sequencialCompra"),
        "numeroControlePNCP": record.get("numeroControlePNCP"),
        "processo": record.get("processo"),
        "numeroCompra": record.get("numeroCompra"),
        "objetoCompra": record.get("objetoCompra"),
        "valorTotalEstimado": _num(record.get("valorTotalEstimado")),
        "valorTotalHomologado": _num(record.get("valorTotalHomologado")),
        "dataPublicacaoPncp": record.get("dataPublicacaoPncp"),
        "modalidadeId": record.get("modalidadeId"),
        "modalidadeNome": record.get("modalidadeNome"),
        "situacaoCompraId": record.get("situacaoCompraId"),
        "situacaoCompraNome": record.get("situacaoCompraNome"),
        "cnpj": cnpj,
        "razaoSocial": org.get("razaoSocial"),
        "municipioNome": unit.get("municipioNome"),
        "ufSigla": unit.get("ufSigla"),
    }


def scan_page(payload: dict[str, Any], config: dict[str, Any], requested_page: int) -> dict[str, Any]:
    _stop(isinstance(payload, dict), "TASK166_PAYLOAD_NOT_OBJECT")
    data = payload.get("data")
    _stop(isinstance(data, list), "TASK166_DATA_NOT_LIST")

    total_records = payload.get("totalRegistros")
    total_pages = payload.get("totalPaginas")
    page_number = payload.get("numeroPagina")
    remaining = payload.get("paginasRestantes")

    _stop(isinstance(total_records, int) and total_records >= 0, "TASK166_TOTAL_RECORDS")
    _stop(isinstance(total_pages, int) and total_pages >= 0, "TASK166_TOTAL_PAGES")
    _stop(page_number == requested_page, "TASK166_PAGE_IDENTITY")
    _stop(total_pages <= config["source"]["maxPaginas"], "TASK166_PAGE_CAP")

    records = [normalize_record(x, config["source"]["cnpj"]) for x in data]
    expected_modality = config["source"]["codigoModalidadeContratacao"]
    for rec in records:
        if rec["modalidadeId"] is not None:
            _stop(rec["modalidadeId"] == expected_modality, "TASK166_MODALITY_IDENTITY")

    explicit_terms = [fold(x) for x in config["explicit_eiti_terms"]]
    edu_terms = [fold(x) for x in config["education_terms"]]
    targets = []
    explicit_hits = []
    education_hits = []

    for rec in records:
        obj = fold(rec.get("objetoCompra"))
        proc = fold(rec.get("processo"))
        if any(term in obj for term in explicit_terms):
            explicit_hits.append(rec)
        if any(term in obj for term in edu_terms):
            education_hits.append(rec)

        for target in config["targets"]:
            process_ok = target.get("processo") is None or proc == fold(target["processo"])
            object_ok = fold(target["object_contains"]) in obj
            expected_value = target.get("estimated_value_brl")
            actual_value = rec.get("valorTotalEstimado")
            value_ok = expected_value is None or (
                actual_value is not None and math.isclose(actual_value, float(expected_value), rel_tol=0.0, abs_tol=0.01)
            )
            if process_ok and object_ok and value_ok:
                targets.append({"target_id": target["id"], "record": rec})

    return {
        "requested_page": requested_page,
        "reported_page": page_number,
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "paginasRestantes": remaining,
        "record_count": len(records),
        "records": records,
        "target_hits": targets,
        "explicit_eiti_hits": explicit_hits,
        "education_hits": education_hits,
    }


def combine_pages(pages: list[dict[str, Any]]) -> dict[str, Any]:
    _stop(bool(pages), "TASK166_NO_PAGES")
    total_pages = pages[0]["totalPaginas"]
    total_records = pages[0]["totalRegistros"]
    _stop(all(x["totalPaginas"] == total_pages for x in pages), "TASK166_TOTAL_PAGES_DRIFT")
    _stop(all(x["totalRegistros"] == total_records for x in pages), "TASK166_TOTAL_RECORDS_DRIFT")
    _stop(len(pages) == total_pages, "TASK166_INCOMPLETE_PAGINATION")
    _stop([x["requested_page"] for x in pages] == list(range(1, total_pages + 1)), "TASK166_PAGE_SEQUENCE")

    records = [r for p in pages for r in p["records"]]
    _stop(len(records) == total_records, "TASK166_RECORD_COUNT_MISMATCH")

    targets = [h for p in pages for h in p["target_hits"]]
    explicit = [r for p in pages for r in p["explicit_eiti_hits"]]
    education = [r for p in pages for r in p["education_hits"]]

    return {
        "status": "EXHAUSTIVE_COMPLETE",
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "pages_scanned": list(range(1, total_pages + 1)),
        "records": records,
        "target_hits": targets,
        "explicit_eiti_hits": explicit,
        "education_hits": education,
        "explicit_eiti_match_count": len(explicit),
        "education_hit_count": len(education),
        "exhaustive_within_exact_scope": True,
    }


def load_config(path: str | Path) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK166_PNCP_MODALITY9_DIRECT_JSON_SWEEP_V1", "TASK166_CONFIG_SCHEMA")
    _stop(obj["authorization"]["scope"] == "PNCP_LIVE_READ_DISCOVERY_ONLY", "TASK166_AUTH_SCOPE")
    _stop(obj["authorization"]["new_per_page_authorization_required"] is False, "TASK166_AUTH_REUSE")
    _stop(obj["source"]["cnpj"] == "45132495000140", "TASK166_CNPJ")
    _stop(obj["source"]["codigoModalidadeContratacao"] == 9, "TASK166_MODALITY")
    _stop(obj["source"]["tamanhoPagina"] == 50, "TASK166_PAGE_SIZE")
    _stop(obj["persistence"]["raw_payload_git"] is False, "TASK166_RAW_GIT")
    _stop(obj["persistence"]["raw_payload_drive"] is False, "TASK166_RAW_DRIVE")
    return obj
