from __future__ import annotations

import json
import re
import unicodedata
from hashlib import sha256
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/jornal_semantic_layers.v1.json"


class JournalSemanticStop(RuntimeError):
    pass


def _ascii_upper(value: str | None) -> str:
    text = value or ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().split())


def _contains(text: str, keyword: str) -> bool:
    kw = _ascii_upper(keyword)
    if not kw:
        return False
    return re.search(rf"(?<![A-Z0-9]){re.escape(kw)}(?![A-Z0-9])", text) is not None


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("schema") != "JORNAL_OFICIAL_SEMANTIC_LAYERS_V1":
        raise JournalSemanticStop("TASK171_JOM_SEMANTIC_SCHEMA")
    rules = obj.get("rules", {})
    if rules.get("multi_label") is not True:
        raise JournalSemanticStop("TASK171_JOM_MULTI_LABEL")
    if rules.get("type_of_act_is_not_subject") is not True:
        raise JournalSemanticStop("TASK171_JOM_TYPE_SUBJECT_GUARD")
    if rules.get("journal_event_is_not_payment_proof_without_explicit_accounting_marker") is not True:
        raise JournalSemanticStop("TASK171_JOM_PAYMENT_GUARD")
    if rules.get("semantic_classification_is_not_policy_or_financial_identity") is not True:
        raise JournalSemanticStop("TASK171_JOM_IDENTITY_GUARD")
    return obj


def _matches(text: str, mapping: dict[str, list[str]]) -> tuple[list[str], dict[str, list[str]]]:
    labels: list[str] = []
    basis: dict[str, list[str]] = {}
    for label, keywords in mapping.items():
        found = [kw for kw in keywords if _contains(text, kw)]
        if found:
            labels.append(label)
            basis[label] = found
    return labels, basis


def classify_event(event: dict[str, Any], *, config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(config_path)
    event_type = str(event.get("event_type") or "")
    fields = [
        event_type,
        event.get("organ"),
        event.get("object_text"),
        event.get("excerpt_redacted"),
        event.get("act_number"),
        event.get("contract_number"),
        event.get("process_number"),
        event.get("bidding_modality"),
    ]
    text = _ascii_upper(" ".join(str(x) for x in fields if x))

    layers, layer_basis = _matches(text, cfg["evidence_layers"])
    for hint in cfg["event_type_layer_hints"].get(event_type, []):
        if hint not in layers:
            layers.append(hint)
            layer_basis.setdefault(hint, []).append(f"EVENT_TYPE:{event_type}")

    domains, domain_basis = _matches(text, cfg["policy_domains"])
    topics, topic_basis = _matches(text, cfg["education_topics"])
    stages, stage_basis = _matches(text, cfg["financial_stages"])

    if not layers:
        layers = [cfg["rules"]["unknown_evidence_layer"]]
    if not domains:
        domains = [cfg["rules"]["unknown_policy_domain"]]
    if not stages:
        stages = [cfg["rules"]["unknown_financial_stage"]]

    education_explicit = "EDUCATION" in domains or bool(topics)
    explicit_payment = "PAYMENT" in stages
    explicit_accounting = "ACCOUNTING_EXECUTION" in layers

    event_id = str(event.get("event_id") or "")
    semantic_id = "JOSEM_" + sha256(
        f"{event_id}|{cfg['version']}|{','.join(sorted(layers))}|{','.join(sorted(domains))}".encode("utf-8")
    ).hexdigest()[:20]

    return {
        "semantic_id": semantic_id,
        "semantic_schema": cfg["schema"],
        "event_id": event_id,
        "source_id": event.get("source_id"),
        "edition": event.get("edition"),
        "page_number": event.get("page_number"),
        "source_sha256": event.get("source_sha256"),
        "event_type": event_type,
        "policy_domains": sorted(domains),
        "evidence_layers": sorted(layers),
        "education_topics": sorted(topics),
        "financial_stages": sorted(stages),
        "education_or_school_relevance": "EXPLICIT" if education_explicit else "NOT_EXPLICIT",
        "explicit_accounting_execution_marker": explicit_accounting,
        "explicit_payment_marker": explicit_payment,
        "classification_basis": {
            "policy_domains": domain_basis,
            "evidence_layers": layer_basis,
            "education_topics": topic_basis,
            "financial_stages": stage_basis,
        },
        "semantic_classification_proves_policy_identity": False,
        "semantic_classification_proves_financial_identity": False,
        "semantic_classification_proves_payment": bool(explicit_payment and explicit_accounting),
        "review_required": domains == [cfg["rules"]["unknown_policy_domain"]],
    }


def validate_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(path)
    required_layers = {
        "NORMATIVE",
        "PLANNING",
        "BUDGET_AUTHORIZATION",
        "ACCOUNTING_EXECUTION",
        "PROCUREMENT_CONTRACT",
        "PERSONNEL",
        "SCHOOL_OR_SERVICE_OPERATION",
        "INFRASTRUCTURE",
        "GOVERNANCE",
    }
    if not required_layers <= set(cfg["evidence_layers"]):
        raise JournalSemanticStop("TASK171_JOM_REQUIRED_LAYER_MISSING")
    required_stages = {"PLANNING", "AUTHORIZATION", "COMMITMENT", "LIQUIDATION", "PAYMENT", "PROCUREMENT"}
    if not required_stages <= set(cfg["financial_stages"]):
        raise JournalSemanticStop("TASK171_JOM_FINANCIAL_STAGE_MISSING")
    return {
        "schema": "TASK171_JOM_SEMANTIC_VALIDATION_RESULT_V1",
        "status": "PASS",
        "evidence_layer_count": len(cfg["evidence_layers"]),
        "policy_domain_count": len(cfg["policy_domains"]),
        "education_topic_count": len(cfg["education_topics"]),
        "network": False,
        "drive_write": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate_config(), ensure_ascii=False, sort_keys=True))
