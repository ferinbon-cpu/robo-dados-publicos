from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_question_answerability,
)
from robo_dados_publicos.analytics.task184_local_bundle import (
    _with_catalog,
    build_task184_bundle,
)
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import (
    build_planning_overlay,
)
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import (
    build_task196_products,
)
from robo_dados_publicos.analytics.task200a_jom_personnel_redigest import (
    build_task200a_jom_product,
)
from robo_dados_publicos.analytics.task201b_inep_workforce_materialization import (
    build_task201b_school_indicator,
)
from robo_dados_publicos.analytics.task202_equity_missingness_aware_gate import (
    build_task202_territory_profile,
)


ROOT = Path(__file__).resolve().parents[2]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"

CANONICAL_PRODUCT_SET = {
    "SCHOOL_INDICATOR_SERIES",
    "JOM_EVENT_INDEX",
    "ACCOUNTING_LEDGER",
    "REVENUE_LEDGER",
    "FISCAL_SERIES",
    "PLANNING_DOCUMENT_INDEX",
    "QUERY_PRODUCT_CATALOG",
    "TERRITORY_PROFILE",
}


class CurrentObservatoryBundleStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise CurrentObservatoryBundleStop(code)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _accounting_shell(*, generated_at: str, software_version: str) -> dict[str, Any]:
    evidence = _load(TASK188)
    ledger = evidence["accounting_ledger"]
    _stop(ledger["row_count"] == 39783, "CURRENT_BUNDLE_ACCOUNTING_DECLARED_ROWS")
    _stop(bool(ledger["snapshot_drive_id"]), "CURRENT_BUNDLE_ACCOUNTING_DRIVE_ID")
    _stop(bool(ledger["manifest_drive_id"]), "CURRENT_BUNDLE_ACCOUNTING_MANIFEST_ID")
    return {
        "product_name": "ACCOUNTING_LEDGER",
        "product_schema": "ACCOUNTING_LEDGER_V1",
        "snapshot_id": ledger["snapshot_id"],
        "content_sha256": ledger["content_sha256"],
        "row_count": ledger["row_count"],
        "generated_at": generated_at,
        "software_version": software_version,
        "rows": [],
        "capabilities": list(ledger["capabilities"]),
        "observed_stages": list(ledger["observed_stages"]),
        "local_payload_state": "REMOTE_SNAPSHOT_METADATA_ONLY_IN_REPOSITORY",
        "local_row_count": 0,
        "remote_snapshot_drive_id": ledger["snapshot_drive_id"],
        "remote_manifest_drive_id": ledger["manifest_drive_id"],
        "source_evidence_path": str(TASK188.relative_to(ROOT)),
    }


def _revenue_shell(*, generated_at: str, software_version: str) -> dict[str, Any]:
    evidence = _load(TASK186)
    ledger = evidence["revenue_ledger"]
    _stop(ledger["row_count"] == 2286, "CURRENT_BUNDLE_REVENUE_DECLARED_ROWS")
    _stop(bool(ledger["drive_id"]), "CURRENT_BUNDLE_REVENUE_DRIVE_ID")
    _stop(bool(ledger["manifest_drive_id"]), "CURRENT_BUNDLE_REVENUE_MANIFEST_ID")
    return {
        "product_name": "REVENUE_LEDGER",
        "product_schema": ledger["product_schema"],
        "snapshot_id": ledger["snapshot_id"],
        "content_sha256": ledger["content_sha256"],
        "row_count": ledger["row_count"],
        "generated_at": generated_at,
        "software_version": software_version,
        "rows": [],
        "capabilities": list(ledger["capabilities"]),
        "local_payload_state": "REMOTE_SNAPSHOT_METADATA_ONLY_IN_REPOSITORY",
        "local_row_count": 0,
        "remote_snapshot_drive_id": ledger["drive_id"],
        "remote_manifest_drive_id": ledger["manifest_drive_id"],
        "source_evidence_path": str(TASK186.relative_to(ROOT)),
    }


