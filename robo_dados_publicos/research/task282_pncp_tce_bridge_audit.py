"""Validate TASK282 repo-local collision evidence only; no network or remote effects."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.reconciliation.accounting_identity import require

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
    require("collision_ranges" in config["pinned_repository_inputs"],
            "COLLISION_WITNESS_PIN_MISSING")
    collision_pin = config["pinned_repository_inputs"]["collision_ranges"]
    require(collision_pin["path"] == config["repo_local_reproducibility"]["collision_witness_path"],
            "COLLISION_WITNESS_PATH_DRIFT")
    require(collision_pin["sha256"] == config["repo_local_reproducibility"]["collision_witness_sha256"],
            "COLLISION_WITNESS_SHA_DRIFT")
    for spec in config["pinned_repository_inputs"].values():
        pinned_file(spec)
    return config


def collision_witness_audit(config: dict | None = None) -> dict:
    config = config or load_config()
    witness = json.loads(pinned_file(config["pinned_repository_inputs"]["collision_ranges"]))
    require(witness["schema"] == "TASK282_COLLISION_RANGES_V3", "COLLISION_WITNESS_SCHEMA")
    require(witness["source_csv_sha256"] == config["ledger"]["csv_sha256"],
            "COLLISION_WITNESS_SOURCE")
    require(
        witness["source_row_count_inherited_from_task187"]
        == config["repo_local_reproducibility"]["source_row_count_inherited_from_task187"],
        "COLLISION_WITNESS_ROW_COUNT",
    )
    require(
        witness["collision_witness_count"]
        == config["repo_local_reproducibility"]["collision_witness_count"],
        "COLLISION_WITNESS_COUNT",
    )
    require(witness["exhaustive_source_collision_count_claimed"] is False,
            "NO_EXHAUSTIVE_COLLISION_CLAIM")
    require(len(witness["ranges"]) == config["repo_local_reproducibility"]["interval_count"],
            "COLLISION_WITNESS_INTERVAL_COUNT")
    entities = witness["entity_codes"]
    require(len(entities) == len(set(entities)) == 3, "COLLISION_ENTITY_CODES")
    fixture = json.loads(pinned_file(config["pinned_repository_inputs"]["real_fixture"]))
    fixture_entities = {record["expected"]["ds_orgao"] for record in fixture["records"]}
    require(fixture_entities.issubset(set(entities)), "COLLISION_FIXTURE_ENTITY_DRIFT")

    expanded: list[tuple[int, int, tuple[int, ...]]] = []
    for item in witness["ranges"]:
        year, start, end, codes = item["y"], item["a"], item["b"], tuple(item["e"])
        require(type(year) is int and 1900 <= year <= 2099, "COLLISION_YEAR")
        require(type(start) is int and type(end) is int and 1 <= start <= end,
                "COLLISION_RANGE")
        require(len(codes) >= 2 and len(codes) == len(set(codes)),
                "COLLISION_ENTITY_CARDINALITY")
        require(all(type(code) is int and 0 <= code < len(entities) for code in codes),
                "COLLISION_ENTITY_CODE")
        expanded.extend((year, number, codes) for number in range(start, end + 1))

    require(len(expanded) == witness["collision_witness_count"], "COLLISION_EXPANSION_COUNT")
    require(len({(year, number) for year, number, _ in expanded}) == len(expanded),
            "COLLISION_DUPLICATE_NUMBER_YEAR")

    return {
        "schema": "TASK282_REPO_LOCAL_COLLISION_AUDIT_V1",
        "status": "PASS_TASK282_REPO_LOCAL_COLLISION_WITNESS",
        "source_csv_sha256": witness["source_csv_sha256"],
        "source_row_count_inherited_from_task187":
            witness["source_row_count_inherited_from_task187"],
        "collision_witness_count": len(expanded),
        "exhaustive_source_collision_count_claimed": False,
        "interval_count": len(witness["ranges"]),
        "entity_codes": entities,
        "canonical_claim":
            "NUMBER_YEAR_ALONE_IS_NOT_A_SAFE_ACCOUNTING_IDENTITY_ACROSS_ENTITIES",
    }


def main() -> None:
    print(json.dumps(
        collision_witness_audit(),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ))


if __name__ == "__main__":
    main()
