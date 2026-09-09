from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlencode

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import fetch_route

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219e_pncp_daily_bidding_bridge.v1.json"


class Task219EStop(RuntimeError):
    pass


class PncpSource(Protocol):
    def fetch(self, url: str, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
        ...


class LivePncpSource:
    def fetch(self, url: str, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
        return fetch_route(url, timeout, max_bytes)


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219EStop(code)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg["schema"] == "TASK219E_PNCP_DAILY_BIDDING_BRIDGE_V1", "TASK219E_SCHEMA")
    _stop(cfg["task"] == "TASK_219E" and cfg["issue"] == 691, "TASK219E_TASK")
    src = cfg["source"]
    _stop(src["endpoint"] == "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao", "TASK219E_ENDPOINT")
    _stop(src["cnpj"] == "45132495000140", "TASK219E_CNPJ")
    _stop(src["tamanhoPagina"] == 50, "TASK219E_PAGE_SIZE")
    _stop(src["maxPaginasPerSeed"] == 3, "TASK219E_PAGE_CAP")
    _stop(src["maxTotalRemoteGets"] == 105, "TASK219E_GET_CAP")
    _stop(src["timeoutSeconds"] == 25, "TASK219E_TIMEOUT")
    _stop(src["retryMax"] == 0 and src["redirectsMax"] == 0, "TASK219E_RETRY")
    ident = cfg["identity"]
    _stop(ident["required"] == ["modalidadeId", "numeroCompra_numeric", "anoCompra"], "TASK219E_IDENTITY")
    _stop(ident["exact_single_numeroControlePNCP_required"] is True, "TASK219E_CONTROL")
    for key in (
        "publication_date_is_identity", "supplier_is_identity", "process_is_identity",
        "amount_is_identity", "object_text_is_identity", "semantic_similarity_is_identity",
    ):
        _stop(ident[key] is False, "TASK219E_WEAK_" + key.upper())
    p = cfg["persistence"]
    _stop(p["rawPayloadGit"] is False and p["rawPayloadDrive"] is False, "TASK219E_RAW_PERSIST")
    _stop(p["rawPayloadWorkflowArtifact"] is False and p["sanitizedResultWorkflowArtifact"] is True, "TASK219E_ARTIFACT")
    _stop(cfg["promotion"]["runtime_auto_promotion"] is False, "TASK219E_PROMOTION")
    _stop(cfg["promotion"]["end_to_end_chain_claim_allowed"] is False, "TASK219E_CHAIN")
    return cfg


def load_search_seeds(cfg: Mapping[str, Any], root: Path = ROOT) -> list[dict[str, Any]]:
    path = root / cfg["input"]["search_seeds"]
    _stop(sha256_path(path) == cfg["input"]["search_seeds_sha256"], "TASK219E_SEED_SHA")
    obj = json.loads(path.read_text(encoding="utf-8"))
    _stop(obj["schema"] == "TASK219D_EDITAL_PNCP_DAILY_SEARCH_SEEDS_V1", "TASK219E_SEED_SCHEMA")
    _stop(obj["seed_count"] == cfg["input"]["seed_count"] == 35, "TASK219E_SEED_COUNT")
    seeds = obj["seeds"]
    _stop(len(seeds) == 35, "TASK219E_SEED_ROWS")
    for seed in seeds:
        _stop(seed["modality_id"] in {6, 8, 9}, "TASK219E_SEED_MODALITY")
        _stop(bool(re.fullmatch(r"20\d{2}-\d{2}-\d{2}", seed["publication_date"])), "TASK219E_SEED_DATE")
        _stop(seed["date_role"] == "SEARCH_SCOPE_ONLY_NOT_IDENTITY", "TASK219E_DATE_ROLE")
        _stop(seed["target_identity_count"] == len(seed["target_identities"]) >= 1, "TASK219E_TARGET_COUNT")
        for target in seed["target_identities"]:
            _stop(target["modality_id"] == seed["modality_id"], "TASK219E_TARGET_MODALITY")
            _stop(isinstance(target["bidding_number"], int) and target["bidding_number"] >= 0, "TASK219E_TARGET_NUMBER")
            _stop(isinstance(target["bidding_year"], int), "TASK219E_TARGET_YEAR")
    return seeds


def validate_owner_authorization(
    authorization: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
    expected_implementation_sha: str,
) -> dict[str, Any]:
    _stop(authorization.get("schema") == "TASK219E_OWNER_AUTHORIZATION_V1", "TASK219E_AUTH_SCHEMA")
    _stop(authorization.get("task") == "TASK_219E_LIVE_AUTHORIZATION", "TASK219E_AUTH_TASK")
    _stop(authorization.get("implementation_sha") == expected_implementation_sha, "TASK219E_AUTH_SHA")
    _stop(authorization.get("runtime_branch") == cfg["runtime"]["branch"], "TASK219E_AUTH_BRANCH")
    _stop(authorization.get("source") == "PNCP", "TASK219E_AUTH_SOURCE")
    _stop(authorization.get("operation") == "BOUNDED_35_DAILY_PNCP_BIDDING_IDENTITY_LOOKUPS", "TASK219E_AUTH_OPERATION")
    _stop(authorization.get("attempt_count") == 1, "TASK219E_AUTH_ATTEMPT")
    _stop(authorization.get("owner_authorized") is True, "TASK219E_AUTH_OWNER")
    _stop(authorization.get("authorization_token_batch") == 10, "TASK219E_AUTH_BATCH")
    _stop(authorization.get("authorization_token_consumed_for_this_operation") == 6, "TASK219E_AUTH_TOKEN")
    _stop(authorization.get("authorization_tokens_remaining_after_this_operation") == 4, "TASK219E_AUTH_REMAINING")
    _stop(authorization.get("max_total_remote_get_count") == 105, "TASK219E_AUTH_GET_CAP")
    _stop(authorization.get("pncp_read_authorized") is True, "TASK219E_AUTH_PNCP")
    for key in (
        "task216_authorization_reused","task219c_authorization_reused","task219c2_authorization_reused",
        "task219e_prior_authorization_reused","tce_network_authorized","drive_write_authorized",
        "serving_authorized","publication_authorized","promotion_authorized",
        "recurrence_authorized","schedule_authorized",
    ):
        _stop(authorization.get(key) is False, "TASK219E_AUTH_FORBIDDEN_" + key.upper())
    return dict(authorization)


def build_url(cfg: Mapping[str, Any], seed: Mapping[str, Any], page: int) -> str:
    day = str(seed["publication_date"]).replace("-", "")
    params = {
        "dataInicial": day,
        "dataFinal": day,
        "codigoModalidadeContratacao": int(seed["modality_id"]),
        "cnpj": cfg["source"]["cnpj"],
        "pagina": page,
        "tamanhoPagina": cfg["source"]["tamanhoPagina"],
    }
    return cfg["source"]["endpoint"] + "?" + urlencode(params)


def _digits_cnpj(record: Mapping[str, Any]) -> str:
    org = record.get("orgaoEntidade") or {}
    return re.sub(r"\D", "", str(org.get("cnpj") or record.get("cnpj") or ""))


def _canonical_numero_compra(value: Any, pattern: str) -> int | None:
    m = re.fullmatch(pattern, str(value or "").strip())
    return int(m.group(1)) if m else None


def _sanitize_record(record: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    cnpj = _digits_cnpj(record)
    _stop(cnpj == cfg["source"]["cnpj"], "TASK219E_ENTITY_CNPJ")
    org = record.get("orgaoEntidade") or {}
    unit = record.get("unidadeOrgao") or {}
    municipality = unit.get("municipioNome")
    uf = unit.get("ufSigla")
    if municipality not in (None, ""):
        _stop(str(municipality).strip().casefold() == cfg["source"]["expectedMunicipio"].casefold(), "TASK219E_ENTITY_CITY")
    if uf not in (None, ""):
        _stop(str(uf).strip().upper() == cfg["source"]["expectedUf"], "TASK219E_ENTITY_UF")
    allowed = (
        "anoCompra","sequencialCompra","numeroControlePNCP","processo","numeroCompra",
        "objetoCompra","valorTotalEstimado","valorTotalHomologado","dataPublicacaoPncp",
        "modalidadeId","modalidadeNome","situacaoCompraId","situacaoCompraNome",
    )
    out = {k: record.get(k) for k in allowed if k in record}
    out["cnpj"] = cnpj
    if org.get("razaoSocial") is not None:
        out["razaoSocial"] = org.get("razaoSocial")
    if municipality is not None:
        out["municipioNome"] = municipality
    if uf is not None:
        out["ufSigla"] = uf
    return out


def _scan_payload(payload: Mapping[str, Any], cfg: Mapping[str, Any], seed: Mapping[str, Any], requested_page: int) -> dict[str, Any]:
    _stop(isinstance(payload, Mapping), "TASK219E_PAYLOAD")
    data = payload.get("data")
    _stop(isinstance(data, list), "TASK219E_DATA")
    total = payload.get("totalRegistros")
    pages = payload.get("totalPaginas")
    reported = payload.get("numeroPagina")
    _stop(isinstance(total, int) and total >= 0, "TASK219E_TOTAL")
    _stop(isinstance(pages, int) and pages >= 0, "TASK219E_PAGES")
    _stop(reported == requested_page, "TASK219E_PAGE_ID")
    _stop(pages <= cfg["source"]["maxPaginasPerSeed"], "TASK219E_PAGE_CAP_RUNTIME")
    records = []
    for raw in data:
        _stop(isinstance(raw, Mapping), "TASK219E_RECORD")
        rec = _sanitize_record(raw, cfg)
        if rec.get("modalidadeId") is not None:
            _stop(int(rec["modalidadeId"]) == int(seed["modality_id"]), "TASK219E_MODALITY_IDENTITY")
        records.append(rec)
    return {
        "totalRegistros": total,
        "totalPaginas": pages,
        "requested_page": requested_page,
        "record_count": len(records),
        "records": records,
    }


def _target_key(target: Mapping[str, Any]) -> tuple[int, int, int]:
    return int(target["modality_id"]), int(target["bidding_number"]), int(target["bidding_year"])


def _record_key(record: Mapping[str, Any], cfg: Mapping[str, Any]) -> tuple[int, int, int] | None:
    modality = record.get("modalidadeId")
    year = record.get("anoCompra")
    number = _canonical_numero_compra(record.get("numeroCompra"), cfg["identity"]["numeroCompra_regex"])
    if modality is None or not isinstance(year, int) or number is None:
        return None
    return int(modality), number, year


def adjudicate_seed(
    seed: Mapping[str, Any],
    records: list[dict[str, Any]],
    cfg: Mapping[str, Any],
) -> dict[str, Any]:
    targets = {_target_key(t) for t in seed["target_identities"]}
    by_key: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = _record_key(record, cfg)
        if key in targets:
            by_key[key].append(record)

    accepted = []
    conflicts = []
    for key in sorted(by_key):
        rows = by_key[key]
        controls = {str(r.get("numeroControlePNCP")) for r in rows if r.get("numeroControlePNCP")}
        if len(controls) != 1:
            conflicts.append({
                "modality_id": key[0],
                "bidding_number": key[1],
                "bidding_year": key[2],
                "reason": "EXACT_BIDDING_IDENTITY_NOT_SINGLE_PNCP_CONTROL",
                "numero_controle_pncp_values": sorted(controls),
                "record_count": len(rows),
            })
            continue
        accepted.append({
            "modality_id": key[0],
            "bidding_number": key[1],
            "bidding_year": key[2],
            "numeroControlePNCP": next(iter(controls)),
            "search_publication_date": seed["publication_date"],
            "publication_date_used_as_identity": False,
            "supplier_used_as_identity": False,
            "pncp_records": sorted(rows, key=lambda r: (str(r.get("numeroControlePNCP") or ""), str(r.get("sequencialCompra") or ""))),
        })
    return {"accepted": accepted, "conflicts": conflicts}


def execute(
    cfg: Mapping[str, Any],
    *,
    source: PncpSource,
    authorization: Mapping[str, Any],
    expected_implementation_sha: str,
) -> dict[str, Any]:
    validate_owner_authorization(authorization, cfg=cfg, expected_implementation_sha=expected_implementation_sha)
    seeds = load_search_seeds(cfg)
    out: dict[str, Any] = {
        "schema": "TASK219E_PNCP_DAILY_BIDDING_BRIDGE_RESULT_V1",
        "seed_count": len(seeds),
        "completed_seed_count": 0,
        "requests": [],
        "seed_results": [],
        "accepted_exact_bidding_identities": [],
        "identity_conflicts": [],
        "raw_payload_persisted": False,
        "weak_identity_fields_used": False,
        "absence_inference_allowed": False,
        "positive_exact_matches_remain_valid_if_later_seed_fails": True,
        "end_to_end_jom_pncp_tce_chain_proven": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
    }

    for seed_index, seed in enumerate(seeds, start=1):
        page = 1
        pages: list[dict[str, Any]] = []
        while True:
            _stop(len(out["requests"]) < cfg["source"]["maxTotalRemoteGets"], "TASK219E_TOTAL_GET_CAP")
            meta, payload = source.fetch(
                build_url(cfg, seed, page),
                int(cfg["source"]["timeoutSeconds"]),
                int(cfg["source"]["maxBytesPerPage"]),
            )
            meta = {"seed_index": seed_index, "modality_id": seed["modality_id"], "publication_date": seed["publication_date"], "page": page, **meta}
            out["requests"].append(meta)
            if meta.get("http_status") == 204:
                _stop(page == 1, "TASK219E_204_AFTER_PAGE1")
                pages = []
                break
            if payload is None:
                out["status"] = "STOP_SEED_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
                out["failed_seed_index"] = seed_index
                out["failed_seed"] = {
                    "modality_id": seed["modality_id"],
                    "publication_date": seed["publication_date"],
                    "target_identities": seed["target_identities"],
                }
                out["failed_page"] = page
                out["complete_seed_sweep"] = False
                out["counts"] = _counts(out)
                return out
            scanned = _scan_payload(payload, cfg, seed, page)
            pages.append(scanned)
            if scanned["totalPaginas"] == 0:
                _stop(scanned["totalRegistros"] == 0 and page == 1, "TASK219E_ZERO_PAGE_DRIFT")
                break
            if page >= scanned["totalPaginas"]:
                break
            page += 1

        if pages:
            total_pages = pages[0]["totalPaginas"]
            total_records = pages[0]["totalRegistros"]
            _stop(all(p["totalPaginas"] == total_pages for p in pages), "TASK219E_PAGE_DRIFT")
            _stop(all(p["totalRegistros"] == total_records for p in pages), "TASK219E_RECORD_DRIFT")
            _stop(len(pages) == total_pages, "TASK219E_INCOMPLETE_SEED")
            _stop(sum(p["record_count"] for p in pages) == total_records, "TASK219E_RECONCILIATION")
            records = [r for p in pages for r in p["records"]]
        else:
            total_pages = 0
            total_records = 0
            records = []

        adjudicated = adjudicate_seed(seed, records, cfg)
        out["accepted_exact_bidding_identities"].extend(adjudicated["accepted"])
        out["identity_conflicts"].extend(adjudicated["conflicts"])
        out["seed_results"].append({
            "seed_index": seed_index,
            "modality_id": seed["modality_id"],
            "publication_date": seed["publication_date"],
            "target_identity_count": seed["target_identity_count"],
            "status": "EXHAUSTIVE_COMPLETE_WITHIN_DAILY_MODALITY_SCOPE",
            "totalRegistros": total_records,
            "totalPaginas": total_pages,
            "accepted_exact_identity_count": len(adjudicated["accepted"]),
            "conflict_count": len(adjudicated["conflicts"]),
        })
        out["completed_seed_count"] += 1

    dedup: dict[tuple[int, int, int, str], dict[str, Any]] = {}
    for row in out["accepted_exact_bidding_identities"]:
        key = (row["modality_id"], row["bidding_number"], row["bidding_year"], row["numeroControlePNCP"])
        if key not in dedup:
            dedup[key] = row
    out["accepted_exact_bidding_identities"] = sorted(dedup.values(), key=lambda r: (r["modality_id"], r["bidding_year"], r["bidding_number"], r["numeroControlePNCP"]))
    out["identity_conflicts"] = sorted(out["identity_conflicts"], key=lambda r: (r["modality_id"], r["bidding_year"], r["bidding_number"]))
    out["complete_seed_sweep"] = True
    out["counts"] = _counts(out)
    out["status"] = (
        "PASS_COMPLETE_DAILY_SEED_SWEEP_EXACT_BIDDING_MATCHES_FOUND"
        if out["counts"]["accepted_exact_identity_count"]
        else "PASS_COMPLETE_DAILY_SEED_SWEEP_NO_EXACT_MATCH_WITHIN_SEARCH_SEEDS"
    )
    return out


def _counts(out: Mapping[str, Any]) -> dict[str, Any]:
    accepted = out.get("accepted_exact_bidding_identities") or []
    conflicts = out.get("identity_conflicts") or []
    controls = {r["numeroControlePNCP"] for r in accepted if r.get("numeroControlePNCP")}
    return {
        "completed_seed_count": int(out.get("completed_seed_count") or 0),
        "request_count": len(out.get("requests") or []),
        "accepted_exact_identity_count": len(accepted),
        "matched_pncp_purchase_control_count": len(controls),
        "conflict_count": len(conflicts),
    }


__all__ = [
    "Task219EStop","LivePncpSource","load_config","load_search_seeds",
    "validate_owner_authorization","build_url","adjudicate_seed","execute",
]
