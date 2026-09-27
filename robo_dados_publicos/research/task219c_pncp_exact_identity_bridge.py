from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlencode

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import fetch_route
from robo_dados_publicos.research.task216_pncp_strong_identity_bridge import (
    _canonical_pncp_commitment,
    _supplier_cnpj,
    _type_class,
    normalize_admin_identifier,
    sanitize_pncp_record,
)
from robo_dados_publicos.research.task219b_jom_strong_identity_canonization import (
    derive_legacy_anchors,
    identity_key,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219c_pncp_exact_identity_bridge.v1.json"


class Task219CStop(RuntimeError):
    pass


class PncpSource(Protocol):
    def fetch(self, url: str, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
        ...


class LivePncpSource:
    def fetch(self, url: str, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
        return fetch_route(url, timeout, max_bytes)


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219CStop(code)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_config(path: Path | str = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg["schema"] == "TASK219C_PNCP_EXACT_IDENTITY_BRIDGE_V1", "TASK219C_SCHEMA")
    _stop(cfg["task"] == "TASK_219C" and cfg["issue"] == 691, "TASK219C_TASK")
    source = cfg["source"]
    _stop(source["endpoint"] == "https://pncp.gov.br/api/consulta/v1/contratos", "TASK219C_ENDPOINT")
    _stop(source["cnpjOrgao"] == "45132495000140", "TASK219C_ORG")
    _stop(source["tamanhoPagina"] == 500, "TASK219C_PAGE_SIZE")
    _stop(source["maxPaginasPerPartition"] == 2, "TASK219C_PAGE_CAP")
    _stop(source["maxTotalRemoteGets"] == 18, "TASK219C_GET_CAP")
    _stop(source["retryMax"] == 0 and source["redirectsMax"] == 0, "TASK219C_RETRY")
    parts = cfg["partitions"]
    _stop(len(parts) == 9, "TASK219C_PARTITIONS")
    _stop(parts[0]["dataInicial"] == "20260101" and parts[-1]["dataFinal"] == "20260908", "TASK219C_SCOPE")
    last_end: str | None = None
    for part in parts:
        _stop(part["dataInicial"] <= part["dataFinal"], "TASK219C_PARTITION_ORDER")
        if last_end is not None:
            _stop(part["dataInicial"] > last_end, "TASK219C_PARTITION_OVERLAP")
        last_end = part["dataFinal"]

    rules = cfg["identity_rules"]
    _stop(rules["exact_process_to_single_purchase_control_required"] is True, "TASK219C_PROCESS_SINGLE_PURCHASE")
    _stop(rules["exact_contract_requires_typed_contract"] is True, "TASK219C_TYPED_CONTRACT")
    _stop(rules["exact_contract_to_single_purchase_control_required"] is True, "TASK219C_CONTRACT_SINGLE_PURCHASE")
    _stop(rules["process_supplier_conflict_blocks_identity"] is False, "TASK219C_PROCESS_SUPPLIER_GUARD")
    _stop(rules["contract_supplier_conflict_blocks_identity"] is True, "TASK219C_CONTRACT_SUPPLIER_GUARD")
    for key in (
        "cnpj_alone_is_identity",
        "amount_similarity_is_identity",
        "date_proximity_is_identity",
        "object_text_is_identity",
        "semantic_similarity_is_identity",
        "incomplete_identifier_is_identity",
    ):
        _stop(rules[key] is False, "TASK219C_WEAK_GUARD_" + key.upper())
    _stop(rules["typed_empenho_sibling_is_tce_candidate_only"] is True, "TASK219C_TCE_CANDIDATE_GUARD")

    persistence = cfg["persistence"]
    _stop(persistence["rawPayloadGit"] is False, "TASK219C_RAW_GIT")
    _stop(persistence["rawPayloadDrive"] is False, "TASK219C_RAW_DRIVE")
    _stop(persistence["rawPayloadWorkflowArtifact"] is False, "TASK219C_RAW_ARTIFACT")
    _stop(persistence["sanitizedResultWorkflowArtifact"] is True, "TASK219C_SANITIZED")
    _stop(cfg["promotion_policy"]["runtime_auto_promotion"] is False, "TASK219C_PROMOTION")
    _stop(cfg["promotion_policy"]["end_to_end_chain_claim_allowed"] is False, "TASK219C_CHAIN_CLAIM")
    return cfg


def load_combined_anchors(cfg: Mapping[str, Any], root: Path = ROOT) -> list[dict[str, Any]]:
    inp = cfg["inputs"]
    index_path = root / inp["combined_identity_index"]
    new_path = root / inp["new_anchor_fixture"]
    legacy_path = root / inp["legacy_event_fixture"]
    _stop(sha256_path(index_path) == inp["combined_identity_index_sha256"], "TASK219C_INDEX_SHA")
    _stop(sha256_path(new_path) == inp["new_anchor_fixture_sha256"], "TASK219C_NEW_ANCHOR_SHA")
    _stop(sha256_path(legacy_path) == inp["legacy_event_fixture_sha256"], "TASK219C_LEGACY_SHA")

    legacy_events = _load_jsonl(legacy_path)
    old = derive_legacy_anchors(legacy_events)
    new = _load_jsonl(new_path)
    anchors = old + new
    _stop(len(anchors) == inp["expected_anchor_rows"], "TASK219C_ANCHOR_ROWS")
    keys = {identity_key(row) for row in anchors}
    _stop(len(keys) == inp["expected_unique_identities"], "TASK219C_IDENTITIES")
    _stop(sum(1 for t, _ in keys if t == "PROCESS_IDENTITY") == inp["expected_unique_process_identities"], "TASK219C_PROCESS_IDENTITIES")
    _stop(sum(1 for t, _ in keys if t == "CONTRACT_IDENTITY") == inp["expected_unique_contract_identities"], "TASK219C_CONTRACT_IDENTITIES")
    return sorted(anchors, key=lambda r: (r["anchor_type"], r["anchor_value"], r["event_id"]))


def validate_owner_authorization(
    authorization: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
    expected_implementation_sha: str,
) -> dict[str, Any]:
    _stop(authorization.get("schema") == "TASK219C_OWNER_AUTHORIZATION_V1", "TASK219C_AUTH_SCHEMA")
    _stop(authorization.get("task") == "TASK_219C_LIVE_AUTHORIZATION", "TASK219C_AUTH_TASK")
    _stop(authorization.get("implementation_sha") == expected_implementation_sha, "TASK219C_AUTH_SHA")
    _stop(authorization.get("runtime_branch") == cfg["runtime"]["branch"], "TASK219C_AUTH_BRANCH")
    _stop(authorization.get("source") == "PNCP", "TASK219C_AUTH_SOURCE")
    _stop(
        authorization.get("operation") == "BOUNDED_2026_PNCP_EXACT_IDENTITY_DISCOVERY_303_KEYS",
        "TASK219C_AUTH_OPERATION",
    )
    _stop(authorization.get("attempt_count") == 1, "TASK219C_AUTH_ATTEMPT")
    _stop(authorization.get("owner_authorized") is True, "TASK219C_AUTH_OWNER")
    _stop(authorization.get("authorization_token_batch") == 10, "TASK219C_AUTH_BATCH")
    _stop(authorization.get("authorization_token_consumed_for_this_operation") == 4, "TASK219C_AUTH_TOKEN")
    _stop(authorization.get("authorization_tokens_remaining_after_this_operation") == 6, "TASK219C_AUTH_REMAINING")
    _stop(authorization.get("max_total_remote_get_count") == cfg["source"]["maxTotalRemoteGets"], "TASK219C_AUTH_GET_CAP")
    _stop(authorization.get("pncp_read_authorized") is True, "TASK219C_AUTH_PNCP")
    for key in (
        "task216_authorization_reused",
        "task219a_authorization_reused",
        "task219c_prior_authorization_reused",
        "tce_network_authorized",
        "drive_write_authorized",
        "serving_authorized",
        "publication_authorized",
        "promotion_authorized",
        "recurrence_authorized",
        "schedule_authorized",
    ):
        _stop(authorization.get(key) is False, "TASK219C_AUTH_FORBIDDEN_" + key.upper())
    return dict(authorization)


def build_url(cfg: Mapping[str, Any], partition: Mapping[str, str], page: int) -> str:
    params = {
        "dataInicial": partition["dataInicial"],
        "dataFinal": partition["dataFinal"],
        "cnpjOrgao": cfg["source"]["cnpjOrgao"],
        "pagina": page,
        "tamanhoPagina": cfg["source"]["tamanhoPagina"],
    }
    return cfg["source"]["endpoint"] + "?" + urlencode(params)


def _scan_page(payload: Mapping[str, Any], requested_page: int, cfg: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    _stop(isinstance(data, list), "TASK219C_DATA_LIST")
    total_records = payload.get("totalRegistros")
    total_pages = payload.get("totalPaginas")
    page_number = payload.get("numeroPagina")
    _stop(isinstance(total_records, int) and total_records >= 0, "TASK219C_TOTAL_RECORDS")
    _stop(isinstance(total_pages, int) and total_pages >= 0, "TASK219C_TOTAL_PAGES")
    _stop(page_number == requested_page, "TASK219C_PAGE_IDENTITY")
    _stop(total_pages <= cfg["source"]["maxPaginasPerPartition"], "TASK219C_PAGE_CAP_RUNTIME")
    _stop(all(isinstance(row, dict) for row in data), "TASK219C_RECORD_OBJECT")
    return {
        "requested_page": requested_page,
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "record_count": len(data),
        "records": data,
    }


def _anchor_supplier_set(rows: list[dict[str, Any]]) -> set[str]:
    return {str(r["supplier_cnpj"]) for r in rows if r.get("supplier_cnpj")}


def adjudicate_pncp_records(
    records: list[dict[str, Any]],
    anchors: list[dict[str, Any]],
) -> dict[str, Any]:
    anchor_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for anchor in anchors:
        anchor_groups[identity_key(anchor)].append(anchor)

    candidates: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    process_keys = {value for typ, value in anchor_groups if typ == "PROCESS_IDENTITY"}
    contract_keys = {value for typ, value in anchor_groups if typ == "CONTRACT_IDENTITY"}
    for record in records:
        process = normalize_admin_identifier(record.get("processo"))
        if process in process_keys:
            candidates[("PROCESS_IDENTITY", process)].append(record)
        if _type_class(record) == "CONTRATO":
            contract = normalize_admin_identifier(record.get("numeroContratoEmpenho"))
            if contract in contract_keys:
                candidates[("CONTRACT_IDENTITY", contract)].append(record)

    accepted: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for key in sorted(anchor_groups):
        rows = anchor_groups[key]
        matched_records = candidates.get(key, [])
        if not matched_records:
            continue

        purchase_ids = {
            str(r.get("numeroControlePNCPCompra"))
            for r in matched_records
            if r.get("numeroControlePNCPCompra") not in (None, "")
        }
        missing_purchase = sum(1 for r in matched_records if r.get("numeroControlePNCPCompra") in (None, ""))
        if not purchase_ids:
            conflicts.append({
                "anchor_type": key[0],
                "anchor_value": key[1],
                "reason": "MISSING_PURCHASE_CONTROL_ID",
                "candidate_record_count": len(matched_records),
                "missing_purchase_record_count": missing_purchase,
            })
            continue
        if len(purchase_ids) != 1:
            conflicts.append({
                "anchor_type": key[0],
                "anchor_value": key[1],
                "reason": "MULTIPLE_PURCHASE_CONTROL_IDS_FOR_EXACT_IDENTIFIER",
                "purchase_control_ids": sorted(purchase_ids),
                "candidate_record_count": len(matched_records),
            })
            continue

        if key[0] == "CONTRACT_IDENTITY":
            jom_suppliers = _anchor_supplier_set(rows)
            pncp_suppliers = {_supplier_cnpj(r) for r in matched_records}
            pncp_suppliers.discard(None)
            if len(pncp_suppliers) > 1:
                conflicts.append({
                    "anchor_type": key[0],
                    "anchor_value": key[1],
                    "reason": "MULTIPLE_PNCP_SUPPLIERS_FOR_EXACT_CONTRACT",
                    "jom_supplier_cnpjs": sorted(jom_suppliers),
                    "pncp_supplier_cnpjs": sorted(pncp_suppliers),
                })
                continue
            if jom_suppliers and pncp_suppliers and jom_suppliers.isdisjoint(pncp_suppliers):
                conflicts.append({
                    "anchor_type": key[0],
                    "anchor_value": key[1],
                    "reason": "CONTRACT_SUPPLIER_CNPJ_CONFLICT",
                    "jom_supplier_cnpjs": sorted(jom_suppliers),
                    "pncp_supplier_cnpjs": sorted(pncp_suppliers),
                })
                continue

        purchase_id = next(iter(purchase_ids))
        accepted.append({
            "anchor_type": key[0],
            "anchor_value": key[1],
            "purchase_control_id": purchase_id,
            "anchor_event_ids": sorted({str(r["event_id"]) for r in rows}),
            "anchor_occurrence_count": len(rows),
            "anchor_supplier_cnpjs": sorted(_anchor_supplier_set(rows)),
            "pncp_anchor_records": sorted(
                [sanitize_pncp_record(r) for r in matched_records],
                key=lambda r: (
                    str(r.get("numeroControlePNCP") or ""),
                    str(r.get("numeroContratoEmpenho") or ""),
                ),
            ),
            "supplier_used_as_identity": False,
            "weak_fields_used": False,
        })

    accepted.sort(key=lambda r: (r["anchor_type"], r["anchor_value"], r["purchase_control_id"]))
    purchase_ids = {r["purchase_control_id"] for r in accepted}
    siblings: list[dict[str, Any]] = []
    tce_candidates: list[dict[str, Any]] = []
    for record in records:
        purchase_id = str(record.get("numeroControlePNCPCompra") or "")
        if purchase_id not in purchase_ids:
            continue
        sanitized = sanitize_pncp_record(record)
        siblings.append(sanitized)
        commitment = _canonical_pncp_commitment(record)
        supplier = _supplier_cnpj(record)
        if commitment and supplier:
            tce_candidates.append({
                "purchase_control_id": purchase_id,
                "pncp_control_id": record.get("numeroControlePNCP"),
                "numero_contrato_empenho": record.get("numeroContratoEmpenho"),
                "ano_contrato": record.get("anoContrato"),
                "canonical_commitment_key": commitment,
                "supplier_cnpj": supplier,
                "type_class": _type_class(record),
            })

    siblings.sort(key=lambda r: (
        str(r.get("numeroControlePNCPCompra") or ""),
        str(r.get("numeroControlePNCP") or ""),
        str(r.get("numeroContratoEmpenho") or ""),
    ))
    tce_candidates.sort(key=lambda r: (
        r["purchase_control_id"],
        r["canonical_commitment_key"],
        str(r["pncp_control_id"] or ""),
    ))

    accepted_keys = {(r["anchor_type"], r["anchor_value"]) for r in accepted}
    counts = {
        "input_anchor_row_count": len(anchors),
        "input_unique_identity_count": len(anchor_groups),
        "matched_identity_count": len(accepted),
        "matched_process_identity_count": sum(1 for r in accepted if r["anchor_type"] == "PROCESS_IDENTITY"),
        "matched_contract_identity_count": sum(1 for r in accepted if r["anchor_type"] == "CONTRACT_IDENTITY"),
        "accepted_event_anchor_count": sum(len(anchor_groups[k]) for k in accepted_keys),
        "conflict_identity_count": len(conflicts),
        "matched_purchase_id_count": len(purchase_ids),
        "sanitized_sibling_count": len(siblings),
        "typed_empenho_tce_candidate_count": len(tce_candidates),
    }
    return {
        "accepted_exact_identities": accepted,
        "identity_conflicts": sorted(conflicts, key=lambda r: (r["anchor_type"], r["anchor_value"], r["reason"])),
        "exact_purchase_siblings": siblings,
        "typed_empenho_tce_candidates": tce_candidates,
        "counts": counts,
        "end_to_end_jom_pncp_tce_chain_proven": False,
        "question_promotion_performed": False,
    }


def execute(
    cfg: Mapping[str, Any],
    *,
    source: PncpSource,
    authorization: Mapping[str, Any],
    expected_implementation_sha: str,
) -> dict[str, Any]:
    validate_owner_authorization(
        authorization,
        cfg=cfg,
        expected_implementation_sha=expected_implementation_sha,
    )
    anchors = load_combined_anchors(cfg)
    out: dict[str, Any] = {
        "schema": "TASK219C_PNCP_EXACT_IDENTITY_BRIDGE_RESULT_V1",
        "scope": {
            "cnpjOrgao": cfg["source"]["cnpjOrgao"],
            "dataInicial": cfg["partitions"][0]["dataInicial"],
            "dataFinal": cfg["partitions"][-1]["dataFinal"],
            "partition_count": len(cfg["partitions"]),
        },
        "partition_results": [],
        "requests": [],
        "raw_payload_persisted": False,
        "weak_identity_fields_used": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "complete_all_partitions": False,
    }
    all_records: list[dict[str, Any]] = []

    for partition in cfg["partitions"]:
        page = 1
        pages: list[dict[str, Any]] = []
        while True:
            _stop(len(out["requests"]) < cfg["source"]["maxTotalRemoteGets"], "TASK219C_TOTAL_GET_CAP")
            meta, payload = source.fetch(
                build_url(cfg, partition, page),
                int(cfg["source"]["timeoutSeconds"]),
                int(cfg["source"]["maxBytesPerPage"]),
            )
            meta = {"partition_id": partition["id"], "page": page, **meta}
            out["requests"].append(meta)
            if meta.get("http_status") == 204:
                _stop(page == 1, "TASK219C_204_AFTER_PAGE1")
                break
            if payload is None:
                out["status"] = "STOP_PARTITION_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
                out["failed_partition"] = partition["id"]
                out["failed_page"] = page
                return out

            scanned = _scan_page(payload, page, cfg)
            pages.append(scanned)
            if scanned["totalPaginas"] == 0:
                _stop(scanned["totalRegistros"] == 0 and page == 1, "TASK219C_ZERO_PAGE_DRIFT")
                break
            if page >= scanned["totalPaginas"]:
                break
            page += 1

        if pages:
            total_pages = pages[0]["totalPaginas"]
            total_records = pages[0]["totalRegistros"]
            _stop(all(p["totalPaginas"] == total_pages for p in pages), "TASK219C_TOTAL_PAGES_DRIFT")
            _stop(all(p["totalRegistros"] == total_records for p in pages), "TASK219C_TOTAL_RECORDS_DRIFT")
            _stop(len(pages) == total_pages, "TASK219C_INCOMPLETE_PARTITION")
            _stop(sum(p["record_count"] for p in pages) == total_records, "TASK219C_RECORD_RECONCILIATION")
            records = [r for p in pages for r in p["records"]]
        else:
            total_pages = 0
            total_records = 0
            records = []

        all_records.extend(records)
        out["partition_results"].append({
            "partition_id": partition["id"],
            "dataInicial": partition["dataInicial"],
            "dataFinal": partition["dataFinal"],
            "status": "EXHAUSTIVE_COMPLETE",
            "totalRegistros": total_records,
            "totalPaginas": total_pages,
            "pages_scanned": list(range(1, total_pages + 1)),
        })

    out["complete_all_partitions"] = True
    out["total_records_across_partitions"] = len(all_records)
    out["identity"] = adjudicate_pncp_records(all_records, anchors)
    out["status"] = (
        "EXHAUSTIVE_COMPLETE_PNCP_EXACT_IDENTITIES_FOUND"
        if out["identity"]["counts"]["matched_identity_count"]
        else "EXHAUSTIVE_COMPLETE_NO_PNCP_EXACT_IDENTITY"
    )
    return out


__all__ = [
    "Task219CStop",
    "LivePncpSource",
    "load_config",
    "load_combined_anchors",
    "validate_owner_authorization",
    "build_url",
    "adjudicate_pncp_records",
    "execute",
]
