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
    require(config["effects"] == {
        "pncp_requests": 0, "tce_requests": 0, "drive_reads": 0,
        "drive_writes": 0, "publication": False, "task281_consumed": False,
    }, "OFFLINE_EFFECTS_REQUIRED")
    require(config["procurement_promotion_allowed"] is False, "PROMOTION_FORBIDDEN")
    for spec in config["pinned_repository_inputs"].values():
        pinned_file(spec)
    return config


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
    for record in fixture["records"]:
        ordinal = record["csv_record_ordinal_1based"]
        require(type(ordinal) is int and 1 <= ordinal <= len(rows), "FIXTURE_ORDINAL")
        require(record["row"] == rows[ordinal - 1], "FIXTURE_ROW_DRIFT")
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
        "effects": config["effects"], "status": "UNRESOLVED",
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
    parser.add_argument("--ledger-csv", required=True, type=Path)
    parser.add_argument("--check", type=Path, help="Compare with a frozen offline result")
    args = parser.parse_args()
    result = audit(args.ledger_csv.read_bytes())
    if args.check:
        require(result == json.loads(args.check.read_text(encoding="utf-8")), "EVIDENCE_DRIFT")
        print("PASS_TASK282_OFFLINE_REPLAY")
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
