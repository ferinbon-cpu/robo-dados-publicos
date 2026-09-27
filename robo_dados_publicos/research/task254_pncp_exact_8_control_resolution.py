from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Protocol

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import fetch_route

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task254_pncp_exact_8_control_resolution.v1.json"
EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
EXPECTED_SOURCE = "PNCP_PUBLIC_RESOURCE_DETAIL"
CONTROL_RE = re.compile(r"^(\d{14})-(\d+)-(\d{6})/(20\d{2})$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class Task254Stop(RuntimeError):
    pass


class DetailSource(Protocol):
    def get(self, url: str, *, timeout: int, max_bytes: int) -> tuple[dict[str, Any], Any | None]:
        ...


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task254Stop(code)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_control(control: str) -> dict[str, Any]:
    match = CONTROL_RE.fullmatch(control or "")
    _stop(match is not None, "TASK254_CONTROL_FORMAT")
    cnpj, kind, sequence, year = match.groups()
    _stop(cnpj == "45132495000140", "TASK254_CONTROL_CNPJ")
    _stop(kind == "1", "TASK254_CONTROL_KIND")
    return {
        "cnpj": cnpj,
        "kind": int(kind),
        "sequencial": int(sequence),
        "ano": int(year),
    }


def build_url(config: Mapping[str, Any], target: Mapping[str, Any]) -> str:
    source = config["source"]
    path = source["endpoint_template"].format(
        cnpj=target["cnpj"],
        ano=target["ano"],
        sequencial=target["sequencial"],
    )
    return source["origin"] + path


def load_config(path: Path | str = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg.get("schema") == "TASK254_PNCP_EXACT_8_CONTROL_RESOLUTION_V1", "TASK254_CONFIG_SCHEMA")
    _stop(cfg.get("task") == "TASK_254", "TASK254_CONFIG_TASK")
    _stop(cfg.get("issue") == 841, "TASK254_CONFIG_ISSUE")
    _stop(cfg.get("mode") == "T1_READONLY_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION", "TASK254_CONFIG_MODE")

    task253 = cfg.get("source_task253") or {}
    _stop(task253.get("evidence_status") == "PASS_TASK252_CANONIZED_AND_8_EXPLICIT_PNCP_CONTROLS_MATERIALIZED", "TASK254_TASK253_STATUS")
    _stop(task253.get("anchor_fixture_sha256") == "db946b80913ebb892168b5406fd8b5cc274a282ef1f81827d6ba29a2a8f0e7b3", "TASK254_TASK253_FIXTURE_SHA")
    _stop(task253.get("expected_anchor_rows") == 8, "TASK254_TASK253_ROWS")
    _stop(task253.get("expected_unique_controls") == 8, "TASK254_TASK253_UNIQUE")
    _stop(task253.get("next_gate") == "BOUNDED_EXACT_8_PNCP_CONTROL_REMOTE_RESOLUTION_REQUIRES_SEPARATE_AUTHORIZATION", "TASK254_TASK253_GATE")

    source = cfg.get("source") or {}
    _stop(source.get("origin") == "https://pncp.gov.br", "TASK254_ORIGIN")
    _stop(source.get("cnpj") == "45132495000140", "TASK254_CNPJ")
    _stop(source.get("endpoint_template") == "/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}", "TASK254_ENDPOINT")
    _stop(source.get("method") == "GET", "TASK254_METHOD")
    _stop(source.get("max_detail_get_count") == 8, "TASK254_GET_BUDGET")
    _stop(source.get("max_total_remote_get_count") == 8, "TASK254_TOTAL_GET_BUDGET")
    _stop(source.get("max_gets_per_target") == 1, "TASK254_GETS_PER_TARGET")
    _stop(source.get("preflight_get_count") == 0, "TASK254_PREFLIGHT")
    _stop(source.get("max_bytes_per_response") == 10_000_000, "TASK254_RESPONSE_CAP")
    _stop(source.get("max_aggregate_response_bytes") == 80_000_000, "TASK254_AGGREGATE_CAP")
    for key in (
        "pagination",
        "automatic_retry",
        "redirects",
        "alternate_url_discovery",
        "publication_search",
        "items_route",
        "history_route",
        "budget_sources_route",
        "contracts_route",
    ):
        _stop(source.get(key) is False, "TASK254_SOURCE_GUARD_" + key.upper())

    targets = cfg.get("targets") or []
    _stop(len(targets) == 8, "TASK254_TARGET_COUNT")
    controls = [str(t.get("control")) for t in targets]
    _stop(len(set(controls)) == 8, "TASK254_TARGET_DUPLICATE")
    for target in targets:
        parsed = parse_control(str(target["control"]))
        for key in ("cnpj", "kind", "ano", "sequencial"):
            _stop(target.get(key) == parsed[key], "TASK254_TARGET_" + key.upper())
        _stop(str(target.get("event_id", "")).startswith("JOEV_"), "TASK254_TARGET_EVENT")
        _stop(target.get("edition") in {7321, 7322, 7324}, "TASK254_TARGET_EDITION")

    identity = cfg.get("identity_validation") or {}
    _stop(identity.get("numeroControlePNCP") == "EXACT_TARGET_CONTROL", "TASK254_ID_CONTROL")
    _stop(identity.get("anoCompra") == "EXACT_TARGET_YEAR", "TASK254_ID_YEAR")
    _stop(identity.get("sequencialCompra") == "EXACT_TARGET_SEQUENCE", "TASK254_ID_SEQUENCE")
    _stop(identity.get("orgaoEntidade.cnpj") == "EXACT_TARGET_CNPJ", "TASK254_ID_CNPJ")
    for key in ("processo_required_for_identity", "object_text_identity_allowed", "supplier_identity_allowed", "semantic_similarity_identity_allowed"):
        _stop(identity.get(key) is False, "TASK254_ID_GUARD_" + key.upper())

    unavailable = cfg.get("unavailable_semantics") or {}
    for key in ("http_404_is_global_absence", "http_503_is_no_data", "http_504_is_no_data", "transport_failure_is_no_data", "absence_inference_allowed"):
        _stop(unavailable.get(key) is False, "TASK254_UNAVAILABLE_GUARD_" + key.upper())
    _stop(unavailable.get("unresolved_target_may_be_recorded") is True, "TASK254_UNRESOLVED_RECORD")

    persistence = cfg.get("persistence") or {}
    for key in (
        "raw_payload_git",
        "raw_payload_drive",
        "raw_payload_workflow_artifact",
        "drive_write",
        "bronze",
        "silver",
        "gold",
        "serving",
        "publication",
        "promotion",
    ):
        _stop(persistence.get(key) is False, "TASK254_PERSISTENCE_" + key.upper())
    _stop(persistence.get("sanitized_result_workflow_artifact") is True, "TASK254_SANITIZED_ARTIFACT")
    _stop(persistence.get("artifact_retention_days") == 1, "TASK254_RETENTION")

    auth = cfg.get("authorization") or {}
    _stop(auth.get("required_task") == "TASK_254_LIVE_AUTHORIZATION", "TASK254_AUTH_TASK")
    _stop(auth.get("required_operation") == "EXACT_8_TASK253_PNCP_PURCHASE_CONTROL_DETAIL_RESOLUTION", "TASK254_AUTH_OPERATION")
    _stop(auth.get("attempt_count") == 1, "TASK254_AUTH_ATTEMPT")
    for key, value in auth.items():
        if key.endswith("_authorized") or key.endswith("_authorized_by_default") or key.endswith("_reuse_allowed"):
            _stop(value is False, "TASK254_AUTH_DEFAULT_" + key.upper())

    _stop(all(v is False for v in (cfg.get("pre_authorization_remote_effects") or {}).values()), "TASK254_PREAUTH_EFFECT")
    _stop(cfg.get("next_gate") == "OWNER_AUTHORIZED_EXACT_8_PNCP_DETAIL_GETS_ON_MERGED_TASK254_SHA", "TASK254_NEXT_GATE")
    return cfg


def validate_task253_inputs(config: Mapping[str, Any], root: Path = ROOT) -> dict[str, Any]:
    src = config["source_task253"]
    evidence_path = root / src["evidence"]
    fixture_path = root / src["anchor_fixture"]
    _stop(evidence_path.is_file(), "TASK254_TASK253_EVIDENCE_FILE")
    _stop(fixture_path.is_file(), "TASK254_TASK253_FIXTURE_FILE")
    _stop(sha256_path(fixture_path) == src["anchor_fixture_sha256"], "TASK254_TASK253_FIXTURE_HASH")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    _stop(evidence.get("schema") == "TASK253_JOM_PNCP_EXPLICIT_CONTROL_CANONIZATION_RESULT_V1", "TASK254_TASK253_EVIDENCE_SCHEMA")
    _stop(evidence.get("status") == src["evidence_status"], "TASK254_TASK253_EVIDENCE_STATUS")
    _stop(evidence.get("next_gate") == src["next_gate"], "TASK254_TASK253_EVIDENCE_GATE")
    materialized = evidence.get("materialized") or {}
    _stop(materialized.get("explicit_pncp_control_anchors_fixture_sha256") == src["anchor_fixture_sha256"], "TASK254_TASK253_EVIDENCE_FIXTURE_HASH")
    _stop((materialized.get("counts") or {}).get("explicit_pncp_anchor_rows") == 8, "TASK254_TASK253_EVIDENCE_ROWS")

    anchors = _load_jsonl(fixture_path)
    _stop(len(anchors) == 8, "TASK254_TASK253_ANCHOR_ROWS")
    _stop(len({r["anchor_value"] for r in anchors}) == 8, "TASK254_TASK253_ANCHOR_UNIQUE")
    target_by_control = {t["control"]: t for t in config["targets"]}
    _stop(set(target_by_control) == {r["anchor_value"] for r in anchors}, "TASK254_TARGET_FIXTURE_CONTROLS")
    for anchor in anchors:
        _stop(anchor.get("anchor_type") == "PNCP_PURCHASE_CONTROL", "TASK254_ANCHOR_TYPE")
        _stop(anchor.get("evidence_class") == "EXPLICIT_PNCP_ID_IN_OFFICIAL_JOM_TEXT", "TASK254_ANCHOR_CLASS")
        target = target_by_control[anchor["anchor_value"]]
        _stop(anchor.get("event_id") == target["event_id"], "TASK254_ANCHOR_EVENT")
        _stop(anchor.get("edition") == target["edition"], "TASK254_ANCHOR_EDITION")
        _stop(bool(HEX64_RE.fullmatch(str(anchor.get("source_sha256", "")))), "TASK254_ANCHOR_SOURCE_SHA")
    return evidence


def _base_result(status: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema": "TASK254_PNCP_EXACT_8_CONTROL_RESOLUTION_RESULT_V1",
        "status": status,
        "complete_observation_scope": False,
        "source_get_count": 0,
        "target_count": 8,
        "resolved_count": 0,
        "unresolved_count": 0,
        "observations": [],
        "aggregate_response_bytes": 0,
        "raw_payload_persisted": False,
        "drive_write_count": 0,
        "bronze_created": 0,
        "silver_created": 0,
        "gold_created": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "retry_performed": False,
        "redirect_followed": False,
        "alternate_url_discovery_performed": False,
        "publication_search_performed": False,
        "pagination_performed": False,
        "other_pncp_routes_requested": False,
        "tce_network_used": False,
        "absence_inference_allowed": False,
        "global_pncp_absence_conclusion": False,
        "financial_identity_promoted": False,
        "transaction_identity_promoted": False,
        **extra,
    }


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if not authorization:
        return _base_result("STOP_TASK254_LIVE_NOT_AUTHORIZED")
    if authorization.get("synthetic_test_only") is True:
        return _base_result("STOP_TASK254_SYNTHETIC_AUTH_NOT_LIVE")
    if authorization.get("prior_authorization_reused") is True:
        return _base_result("STOP_TASK254_PRIOR_AUTHORIZATION_REUSE")
    if re.fullmatch(r"[0-9a-f]{40}", expected_implementation_sha or "") is None:
        return _base_result("STOP_TASK254_IMPLEMENTATION_SHA_FORMAT")

    controls = [t["control"] for t in config["targets"]]
    required = {
        "task": "TASK_254_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "implementation_branch": "main",
        "runtime_branch": config["runtime"]["branch"],
        "implementation_sha": expected_implementation_sha,
        "source": EXPECTED_SOURCE,
        "operation": "EXACT_8_TASK253_PNCP_PURCHASE_CONTROL_DETAIL_RESOLUTION",
        "controls": controls,
        "target_count": 8,
        "max_detail_get_count": 8,
        "max_total_remote_get_count": 8,
        "max_gets_per_target": 1,
        "attempt_count": 1,
        "owner_authorized": True,
        "source_network_authorized": True,
        "pncp_detail_gets_authorized": True,
        "rediscovery_authorized": False,
        "publication_search_authorized": False,
        "other_pncp_routes_authorized": False,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
        "prior_authorization_reused": False,
        "drive_write_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
        "consumed": False,
    }
    if any(authorization.get(k) != v for k, v in required.items()):
        return _base_result("STOP_TASK254_AUTHORIZATION_CONTRACT_MISMATCH")
    return {"status": "PASS_TASK254_LIVE_AUTHORIZATION"}


def _primitive(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def sanitize_detail(payload: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    selected = {
        key: payload.get(key)
        for key in config["sanitized_fields"]
        if key in payload and _primitive(payload.get(key))
    }
    org = payload.get("orgaoEntidade")
    if isinstance(org, Mapping):
        selected["orgaoEntidade"] = {
            key: org.get(key)
            for key in ("cnpj", "razaoSocial", "poderId", "esferaId")
            if key in org and _primitive(org.get(key))
        }
    unit = payload.get("unidadeOrgao")
    if isinstance(unit, Mapping):
        selected["unidadeOrgao"] = {
            key: unit.get(key)
            for key in ("codigoUnidade", "nomeUnidade", "municipioNome", "ufSigla")
            if key in unit and _primitive(unit.get(key))
        }
    return {
        "top_level_keys": sorted(str(k) for k in payload.keys()),
        "selected": selected,
    }


def validate_detail_identity(payload: Mapping[str, Any], target: Mapping[str, Any]) -> None:
    _stop(payload.get("numeroControlePNCP") == target["control"], "TASK254_DETAIL_CONTROL_IDENTITY_MISMATCH")
    _stop(payload.get("anoCompra") == target["ano"], "TASK254_DETAIL_YEAR_IDENTITY_MISMATCH")
    _stop(payload.get("sequencialCompra") == target["sequencial"], "TASK254_DETAIL_SEQUENCE_IDENTITY_MISMATCH")
    org = payload.get("orgaoEntidade")
    _stop(isinstance(org, Mapping), "TASK254_DETAIL_ORG_SCHEMA")
    _stop(str(org.get("cnpj") or "") == target["cnpj"], "TASK254_DETAIL_CNPJ_IDENTITY_MISMATCH")


class LivePncpDetailSource:
    def get(self, url: str, *, timeout: int, max_bytes: int) -> tuple[dict[str, Any], Any | None]:
        meta, payload = fetch_route(url, timeout, max_bytes)
        return {**meta, "requested_url": url, "remote_get_count": 1}, payload


def execute_exact_resolution(
    config: Mapping[str, Any],
    *,
    source: DetailSource,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    validate_task253_inputs(config)
    if not offline_test_mode:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
            config=config,
        )
        if auth["status"] != "PASS_TASK254_LIVE_AUTHORIZATION":
            return auth

    observations: list[dict[str, Any]] = []
    source_get_count = 0
    aggregate_bytes = 0
    try:
        for target in config["targets"]:
            _stop(source_get_count < config["source"]["max_total_remote_get_count"], "TASK254_TOTAL_GET_BUDGET_EXCEEDED")
            url = build_url(config, target)
            meta, payload = source.get(
                url,
                timeout=int(config["source"]["timeout_seconds"]),
                max_bytes=int(config["source"]["max_bytes_per_response"]),
            )
            source_get_count += 1
            _stop(meta.get("remote_get_count", 1) == 1, "TASK254_TARGET_GET_COUNT")
            _stop(meta.get("requested_url", meta.get("url")) == url, "TASK254_REQUEST_URL_DRIFT")
            bytes_received = int(meta.get("bytes_received") or 0)
            _stop(0 <= bytes_received <= config["source"]["max_bytes_per_response"], "TASK254_RESPONSE_BYTE_CAP")
            aggregate_bytes += bytes_received
            _stop(aggregate_bytes <= config["source"]["max_aggregate_response_bytes"], "TASK254_AGGREGATE_BYTE_CAP")

            status = meta.get("http_status")
            base = {
                "control": target["control"],
                "cnpj": target["cnpj"],
                "ano": target["ano"],
                "sequencial": target["sequencial"],
                "edition": target["edition"],
                "event_id": target["event_id"],
                "requested_url": url,
                "http_status": status,
                "content_type": meta.get("content_type"),
                "bytes_received": bytes_received,
                "response_sha256": meta.get("sha256"),
                "transport_error": meta.get("transport_error"),
                "resolved": False,
                "absence_inference_allowed": False,
            }

            if isinstance(status, int) and 300 <= status < 400:
                raise Task254Stop("TASK254_REDIRECT_STATUS_OBSERVED")

            if status == 200:
                content_type = str(meta.get("content_type") or "").lower()
                _stop("application/json" in content_type, "TASK254_HTTP_200_CONTENT_TYPE")
                _stop(payload is not None, "TASK254_HTTP_200_JSON_UNAVAILABLE")
                _stop(isinstance(payload, Mapping), "TASK254_DETAIL_SCHEMA")
                validate_detail_identity(payload, target)
                observations.append(
                    {
                        **base,
                        "status": "RESOLVED_EXACT_PNCP_DETAIL_IDENTITY",
                        "resolved": True,
                        "sanitized": sanitize_detail(payload, config),
                    }
                )
            else:
                observations.append(
                    {
                        **base,
                        "status": "UNRESOLVED_SOURCE_OBSERVATION",
                    }
                )

        _stop(source_get_count == 8, "TASK254_EXACT_GET_COUNT")
        _stop(len(observations) == 8, "TASK254_EXACT_OBSERVATION_COUNT")
        resolved_count = sum(1 for row in observations if row["resolved"])
        unresolved_count = len(observations) - resolved_count
        http_counts = Counter(str(row["http_status"]) for row in observations)
        return {
            **_base_result("PASS_BOUNDED_EXACT_8_PNCP_DETAIL_OBSERVATION"),
            "complete_observation_scope": True,
            "source_get_count": source_get_count,
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "observations": observations,
            "aggregate_response_bytes": aggregate_bytes,
            "http_status_counts": dict(sorted(http_counts.items())),
            "task253_direct_controls_preserved": True,
            "remote_resolution_proved_controls": [row["control"] for row in observations if row["resolved"]],
            "unresolved_controls": [row["control"] for row in observations if not row["resolved"]],
            "scientific_interpretation": "BOUNDED_CURRENT_PNCP_DETAIL_OBSERVATION_ONLY",
        }
    except Task254Stop as exc:
        return {
            **_base_result("STOP_TASK254_FAIL_CLOSED"),
            "source_get_count": source_get_count,
            "observations": observations,
            "aggregate_response_bytes": aggregate_bytes,
            "stop_code": str(exc),
        }
