"""Validate TASK282 repo-local accounting identity evidence only; no network or remote effects."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.reconciliation.accounting_identity import (
    CommitmentKey,
    index_rows,
    namespace_collisions,
    require,
    resolve_accounting_cohort,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/task282_pncp_tce_offline_identity.v1.json"


def pinned_file(spec: dict, root: Path = ROOT) -> bytes:
    payload = (root / spec["path"]).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == spec["sha256"], "PINNED_SOURCE_DRIFT")
    return payload


def load_config() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    require(config["schema"] == "TASK282_PNCP_TCE_OFFLINE_IDENTITY_V1", "CONFIG_SCHEMA")
    require(config["issue"] == 901, "CONFIG_ISSUE")
    require(config["execution_class"] == "T0_OFFLINE_REPLAY", "EXECUTION_CLASS")
    require(config["effects_scope"] == "TASK282_LIBRARY_AND_REPLAY_RUNTIME_ONLY",
            "EFFECTS_SCOPE")
    require(config["effects"] == {
        "pncp_requests": 0, "tce_requests": 0, "drive_reads": 0,
        "drive_writes": 0, "publication": False, "task281_consumed": False,
    }, "OFFLINE_RUNTIME_EFFECTS_REQUIRED")
    require(config["procurement_promotion_allowed"] is False, "PROMOTION_FORBIDDEN")
    for spec in config["pinned_repository_inputs"].values():
        pinned_file(spec)
    return config


def load_fixture(config: dict | None = None) -> dict:
    config = config or load_config()
    fixture = json.loads(pinned_file(config["pinned_repository_inputs"]["real_fixture"]))
    require(fixture["schema"] == "TASK282_MINIMIZED_ACCOUNTING_FIXTURE_V4",
            "FIXTURE_SCHEMA")
    require(fixture["privacy"] == {
        "raw_supplier_identifier_persisted": False,
        "synthetic_supplier_identifiers_only": True,
        "official_detail_ids_synthetic": True,
        "amount_persisted": False,
        "expense_description_persisted": False,
        "history_text_persisted": False,
    }, "FIXTURE_PRIVACY")
    provenance = fixture["provenance"]
    require(provenance["authority"].startswith("Tribunal de Contas"), "FIXTURE_AUTHORITY")
    require(provenance["source_contract"] ==
            "config/task187_tcesp_rich_expenses_2026.v1.json", "FIXTURE_SOURCE_CONTRACT")
    require(provenance["raw_source_redistributed_here"] is False,
            "RAW_SOURCE_REDISTRIBUTION_FORBIDDEN")
    require(provenance["license_status"] == "NOT_ASSERTED_BY_TASK282",
            "FIXTURE_LICENSE_MUST_NOT_BE_INVENTED")
    require(fixture["source_csv_sha256"] == config["ledger"]["csv_sha256"],
            "FIXTURE_SOURCE_DRIFT")
    return fixture


def fixture_rows(config: dict | None = None) -> list[dict]:
    fixture = load_fixture(config)
    rows = [dict(record["row"]) for record in fixture["records"]]
    require(all(row.get("identificador_despesa", "").startswith("FIXTURE_SUPPLIER_")
                for row in rows), "FIXTURE_SUPPLIER_MUST_BE_SYNTHETIC")
    return rows


def repo_local_identity_audit(config: dict | None = None) -> dict:
    config = config or load_config()
    rows = fixture_rows(config)
    index = index_rows(rows)
    collisions = namespace_collisions(index)
    proof = config["repo_local_reproducibility"]
    expected_entities = sorted(proof["colliding_entities"])
    matching = [
        collision for collision in collisions
        if collision["number"] == proof["colliding_number"]
        and collision["original_year"] == proof["colliding_original_year"]
        and sorted(collision["entities"]) == expected_entities
    ]
    require(len(matching) == 1, "DIRECT_COLLISION_COUNTEREXAMPLE_MISSING")

    candidate = resolve_accounting_cohort(
        index,
        CommitmentKey("Limeira", "PREFEITURA MUNICIPAL DE LIMEIRA", 2026, "3286"),
    )
    require([obs["stage"] for obs in candidate["observations"]]
            == ["COMMITMENT", "LIQUIDATION", "PAYMENT"],
            "NEGATIVE_CONTROL_STAGE_DRIFT")
    require(candidate["procurement_identity"] == "UNRESOLVED",
            "PROCUREMENT_IDENTITY_MUST_REMAIN_UNRESOLVED")
    require(candidate["payment_attribution_authorized"] is False,
            "PAYMENT_ATTRIBUTION_MUST_REMAIN_BLOCKED")

    return {
        "schema": "TASK282_REPO_LOCAL_IDENTITY_AUDIT_V2",
        "status": "PASS_TASK282_REPO_LOCAL_IDENTITY_AUDIT",
        "collision_counterexample": matching[0],
        "canonical_claim":
            "NUMBER_YEAR_ALONE_IS_NOT_A_SAFE_ACCOUNTING_IDENTITY_ACROSS_ENTITIES",
        "exhaustive_source_collision_count_claimed": False,
        "negative_control": {
            "key": candidate["key"],
            "stages": [obs["stage"] for obs in candidate["observations"]],
            "official_detail_ids":
                [obs["official_detail_id"] for obs in candidate["observations"]],
            "procurement_identity": candidate["procurement_identity"],
            "payment_attribution_authorized":
                candidate["payment_attribution_authorized"],
        },
    }


def main() -> None:
    print(json.dumps(
        repo_local_identity_audit(),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ))


if __name__ == "__main__":
    main()
