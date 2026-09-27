from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_planning_document_index
from robo_dados_publicos.analytics.task184_local_bundle import load_planning_rows

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task189_loa_substantive_2026.v1.json"


class Task189Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task189Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK189_LOA_SUBSTANTIVE_OVERLAY_2026_V1", "TASK189_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_EXISTING_CUSTODY_SUBSTANTIVE_OVERLAY", "TASK189_MODE")
    _stop(obj["source"]["silver_v2_sha256"] == "9f04a7202d03a58687d5382565777f15887b056ba28c65d9c01e226af7d3ef25", "TASK189_SILVER_SHA")
    _stop(obj["source"]["primary_jom_sha256"] == "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4", "TASK189_PRIMARY_SHA")
    _stop(len(obj.get("substantive_segments") or []) == 2, "TASK189_SEGMENT_COUNT")
    promotion = obj["promotion"]
    _stop(promotion["evidence_role"] == "PRIMARY_SUBSTANTIVE", "TASK189_ROLE")
    _stop(promotion["complete_loa_parse_claim"] is False, "TASK189_COMPLETE_PARSE_GUARD")
    _stop(promotion["whole_loa_substantive_coverage_claim"] is False, "TASK189_WHOLE_LOA_GUARD")
    _stop(promotion["accounting_execution_proven"] is False, "TASK189_EXECUTION_GUARD")
    _stop(promotion["eiti_financial_identity"] == "EVIDENCIA_INSUFICIENTE", "TASK189_EITI_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK189_REMOTE_EFFECT")
    return obj


def _sum_values(mapping: dict[str, str]) -> Decimal:
    return sum((Decimal(value) for value in mapping.values()), Decimal("0"))


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    seen = set()
    for segment in contract["substantive_segments"]:
        sid = segment["segment_id"]
        _stop(sid not in seen, "TASK189_DUPLICATE_SEGMENT")
        seen.add(sid)
        appropriation = Decimal(segment["appropriation_brl"])
        _stop(_sum_values(segment["expense_group_breakdown_brl"]) == appropriation, "TASK189_EXPENSE_GROUP_SUM")
        _stop(_sum_values(segment["funding_sources_brl"]) == appropriation, "TASK189_FUNDING_SUM")
        _stop(segment["program_code"] == "2001", "TASK189_PROGRAM")
        _stop(segment["organ_name"] == "SECRETARIA DE EDUCACAO", "TASK189_ORGAN")
        _stop(segment["eiti_specific"] is False, "TASK189_EITI_SPECIFIC")
    food = next(x for x in contract["substantive_segments"] if x["label"] == "ALIMENTACAO ESCOLAR")
    _stop(food["text_layer_amount_brl"] == "29000000.00", "TASK189_TEXT_MISMATCH")
    _stop(food["visual_source_amount_brl"] == "28000000.00", "TASK189_VISUAL_AMOUNT")
    _stop(food["appropriation_brl"] == food["visual_source_amount_brl"], "TASK189_VISUAL_SOURCE_TRUTH")
    return {
        "schema": "TASK189_LOA_SUBSTANTIVE_OVERLAY_VALIDATION_V1",
        "status": "PASS",
        "segment_count": 2,
        "complete_loa_parse_claim": False,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "network": False,
        "drive_write": False,
    }


def overlay_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    contract = load_contract(path)
    source = contract["source"]
    out = []
    for segment in contract["substantive_segments"]:
        funding = "; ".join(
            f"{name} R$ {Decimal(value):.2f}"
            for name, value in sorted(segment["funding_sources_brl"].items())
        )
        text = (
            f"LOA 2026: ação {segment['action_code']} {segment['label']}; "
            f"Programa {segment['program_code']}; órgão {segment['organ_name']}; "
            f"unidade {segment['unit_name']}; dotação R$ {Decimal(segment['appropriation_brl']):.2f}; "
            f"fontes: {funding}."
        )
        out.append(
            {
                "document_id": source["logical_document_id"],
                "document_type": source["document_type"],
                "period": source["period"],
                "evidence_role": "PRIMARY_SUBSTANTIVE",
                "locator": segment["locator"],
                "text_redacted": text,
                "policy_domains": ["PLANNING_BUDGET", "EDUCATION"],
                "topics": [
                    "BUDGET_AUTHORIZATION",
                    "PROGRAM_2001",
                    segment["label"].replace(" ", "_"),
                ],
                "substantive_status": "PRIMARY_SUBSTANTIVE_SCOPED_SEGMENT",
                "budget_authorization": {
                    "action_code": segment["action_code"],
                    "label": segment["label"],
                    "function": segment["function"],
                    "subfunction": segment["subfunction"],
                    "program_code": segment["program_code"],
                    "organ_code": segment["organ_code"],
                    "organ_name": segment["organ_name"],
                    "unit_code": segment["unit_code"],
                    "unit_name": segment["unit_name"],
                    "appropriation_brl": segment["appropriation_brl"],
                    "expense_group_breakdown_brl": dict(segment["expense_group_breakdown_brl"]),
                    "funding_sources_brl": dict(segment["funding_sources_brl"]),
                    "validation": segment["validation"],
                    "eiti_specific": False,
                },
                "observation_period": source["period"],
                "source_family": "LOA",
                "source_sha256": source["primary_jom_sha256"],
                "provenance_ref": f"{source['silver_v2_drive_id']}:{segment['segment_id']}",
                "quality_status": "VALIDATED",
                "caution": "LOA_AUTHORIZATION_NE_ACCOUNTING_EXECUTION_AND_SCOPED_SEGMENT_NE_COMPLETE_LOA_PARSE",
            }
        )
    return out


def build_planning_overlay(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validate_contract(contract_path)
    base = load_planning_rows()
    rows = [*base, *overlay_rows(contract_path)]
    product = build_planning_document_index(
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )
    product["overlay_scope"] = {
        "base_task184_rows": len(base),
        "task189_rows": 2,
        "complete_loa_parse_claim": False,
        "loa_primary_substantive_segments": 2,
        "loa_primary_substantive_scope": "VALIDATED_ACTION_SEGMENTS_ONLY",
        "accounting_execution_proven_by_loa": False,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
    }
    return product
