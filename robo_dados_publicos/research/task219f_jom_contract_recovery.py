from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219f_jom_contract_recovery.v1.json"


class Task219FStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219FStop(code)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _canonical_row_sha256(obj: Mapping[str, Any]) -> str:
    raw = (json.dumps(dict(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = _load(Path(path))
    _stop(cfg.get("schema") == "TASK219F_JOM_CONTRACT_RECOVERY_V1", "TASK219F_SCHEMA")
    _stop(cfg.get("task") == "TASK_219F" and cfg.get("issue") == 701, "TASK219F_TASK")
    _stop(cfg.get("parent_issue") == 691, "TASK219F_PARENT")

    recovery = cfg["recovery_policy"]
    _stop(recovery["required_label"] == "CONTRATO", "TASK219F_LABEL")
    _stop(recovery["structured_prefix_must_agree"] is True, "TASK219F_PREFIX_GUARD")
    _stop(recovery["single_label_scoped_reference_required"] is True, "TASK219F_SINGLE_REFERENCE")
    _stop(recovery["historical_event_id_must_be_preserved"] is True, "TASK219F_EVENT_ID_GUARD")
    _stop(recovery["generic_journal_parser_migration_allowed"] is False, "TASK219F_NO_PARSER_MIGRATION")

    bridge = cfg["municipal_bridge"]
    _stop(bridge["source_id"] == "LIMEIRA_CONTRATOS", "TASK219F_SOURCE")
    _stop(bridge["resolver"].endswith("LimeiraContractsResolver"), "TASK219F_RESOLVER")
    _stop(bridge["live_execution_implemented"] is False, "TASK219F_LIVE_IMPLEMENTATION")
    _stop(bridge["live_execution_authorized"] is False, "TASK219F_LIVE_AUTH")
    _stop(bridge["fresh_owner_authorization_required"] is True, "TASK219F_FRESH_AUTH")
    _stop(bridge["authorization_reuse_allowed"] is False, "TASK219F_AUTH_REUSE")
    _stop(not any(cfg["remote_effects"].values()), "TASK219F_REMOTE_EFFECTS")
    return cfg


def load_fixture(cfg: Mapping[str, Any], root: Path = ROOT) -> dict[str, Any]:
    spec = cfg["fixture"]
    path = root / spec["path"]
    _stop(path.is_file(), "TASK219F_FIXTURE_MISSING")
    _stop(_git_blob_sha(path) == spec["git_blob_sha"], "TASK219F_FIXTURE_BLOB_SHA")
    obj = _load(path)
    _stop(_canonical_row_sha256(obj) == spec["canonical_row_sha256"], "TASK219F_FIXTURE_ROW_SHA")
    return obj


def recover_contract_reference(event: Mapping[str, Any], cfg: Mapping[str, Any]) -> str:
    expected = cfg["expected_event"]
    policy = cfg["recovery_policy"]

    _stop(event.get("event_id") == expected["event_id"], "TASK219F_EVENT_ID")
    _stop(event.get("event_type") == "CONTRATO", "TASK219F_EVENT_TYPE")
    _stop(event.get("contract_number") == expected["structured_contract_number"], "TASK219F_STRUCTURED_CONTRACT")

    excerpt = str(event.get("excerpt_redacted") or "")
    pattern = re.compile(policy["exact_label_regex"])
    matches = pattern.findall(excerpt)
    _stop(len(matches) == 1, "TASK219F_LABEL_SCOPED_REFERENCE_COUNT")

    number_raw, year = matches[0]
    number = str(int(number_raw))
    recovered = f"{number}/{year}"

    structured = str(event.get("contract_number") or "")
    prefix = re.fullmatch(r"\s*0*(\d{1,9})\s*/\s*", structured)
    _stop(prefix is not None, "TASK219F_STRUCTURED_PREFIX_SHAPE")
    _stop(str(int(prefix.group(1))) == number, "TASK219F_STRUCTURED_PREFIX_CONFLICT")
    _stop(recovered == expected["recovered_contract_number"], "TASK219F_RECOVERED_CONTRACT")
    return recovered


def _validate_exact_event_fields(event: Mapping[str, Any], cfg: Mapping[str, Any]) -> None:
    expected = cfg["expected_event"]
    for key in (
        "event_id",
        "event_type",
        "edition",
        "page_number",
        "publication_date",
        "source_id",
        "source_sha256",
        "bidding_modality",
        "bidding_number",
        "process_number",
        "contractor",
        "cnpj",
        "object_text",
        "value_brl",
    ):
        _stop(event.get(key) == expected[key], f"TASK219F_FIELD_{key.upper()}")


def _query_contract(cfg: Mapping[str, Any]) -> dict[str, Any]:
    query = json.loads(json.dumps(cfg["municipal_bridge"]["query"], ensure_ascii=False))
    _stop(LimeiraContractsResolver.has_minimum_search_key(query), "TASK219F_QUERY_NOT_EXECUTABLE")
    keys = query["match_keys"]
    _stop(keys["year"] == 2026, "TASK219F_QUERY_YEAR")
    _stop(keys["contract_number"] == "45/2026", "TASK219F_QUERY_CONTRACT")
    _stop(keys["cnpj"] == "37457979000131", "TASK219F_QUERY_CNPJ")
    _stop(keys["contractor"] == "Med Doctor Acessórios Ltda", "TASK219F_QUERY_SUPPLIER")
    return query


def _prove_candidate_policy(cfg: Mapping[str, Any]) -> dict[str, Any]:
    query = _query_contract(cfg)
    keys = query["match_keys"]
    synthetic_exact_row = [[
        "Contrato 45/2026",
        "Med Doctor Acessórios Ltda",
        "37.457.979/0001-31",
        "Processo 902.281/2025",
        "Pregão Eletrônico 10/2026",
    ]]
    candidates = LimeiraContractsResolver._candidate_rows(synthetic_exact_row, keys)
    _stop(len(candidates) == 1, "TASK219F_SYNTHETIC_POLICY_PROOF")
    signals = candidates[0]["match_signals"]
    for signal in cfg["municipal_bridge"]["candidate_required_signals"]:
        _stop(signal in signals, "TASK219F_REQUIRED_SIGNAL_" + signal)
    return {
        "synthetic_only": True,
        "purpose": "PROVE_EXISTING_FAIL_CLOSED_CANDIDATE_POLICY_BEFORE_ANY_LIVE_QUERY",
        "required_signals": cfg["municipal_bridge"]["candidate_required_signals"],
        "observed_signals": signals,
        "identity_proven_by_synthetic_row": False,
    }


def build_evidence(root: Path = ROOT) -> dict[str, Any]:
    cfg = load_config(root / "config/task219f_jom_contract_recovery.v1.json")
    event = load_fixture(cfg, root)
    _validate_exact_event_fields(event, cfg)
    recovered = recover_contract_reference(event, cfg)
    query = _query_contract(cfg)
    policy_proof = _prove_candidate_policy(cfg)

    seed = {
        "event_id": event["event_id"],
        "historical_event_id_preserved": True,
        "source_id": event["source_id"],
        "source_sha256": event["source_sha256"],
        "edition": event["edition"],
        "page_number": event["page_number"],
        "publication_date": event["publication_date"],
        "event_type": event["event_type"],
        "structured_contract_number_original": event["contract_number"],
        "recovered_contract_number": recovered,
        "recovery_basis": "EXACT_LABEL_SCOPED_SANITIZED_JOM_EXCERPT_PLUS_STRUCTURED_PREFIX_AGREEMENT",
        "process_number": event["process_number"],
        "bidding_modality": event["bidding_modality"],
        "bidding_number": event["bidding_number"],
        "contractor": event["contractor"],
        "cnpj": event["cnpj"],
        "object_text": event["object_text"],
        "value_brl": event["value_brl"],
    }

    return {
        "task": "TASK_219F_JOM_CONTRACT_45_2026_RECOVERY",
        "issue": 701,
        "parent_issue": 691,
        "canonical_date": "2026-09-09",
        "source_artifact": cfg["source_artifact"],
        "recovered_primary_jom_seed": seed,
        "municipal_primary_bridge": {
            "status": "READY_FOR_SINGLE_USE_LIVE_QUERY_AFTER_FRESH_AUTHORIZATION",
            "source_id": cfg["municipal_bridge"]["source_id"],
            "authority": cfg["municipal_bridge"]["authority"],
            "search_url": cfg["municipal_bridge"]["search_url"],
            "resolver": cfg["municipal_bridge"]["resolver"],
            "query": query,
            "candidate_policy_proof": policy_proof,
            "max_http_requests_future": cfg["municipal_bridge"]["max_http_requests_future"],
            "same_origin_only_future": cfg["municipal_bridge"]["same_origin_only_future"],
            "live_execution_implemented": False,
            "live_execution_authorized": False,
        },
        "adjudication": {
            "exact_contract_identity_recovered_from_primary_jom": True,
            "generic_parser_changed": False,
            "historical_event_id_changed": False,
            "municipal_contract_match_proven": False,
            "pncp_match_proven": False,
            "tce_commitment_identity_proven": False,
            "question_promotion_performed": False,
            "contextual_paths_before": 34,
            "contextual_paths_after": 34,
            "canonical_questions_total": 38,
            "remaining_blockers": cfg["scientific_state"]["remaining_blockers"],
        },
        "next_action": "ONE_BOUNDED_LIMEIRA_CONTRATOS_QUERY_FOR_EXACT_CONTRACT_45_2026_AFTER_FRESH_OWNER_AUTHORIZATION",
        "remote_effects": cfg["remote_effects"],
    }


def materialize(root: Path = ROOT) -> dict[str, Any]:
    cfg = load_config(root / "config/task219f_jom_contract_recovery.v1.json")
    evidence = build_evidence(root)
    out = root / cfg["outputs"]["evidence"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    evidence = materialize()
    print("TASK219F_STATUS=PASS_JOM_CONTRACT_45_2026_RECOVERY")
    print("TASK219F_CONTRACT=" + evidence["recovered_primary_jom_seed"]["recovered_contract_number"])
    print("TASK219F_LIVE_AUTHORIZED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
