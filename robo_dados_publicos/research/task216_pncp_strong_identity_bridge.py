from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import fetch_route


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task216_pncp_strong_identity_bridge.v1.json"


class Task216Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task216Stop(code)


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _ascii_upper(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def normalize_admin_identifier(value: Any) -> str:
    text = str(value or "").strip().upper()
    return re.sub(r"[\s\.,;]+$", "", text)


def _complete(value: str, pattern: str) -> bool:
    return bool(value and re.fullmatch(pattern, value))


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK216_PNCP_STRONG_IDENTITY_BRIDGE_V1", "TASK216_SCHEMA")
    _stop(obj.get("issue") == 676, "TASK216_ISSUE")
    _stop(
        obj.get("base_main_sha") == "3104bde110f24398c27c9bdf609fdb01d1989bae",
        "TASK216_BASE",
    )
    _stop(obj["authorization"]["scope"] == "PNCP_LIVE_READ_DISCOVERY_ONLY", "TASK216_AUTH")
    _stop(obj["authorization"]["mutations_allowed"] is False, "TASK216_MUTATION")
    p = obj["pncp"]
    _stop(p["endpoint"] == "https://pncp.gov.br/api/consulta/v1/contratos", "TASK216_ENDPOINT")
    _stop(p["cnpjOrgao"] == "45132495000140", "TASK216_CNPJ")
    _stop(p["tamanhoPagina"] == 500, "TASK216_PAGE_SIZE")
    _stop(p["maxPaginas"] == 10, "TASK216_PAGE_CAP")
    _stop(p["retryMax"] == 0 and p["redirectsMax"] == 0, "TASK216_RETRY_REDIRECT")
    persistence = obj["persistence"]
    _stop(persistence["rawPayloadGit"] is False, "TASK216_RAW_GIT")
    _stop(persistence["rawPayloadDrive"] is False, "TASK216_RAW_DRIVE")
    _stop(persistence["rawPayloadWorkflowArtifact"] is False, "TASK216_RAW_ARTIFACT")
    _stop(persistence["sanitizedResultWorkflowArtifact"] is True, "TASK216_SANITIZED_ARTIFACT")
    rules = obj["tce_bridge_rules"]
    _stop(rules["supplier_cnpj_must_match"] is True, "TASK216_SUPPLIER_REQUIRED")
    _stop(rules["amount_not_identity"] is True, "TASK216_AMOUNT_GUARD")
    _stop(rules["date_not_identity"] is True, "TASK216_DATE_GUARD")
    _stop(rules["text_not_identity"] is True, "TASK216_TEXT_GUARD")
    return obj


def build_url(config: dict[str, Any], page: int) -> str:
    p = config["pncp"]
    params = {
        "dataInicial": p["dataInicial"],
        "dataFinal": p["dataFinal"],
        "cnpjOrgao": p["cnpjOrgao"],
        "pagina": page,
        "tamanhoPagina": p["tamanhoPagina"],
    }
    return p["endpoint"] + "?" + urlencode(params)


def _supplier_cnpj(record: dict[str, Any]) -> str | None:
    direct = record.get("niFornecedor")
    if direct not in (None, ""):
        digits = re.sub(r"\D", "", str(direct))
        return digits if len(digits) == 14 else None
    fornecedor = record.get("fornecedor")
    if isinstance(fornecedor, dict):
        raw = fornecedor.get("niFornecedor") or fornecedor.get("cnpj")
        digits = re.sub(r"\D", "", str(raw or ""))
        return digits if len(digits) == 14 else None
    return None


def _type_class(record: dict[str, Any]) -> str:
    name = _ascii_upper(record.get("tipoContratoNome"))
    if "EMPENHO" in name:
        return "EMPENHO"
    if "CONTRATO" in name:
        return "CONTRATO"
    return "OTHER"


def sanitize_pncp_record(record: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "numeroControlePNCP",
        "numeroControlePNCPCompra",
        "numeroContratoEmpenho",
        "anoContrato",
        "sequencialContrato",
        "processo",
        "objetoContrato",
        "tipoContratoId",
        "tipoContratoNome",
        "valorInicial",
        "valorGlobal",
        "dataAssinatura",
        "dataPublicacaoPncp",
        "niFornecedor",
        "nomeRazaoSocialFornecedor",
    )
    out = {
        key: record.get(key)
        for key in allowed
        if key in record and (record.get(key) is None or isinstance(record.get(key), (str, int, float, bool)))
    }
    supplier = _supplier_cnpj(record)
    if supplier:
        out["supplier_cnpj"] = supplier
    out["type_class"] = _type_class(record)
    return out


def load_jom_anchors(config: dict[str, Any]) -> list[dict[str, Any]]:
    path = ROOT / config["sources"]["jom_fixture"]
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    _stop(len(events) == config["sources"]["jom_expected_rows"], "TASK216_JOM_ROWS")
    rules = config["jom_anchor_rules"]
    allowed_types = set(rules["event_types"])
    anchors: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") not in allowed_types:
            continue
        process = normalize_admin_identifier(event.get("process_number"))
        contract = normalize_admin_identifier(event.get("contract_number"))
        supplier = re.sub(r"\D", "", str(event.get("cnpj") or ""))
        base = {
            "event_id": event["event_id"],
            "event_type": event.get("event_type"),
            "publication_date": event.get("publication_date"),
            "supplier_cnpj": supplier if len(supplier) == 14 else None,
        }
        if _complete(process, rules["complete_process_regex"]):
            anchors.append({**base, "anchor_type": "PROCESS_IDENTITY", "anchor_value": process})
        if _complete(contract, rules["complete_contract_regex"]):
            anchors.append({**base, "anchor_type": "CONTRACT_IDENTITY", "anchor_value": contract})
    anchors.sort(key=lambda row: (row["event_id"], row["anchor_type"], row["anchor_value"]))
    return anchors


def load_tce_index(config: dict[str, Any]) -> dict[str, Any]:
    obj = _load(ROOT / config["sources"]["tce_identity_fixture"])
    _stop(obj.get("schema") == "TASK216_TCE_JOM_SUPPLIER_COMMITMENT_IDENTITY_INDEX_V1", "TASK216_TCE_SCHEMA")
    _stop(obj["row_count"] == config["sources"]["tce_identity_expected_rows"], "TASK216_TCE_ROWS")
    _stop(obj["supplier_count"] == config["sources"]["tce_identity_expected_suppliers"], "TASK216_TCE_SUPPLIERS")
    _stop(obj["rows_sha256"] == config["sources"]["tce_rows_sha256"], "TASK216_TCE_SHA")
    return obj


def _scan_page(payload: dict[str, Any], requested_page: int, config: dict[str, Any]) -> dict[str, Any]:
    _stop(isinstance(payload, dict), "TASK216_PAYLOAD_OBJECT")
    data = payload.get("data")
    _stop(isinstance(data, list), "TASK216_DATA_LIST")
    total_records = payload.get("totalRegistros")
    total_pages = payload.get("totalPaginas")
    page_number = payload.get("numeroPagina")
    _stop(isinstance(total_records, int) and total_records >= 0, "TASK216_TOTAL_RECORDS")
    _stop(isinstance(total_pages, int) and total_pages >= 0, "TASK216_TOTAL_PAGES")
    _stop(page_number == requested_page, "TASK216_PAGE_IDENTITY")
    _stop(total_pages <= config["pncp"]["maxPaginas"], "TASK216_PAGE_CAP")
    _stop(all(isinstance(row, dict) for row in data), "TASK216_RECORD_OBJECT")
    return {
        "requested_page": requested_page,
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "record_count": len(data),
        "records": data,
    }


def _canonical_pncp_commitment(record: dict[str, Any]) -> str | None:
    if _type_class(record) != "EMPENHO":
        return None
    raw = normalize_admin_identifier(record.get("numeroContratoEmpenho"))
    year = record.get("anoContrato")
    match = re.fullmatch(r"0*(\d+)[/-](20\d{2})", raw)
    if match:
        number, y = match.groups()
        if year not in (None, "") and int(year) != int(y):
            return None
        return f"{int(y)}:{int(number)}"
    if re.fullmatch(r"0*\d+", raw) and isinstance(year, int) and 2000 <= year <= 2100:
        return f"{year}:{int(raw)}"
    return None


def _canonical_tce_commitment(value: str) -> str | None:
    match = re.fullmatch(r"(20\d{2}):0*(\d+)-(20\d{2})", str(value))
    if not match or match.group(1) != match.group(3):
        return None
    return f"{int(match.group(1))}:{int(match.group(2))}"


def adjudicate_records(
    records: list[dict[str, Any]],
    anchors: list[dict[str, Any]],
    tce_index: dict[str, Any],
) -> dict[str, Any]:
    by_process: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_contract: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for anchor in anchors:
        if anchor["anchor_type"] == "PROCESS_IDENTITY":
            by_process[anchor["anchor_value"]].append(anchor)
        else:
            by_contract[anchor["anchor_value"]].append(anchor)

    accepted: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for record in records:
        process = normalize_admin_identifier(record.get("processo"))
        contract = normalize_admin_identifier(record.get("numeroContratoEmpenho"))
        candidates: list[dict[str, Any]] = []
        for anchor in by_process.get(process, []):
            candidates.append(anchor)
        if _type_class(record) == "CONTRATO":
            for anchor in by_contract.get(contract, []):
                candidates.append(anchor)
        if not candidates:
            continue
        pncp_supplier = _supplier_cnpj(record)
        for anchor in candidates:
            if anchor.get("supplier_cnpj") and pncp_supplier and anchor["supplier_cnpj"] != pncp_supplier:
                conflicts.append({
                    "event_id": anchor["event_id"],
                    "anchor_type": anchor["anchor_type"],
                    "anchor_value": anchor["anchor_value"],
                    "pncp_control_id": record.get("numeroControlePNCP"),
                    "reason": "SUPPLIER_CNPJ_CONFLICT",
                })
                continue
            purchase_id = record.get("numeroControlePNCPCompra")
            if not purchase_id:
                conflicts.append({
                    "event_id": anchor["event_id"],
                    "anchor_type": anchor["anchor_type"],
                    "anchor_value": anchor["anchor_value"],
                    "pncp_control_id": record.get("numeroControlePNCP"),
                    "reason": "MISSING_PURCHASE_CONTROL_ID",
                })
                continue
            accepted.append({
                "event_id": anchor["event_id"],
                "event_type": anchor["event_type"],
                "anchor_type": anchor["anchor_type"],
                "anchor_value": anchor["anchor_value"],
                "jom_supplier_cnpj": anchor.get("supplier_cnpj"),
                "pncp_anchor_record": sanitize_pncp_record(record),
                "purchase_control_id": str(purchase_id),
            })

    accepted.sort(key=lambda x: (x["event_id"], x["anchor_type"], x["anchor_value"], x["purchase_control_id"]))
    purchase_ids = {row["purchase_control_id"] for row in accepted}
    siblings = [
        sanitize_pncp_record(record)
        for record in records
        if str(record.get("numeroControlePNCPCompra") or "") in purchase_ids
    ]
    siblings.sort(key=lambda x: (
        str(x.get("numeroControlePNCPCompra") or ""),
        str(x.get("numeroControlePNCP") or ""),
        str(x.get("numeroContratoEmpenho") or ""),
    ))

    tce_columns = tce_index["columns"]
    tce_rows = [dict(zip(tce_columns, row)) for row in tce_index["rows"]]
    tce_lookup: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in tce_rows:
        key = _canonical_tce_commitment(row["commitment_number"])
        _stop(key is not None, "TASK216_TCE_COMMITMENT_PARSE")
        tce_lookup[(key, row["supplier_cnpj"])].append(row)

    sibling_by_purchase: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in siblings:
        sibling_by_purchase[str(row.get("numeroControlePNCPCompra") or "")].append(row)

    chains: list[dict[str, Any]] = []
    for anchor in accepted:
        purchase_id = anchor["purchase_control_id"]
        for sibling in sibling_by_purchase[purchase_id]:
            commitment_key = _canonical_pncp_commitment(sibling)
            supplier = sibling.get("supplier_cnpj")
            if not commitment_key or not supplier:
                continue
            matches = tce_lookup.get((commitment_key, supplier), [])
            if not matches:
                continue
            chains.append({
                "event_id": anchor["event_id"],
                "jom_anchor_type": anchor["anchor_type"],
                "jom_anchor_value": anchor["anchor_value"],
                "purchase_control_id": purchase_id,
                "pncp_anchor_control_id": anchor["pncp_anchor_record"].get("numeroControlePNCP"),
                "pncp_empenho_control_id": sibling.get("numeroControlePNCP"),
                "pncp_tipo_contrato_nome": sibling.get("tipoContratoNome"),
                "pncp_numero_contrato_empenho": sibling.get("numeroContratoEmpenho"),
                "canonical_commitment_key": commitment_key,
                "supplier_cnpj": supplier,
                "tce_matches": [
                    {
                        "commitment_number": row["commitment_number"],
                        "official_record_id": row["official_record_id"],
                    }
                    for row in matches
                ],
                "identity_chain": [
                    anchor["anchor_type"],
                    "PNCP_PURCHASE_IDENTITY",
                    "COMMITMENT_IDENTITY",
                ],
                "weak_fields_used": False,
            })
    chains.sort(key=lambda x: (
        x["event_id"],
        x["purchase_control_id"],
        x["canonical_commitment_key"],
        x["pncp_empenho_control_id"] or "",
    ))
    return {
        "accepted_jom_pncp_anchors": accepted,
        "anchor_conflicts": sorted(conflicts, key=lambda x: (x["event_id"], x["anchor_type"], x["anchor_value"])),
        "exact_purchase_siblings": siblings,
        "end_to_end_identity_chains": chains,
        "counts": {
            "jom_anchor_count": len(anchors),
            "accepted_jom_pncp_anchor_count": len(accepted),
            "anchor_conflict_count": len(conflicts),
            "matched_purchase_id_count": len(purchase_ids),
            "sanitized_sibling_count": len(siblings),
            "end_to_end_identity_chain_count": len(chains),
        },
    }


def execute(config: dict[str, Any]) -> dict[str, Any]:
    anchors = load_jom_anchors(config)
    tce_index = load_tce_index(config)
    out: dict[str, Any] = {
        "schema": "TASK216_PNCP_STRONG_IDENTITY_BRIDGE_RESULT_V1",
        "scope": {
            "endpoint": config["pncp"]["endpoint"],
            "cnpjOrgao": config["pncp"]["cnpjOrgao"],
            "dataInicial": config["pncp"]["dataInicial"],
            "dataFinal": config["pncp"]["dataFinal"],
            "tamanhoPagina": config["pncp"]["tamanhoPagina"],
        },
        "requests": [],
        "raw_payload_persisted": False,
        "weak_identity_fields_used": False,
        "promotion_auto_decision": "FORBIDDEN_RUNTIME_ONLY_DISCOVERY",
    }
    pages: list[dict[str, Any]] = []
    page = 1
    while True:
        meta, payload = fetch_route(
            build_url(config, page),
            int(config["pncp"]["timeoutSeconds"]),
            int(config["pncp"]["maxBytesPerPage"]),
        )
        out["requests"].append(meta)
        if meta.get("http_status") == 204:
            _stop(page == 1, "TASK216_204_AFTER_PAGE1")
            out["status"] = "EXHAUSTIVE_COMPLETE_EMPTY_204"
            out["pagination"] = {
                "totalRegistros": 0,
                "totalPaginas": 0,
                "pages_scanned": [],
                "exhaustive_within_exact_scope": True,
            }
            out["identity"] = adjudicate_records([], anchors, tce_index)
            return out
        if payload is None:
            out["status"] = "STOP_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
            out["failed_page"] = page
            out["complete_pagination"] = False
            return out
        scanned = _scan_page(payload, page, config)
        pages.append(scanned)
        if scanned["totalPaginas"] == 0:
            _stop(scanned["totalRegistros"] == 0 and page == 1, "TASK216_ZERO_PAGE_DRIFT")
            break
        if page >= scanned["totalPaginas"]:
            break
        page += 1

    total_pages = pages[0]["totalPaginas"] if pages else 0
    total_records = pages[0]["totalRegistros"] if pages else 0
    _stop(all(p["totalPaginas"] == total_pages for p in pages), "TASK216_TOTAL_PAGES_DRIFT")
    _stop(all(p["totalRegistros"] == total_records for p in pages), "TASK216_TOTAL_RECORDS_DRIFT")
    _stop(len(pages) == total_pages or total_pages == 0, "TASK216_INCOMPLETE_PAGINATION")
    _stop(sum(p["record_count"] for p in pages) == total_records, "TASK216_RECORD_COUNT")
    records = [row for p in pages for row in p["records"]]
    out["pagination"] = {
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "pages_scanned": list(range(1, total_pages + 1)),
        "exhaustive_within_exact_scope": True,
    }
    out["complete_pagination"] = True
    out["identity"] = adjudicate_records(records, anchors, tce_index)
    out["status"] = (
        "EXHAUSTIVE_COMPLETE_STRONG_CHAINS_FOUND"
        if out["identity"]["counts"]["end_to_end_identity_chain_count"]
        else "EXHAUSTIVE_COMPLETE_NO_END_TO_END_STRONG_CHAIN"
    )
    return out
