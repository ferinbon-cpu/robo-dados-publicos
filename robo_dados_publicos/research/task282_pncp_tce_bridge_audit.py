"""Read local pinned evidence only; stdout JSON, no fetch, persistence or live gate."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from robo_dados_publicos.accounting.tcesp_rich_expenses import (
    parse_csv_bytes, validate_real_payload,
)
from robo_dados_publicos.reconciliation.accounting_identity import (
    CommitmentKey, digest, index_rows, namespace_collisions, require,
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
    require(config["effects_scope"] ==
            "TASK282_LIBRARY_AND_REPLAY_RUNTIME_ONLY",
            "EFFECTS_SCOPE")
    require(config["effects"] == {
        "pncp_requests": 0, "tce_requests": 0, "drive_reads": 0,
        "drive_writes": 0, "publication": False, "task281_consumed": False,
    }, "OFFLINE_RUNTIME_EFFECTS_REQUIRED")
    require(config["procurement_promotion_allowed"] is False, "PROMOTION_FORBIDDEN")
    for spec in config["pinned_repository_inputs"].values():
        pinned_file(spec)
    return config


def collision_witness_audit(config: dict | None = None) -> dict:
    config = config or load_config()
    witness = json.loads(pinned_file(config["pinned_repository_inputs"]["collision_ranges"]))
    require(witness["schema"] == "TASK282_COLLISION_RANGES_V2", "COLLISION_WITNESS_SCHEMA")
    require(witness["source_csv_sha256"] == config["ledger"]["csv_sha256"],
            "COLLISION_WITNESS_SOURCE")
    require(witness["source_row_count_inherited_from_task187"] == config["repo_local_reproducibility"]["source_row_count_inherited_from_task187"],
            "COLLISION_WITNESS_ROW_COUNT")
    require(witness["collision_count"] == config["repo_local_reproducibility"]["collision_count"],
            "COLLISION_WITNESS_COUNT")
    require(len(witness["ranges"]) == config["repo_local_reproducibility"]["interval_count"],
            "COLLISION_WITNESS_INTERVAL_COUNT")
    entities = witness["entity_codes"]
    require(len(entities) == len(set(entities)) == 3, "COLLISION_ENTITY_CODES")
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
    require(len(expanded) == witness["collision_count"], "COLLISION_EXPANSION_COUNT")
    require(len({(year, number) for year, number, _ in expanded}) == len(expanded),
            "COLLISION_DUPLICATE_NUMBER_YEAR")
    require(all(len(codes) >= 2 for _, _, codes in expanded), "COLLISION_SCOPE")
    return {
        "schema": "TASK282_REPO_LOCAL_COLLISION_AUDIT_V1",
        "status": "PASS_TASK282_REPO_LOCAL_COLLISION_WITNESS",
        "source_csv_sha256": witness["source_csv_sha256"],
        "source_row_count_inherited_from_task187": witness["source_row_count_inherited_from_task187"],
        "collision_count": len(expanded),
        "interval_count": len(witness["ranges"]),
        "entity_codes": entities,
        "canonical_claim":
            "NUMBER_YEAR_ALONE_IS_NOT_A_SAFE_ACCOUNTING_IDENTITY_ACROSS_ENTITIES",
    }


def target_gaps(seeds: list[dict], coverage_end: str, rows: list[dict]) -> list[dict]:
    end = date.fromisoformat(coverage_end)
    result = []
    seen = set()
    for seed in sorted(seeds, key=lambda r: r["seq"]):
        expected = f'{seed["cnpj"]}-1-{seed["seq"]:06d}/{seed["year"]}'
        require(seed["control"] == expected and expected not in seen, "PURCHASE_IDENTITY_DRIFT")
        require(bool(re.fullmatch(r"[A-Z0-9]{12}[0-9]{2}-1-[0-9]{6}/[0-9]{4}", expected)),
                "PURCHASE_NAMESPACE")
        require(seed["exact_identity_proven"] is True, "JOM_PNCP_ANCHOR_NOT_PROVEN")
        seen.add(expected)
        # Literal, boundary-delimited diagnostic only. Neither presence nor absence proves identity.
        counts = {}
        for label, value in (("pncp_control", expected), ("jom_process", seed["jom_process"])):
            pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(value) + r"(?![A-Za-z0-9])")
            counts[label] = sum(bool(pattern.search(r["historico_despesa"])) for r in rows)
        published = seed["data_publicacao"][:10]
        result.append({
            "purchase_control": expected, "jom_event_id": seed["event_id"],
            "jom_process": seed["jom_process"], "pncp_process": seed["pncp_processo"],
            "same_process_literal": seed["jom_process"] == seed["pncp_processo"],
            "publication_date_in_detail": published,
            "closing_date_in_detail": seed["data_encerramento"][:10],
            "publication_after_ledger_coverage": date.fromisoformat(published) > end,
            "literal_history_occurrences": counts,
            "status": "UNRESOLVED",
            "missing_proposition": "THIS_PURCHASE_HAS_THIS_SCOPED_COMMITMENT",
            "required_witness": "OFFICIAL_TYPED_RELATION_WITH_ENTITY_ORIGINAL_YEAR_AND_COMMITMENT_NUMBER",
            "absence_or_future_execution_inference_allowed": False,
        })
    return result


def audit(csv_bytes: bytes) -> dict:
    config = load_config()
    require(hashlib.sha256(csv_bytes).hexdigest() == config["ledger"]["csv_sha256"],
            "LEDGER_BYTES_DRIFT")
    validate_real_payload(csv_bytes)
    rows = parse_csv_bytes(csv_bytes)
    fixture = json.loads(pinned_file(config["pinned_repository_inputs"]["real_fixture"]))
    require(fixture["source_csv_sha256"] == config["ledger"]["csv_sha256"], "FIXTURE_SOURCE_DRIFT")
    require(fixture["schema"] == "TASK282_MINIMIZED_ACCOUNTING_FIXTURE_V2",
            "FIXTURE_SCHEMA")
    require(fixture["privacy"] == {
        "raw_supplier_identifier_persisted": False,
        "amount_persisted": False,
        "expense_description_persisted": False,
        "history_text_persisted": False,
    }, "FIXTURE_PRIVACY")
    for record in fixture["records"]:
        ordinal = record["csv_record_ordinal_1based"]
        require(type(ordinal) is int and 1 <= ordinal <= len(rows), "FIXTURE_ORDINAL")
        actual = rows[ordinal - 1]
        expected = record["expected"]
        require(all(actual.get(field) == value for field, value in expected.items()),
                "FIXTURE_ROW_DRIFT")
    index = index_rows(rows)
    collisions = namespace_collisions(index)
    seeds = [json.loads(line) for line in pinned_file(
        config["pinned_repository_inputs"]["task264_seeds"]
    ).decode("utf-8").splitlines() if line.strip()]
    require(len(seeds) == 8, "SEED_COUNT")
    targets = target_gaps(seeds, config["ledger"]["coverage_end"], rows)
    months = sorted({int(r["mes_referencia"].strip()) for r in rows})
    require(months == config["ledger"]["months"], "COVERAGE_DRIFT")
    return {
        "schema": "TASK282_PNCP_TCE_OFFLINE_AUDIT_RESULT_V1",
        "base_main_sha": config["base_main_sha"], "issue": config["issue"],
        "execution_class": config["execution_class"],
        "effects_scope": config["effects_scope"],
        "effects": config["effects"],
        "status": "UNRESOLVED",
        "ledger": {
            "csv_sha256": config["ledger"]["csv_sha256"],
            "row_count": len(rows), "unique_official_detail_ids": len(rows),
            "months": months, "coverage_end": config["ledger"]["coverage_end"],
            "entity_row_counts": dict(sorted(Counter(r["ds_orgao"].strip() for r in rows).items())),
            "source_stage_counts": dict(sorted(Counter(r["tp_despesa"].strip() for r in rows).items())),
            "scoped_commitment_count": len(index),
            "unscoped_colliding_key_count": len(collisions),
            "unscoped_collisions_sha256": digest(collisions),
            "collision_samples": collisions[:5],
            "supplier_conflicts_within_scoped_commitment": 0,
            "supplier_identifier_is_expense_record_id": False,
        },
        "targets": targets,
        "negative_control": {
            "contract": "45/2026", "jom_process": "902.281/2025",
            "municipal_chain": "PROVEN_TASK219AA_TASK219AB_PRESERVED",
            "tda_typed_procurement": "E00010/2026",
            "tda_commitment": "03286-01",
            "claim": "TDA_03286_01_EQUALS_TCESP_3286_2026_IN_THE_SAME_ENTITY",
            "missing_proposition": "OFFICIAL_CROSS_SYSTEM_COMMITMENT_NAMESPACE_EQUIVALENCE",
            "result": resolve_accounting_cohort(index, CommitmentKey(
                "Limeira", "PREFEITURA MUNICIPAL DE LIMEIRA", 2026, "3286",
            )),
        },
        "remaining_edges": config["remaining_edges"],
        "production_identity_promoted": False,
        "individual_liquidation_to_payment_edge_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-csv", type=Path,
                        help="Optional extended replay using the already-custodied TASK187 CSV")
    args = parser.parse_args()
    repo_local = collision_witness_audit()
    if args.ledger_csv is None:
        print(json.dumps(repo_local, ensure_ascii=False, sort_keys=True, indent=2))
        return
    result = audit(args.ledger_csv.read_bytes())
    print(json.dumps({
        "repo_local_collision_audit": repo_local,
        "extended_custodied_replay": result,
        "extended_replay_role": "OPTIONAL_NOT_MERGE_GATE",
    }, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