def build_current_products(
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, dict[str, Any]]:
    """Assemble the post-TASK202 canonical observatory bundle without test helpers."""
    _stop(bool(generated_at), "CURRENT_BUNDLE_GENERATED_AT")
    _stop(bool(software_version), "CURRENT_BUNDLE_SOFTWARE_VERSION")

    task184 = build_task184_bundle(
        generated_at=generated_at,
        software_version=software_version,
    )
    substantive = {
        name: product
        for name, product in task184["products"].items()
        if name not in {
            "QUERY_PRODUCT_CATALOG",
            "PLANNING_DOCUMENT_INDEX",
            "JOM_EVENT_INDEX",
        }
    }

    task196 = build_task196_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    substantive["SCHOOL_INDICATOR_SERIES"] = build_task201b_school_indicator(
        generated_at=generated_at,
        software_version=software_version,
    )["SCHOOL_INDICATOR_SERIES"]
    substantive["FISCAL_SERIES"] = task196["FISCAL_SERIES"]

    products = _with_catalog(
        {
            **substantive,
            "JOM_EVENT_INDEX": build_task200a_jom_product(
                generated_at=generated_at,
                software_version=software_version,
            ),
            "PLANNING_DOCUMENT_INDEX": build_planning_overlay(
                generated_at=generated_at,
                software_version=software_version,
            ),
            "ACCOUNTING_LEDGER": _accounting_shell(
                generated_at=generated_at,
                software_version=software_version,
            ),
            "REVENUE_LEDGER": _revenue_shell(
                generated_at=generated_at,
                software_version=software_version,
            ),
            "TERRITORY_PROFILE": build_task202_territory_profile(
                generated_at=generated_at,
                software_version=software_version,
            ),
        },
        generated_at=generated_at,
        software_version=software_version,
    )
    _stop(set(products) == CANONICAL_PRODUCT_SET, "CURRENT_BUNDLE_PRODUCT_SET")
    return products


def _payload_inventory(products: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for name in sorted(products):
        product = products[name]
        local_count = len(product.get("rows", []))
        declared_count = int(product.get("row_count") or 0)
        if local_count:
            payload_state = "LOCAL_ROWS_PRESENT"
        elif declared_count:
            payload_state = "REMOTE_SNAPSHOT_METADATA_ONLY"
        else:
            payload_state = "EMPTY_PRODUCT"
        rows.append(
            {
                "product_name": name,
                "snapshot_id": str(product.get("snapshot_id") or ""),
                "content_sha256": str(product.get("content_sha256") or ""),
                "declared_row_count": declared_count,
                "local_row_count": local_count,
                "payload_state": payload_state,
                "remote_snapshot_drive_id": product.get("remote_snapshot_drive_id"),
                "remote_manifest_drive_id": product.get("remote_manifest_drive_id"),
            }
        )
    return rows


def build_current_bundle(
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    answerability = current_question_answerability(products)
    _stop(answerability["question_count"] == 38, "CURRENT_BUNDLE_QUESTION_COUNT")
    _stop(
        answerability["status_counts"] == {"MATERIALIZED_ANSWERABLE": 38},
        "CURRENT_BUNDLE_ANSWERABILITY",
    )
    inventory = _payload_inventory(products)
    by_name = {row["product_name"]: row for row in inventory}
    _stop(
        by_name["ACCOUNTING_LEDGER"]["declared_row_count"] == 39783
        and by_name["ACCOUNTING_LEDGER"]["local_row_count"] == 0,
        "CURRENT_BUNDLE_ACCOUNTING_PAYLOAD_BOUNDARY",
    )
    _stop(
        by_name["REVENUE_LEDGER"]["declared_row_count"] == 2286
        and by_name["REVENUE_LEDGER"]["local_row_count"] == 0,
        "CURRENT_BUNDLE_REVENUE_PAYLOAD_BOUNDARY",
    )
    return {
        "schema": "CURRENT_OBSERVATORY_CANONICAL_BUNDLE_V1",
        "generated_at": generated_at,
        "software_version": software_version,
        "product_count": len(products),
        "products": products,
        "payload_inventory": inventory,
        "answerability": answerability,
        "semantics": {
            "canonical_answerability_version": 4,
            "semantic_answerability_equals_local_renderability": False,
            "capability_metadata_may_supply_numeric_value": False,
            "llm_may_fill_missing_numeric_evidence": False,
        },
        "remote_effects": {
            "network": False,
            "drive_read": False,
            "drive_write": False,
            "serving": False,
            "publication": False,
            "schedule": False,
            "recurrence": False,
        },
    }
