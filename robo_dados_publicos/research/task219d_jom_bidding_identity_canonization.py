from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219d_jom_bidding_identity_canonization.v1.json"


class Task219DError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219DError(code)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg["schema"] == "TASK219D_JOM_BIDDING_IDENTITY_CANONIZATION_V1", "TASK219D_SCHEMA")
    _stop(cfg["task"] == "TASK_219D" and cfg["issue"] == 691, "TASK219D_TASK")
    rules = cfg["rules"]
    _stop(rules["identity_grain"] == ["modality_id", "bidding_number", "bidding_year"], "TASK219D_GRAIN")
    _stop(rules["supplier_is_identity"] is False, "TASK219D_SUPPLIER")
    _stop(rules["date_is_identity"] is False, "TASK219D_DATE")
    _stop(rules["object_text_is_identity"] is False, "TASK219D_OBJECT")
    _stop(rules["semantic_similarity_is_identity"] is False, "TASK219D_SEMANTIC")
    _stop(rules["edital_publication_date_may_scope_search_only"] is True, "TASK219D_SEARCH_DATE")
    _stop(set(rules["modality_map"].values()) == {6, 8, 9}, "TASK219D_MODALITIES")
    _stop(not any(cfg["remote_effects"].values()), "TASK219D_REMOTE")
    return cfg


def _norm_modality(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().upper())


def _supplier(value: Any) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if len(digits) == 14 else None


def derive_bidding_anchors(
    events: Iterable[Mapping[str, Any]],
    cfg: Mapping[str, Any],
    *,
    corpus: str,
) -> list[dict[str, Any]]:
    rules = cfg["rules"]
    allowed = set(rules["allowed_event_types"])
    modality_map = {str(k): int(v) for k, v in rules["modality_map"].items()}
    pattern = re.compile(rules["complete_bidding_number_regex"])
    out: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") not in allowed:
            continue
        modality = _norm_modality(event.get("bidding_modality"))
        modality_id = modality_map.get(modality)
        if modality_id is None:
            continue
        match = pattern.fullmatch(str(event.get("bidding_number") or "").strip())
        if not match:
            continue
        number = int(match.group(1))
        year = int(match.group(2))
        row = {
            "corpus": corpus,
            "event_id": event["event_id"],
            "event_type": event.get("event_type"),
            "publication_date": event.get("publication_date"),
            "modality_id": modality_id,
            "modality_name_jom": modality,
            "bidding_number": number,
            "bidding_year": year,
            "supplier_cnpj": _supplier(event.get("cnpj")),
        }
        for key in ("edition", "source_id", "source_sha256"):
            if event.get(key) is not None:
                row[key] = event.get(key)
        out.append(row)
    return sorted(out, key=lambda r: (
        r["modality_id"], r["bidding_year"], r["bidding_number"],
        str(r.get("publication_date") or ""), r["event_id"],
    ))


def identity_key(row: Mapping[str, Any]) -> tuple[int, int, int]:
    return int(row["modality_id"]), int(row["bidding_number"]), int(row["bidding_year"])


def _counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = {identity_key(r) for r in rows}
    return {
        "anchor_rows": len(rows),
        "unique_identities": len(keys),
        "unique_by_modality": {
            str(mid): sum(1 for k in keys if k[0] == mid)
            for mid in (6, 8, 9)
        },
        "edital_rows": sum(1 for r in rows if r["event_type"] == "EDITAL"),
        "edital_identity_keys": len({
            identity_key(r) for r in rows if r["event_type"] == "EDITAL"
        }),
        "search_seed_count": len({
            (int(r["modality_id"]), str(r["publication_date"]))
            for r in rows
            if r["event_type"] == "EDITAL" and r.get("publication_date")
        }),
    }


def build_index(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in old + new:
        grouped[identity_key(row)].append(row)
    identities = []
    for key in sorted(grouped):
        rows = grouped[key]
        identities.append({
            "modality_id": key[0],
            "bidding_number": key[1],
            "bidding_year": key[2],
            "occurrence_count": len(rows),
            "event_count": len({r["event_id"] for r in rows}),
            "source_corpora": sorted({r["corpus"] for r in rows}),
            "event_types": sorted({str(r["event_type"]) for r in rows}),
            "publication_dates": sorted({str(r["publication_date"]) for r in rows if r.get("publication_date")}),
            "event_ids": sorted({str(r["event_id"]) for r in rows}),
            "supplier_cnpjs": sorted({str(r["supplier_cnpj"]) for r in rows if r.get("supplier_cnpj")}),
            "has_edital_seed": any(r["event_type"] == "EDITAL" and r.get("publication_date") for r in rows),
        })
    return {
        "schema": "TASK219D_FULL_99_EDITION_BIDDING_IDENTITY_INDEX_V1",
        "identity_grain": ["modality_id", "bidding_number", "bidding_year"],
        "identities": identities,
        "guards": {
            "supplier_is_identity": False,
            "date_is_identity": False,
            "object_text_is_identity": False,
            "semantic_similarity_is_identity": False,
        },
    }


def build_search_seeds(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[int, str], set[tuple[int, int, int]]] = defaultdict(set)
    event_ids: dict[tuple[int, str], set[str]] = defaultdict(set)
    for row in old + new:
        if row["event_type"] != "EDITAL" or not row.get("publication_date"):
            continue
        seed = (int(row["modality_id"]), str(row["publication_date"]))
        grouped[seed].add(identity_key(row))
        event_ids[seed].add(str(row["event_id"]))
    seeds = []
    for seed in sorted(grouped):
        modality_id, date = seed
        targets = sorted(grouped[seed])
        seeds.append({
            "modality_id": modality_id,
            "publication_date": date,
            "target_identity_count": len(targets),
            "target_identities": [
                {
                    "modality_id": k[0],
                    "bidding_number": k[1],
                    "bidding_year": k[2],
                }
                for k in targets
            ],
            "jom_edital_event_ids": sorted(event_ids[seed]),
            "date_role": "SEARCH_SCOPE_ONLY_NOT_IDENTITY",
        })
    return {
        "schema": "TASK219D_EDITAL_PNCP_DAILY_SEARCH_SEEDS_V1",
        "endpoint": "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
        "identity_grain": ["modality_id", "bidding_number", "bidding_year"],
        "search_scope_grain": ["modality_id", "publication_date"],
        "seed_count": len(seeds),
        "seeds": seeds,
        "guards": {
            "publication_date_is_identity": False,
            "exact_identity_match_required_after_retrieval": True,
            "supplier_is_identity": False,
        },
    }


def canonize(artifact_dir: Path, root: Path = ROOT) -> dict[str, Any]:
    cfg = load_config(root / "config/task219d_jom_bidding_identity_canonization.v1.json")
    source = cfg["source_artifact"]
    event_path = artifact_dir / "task219a_events_gold_sanitized.jsonl"
    _stop(event_path.is_file(), "TASK219D_EVENT_FILE")
    _stop(sha256_path(event_path) == source["events_sha256"], "TASK219D_EVENT_SHA")

    legacy_path = root / cfg["legacy_fixture"]
    _stop(sha256_path(legacy_path) == cfg["legacy_fixture_sha256"], "TASK219D_LEGACY_SHA")
    new_events = _load_jsonl(event_path)
    old_events = _load_jsonl(legacy_path)
    _stop(len(new_events) == 2408, "TASK219D_NEW_EVENT_ROWS")
    _stop(len(old_events) == 303, "TASK219D_OLD_EVENT_ROWS")

    new = derive_bidding_anchors(new_events, cfg, corpus="NEW_87_EDITIONS")
    old = derive_bidding_anchors(old_events, cfg, corpus="LEGACY_12_EDITIONS")
    nc, oc = _counts(new), _counts(old)
    exp = cfg["expected"]
    _stop(nc["anchor_rows"] == exp["new_anchor_rows"], "TASK219D_NEW_ANCHORS")
    _stop(nc["unique_identities"] == exp["new_unique_identities"], "TASK219D_NEW_UNIQUE")
    _stop(nc["unique_by_modality"] == exp["new_unique_by_modality"], "TASK219D_NEW_MODALITIES")
    _stop(nc["edital_rows"] == exp["new_edital_rows"], "TASK219D_NEW_EDITAL_ROWS")
    _stop(nc["edital_identity_keys"] == exp["new_edital_identity_keys"], "TASK219D_NEW_EDITAL_KEYS")
    _stop(nc["search_seed_count"] == exp["new_search_seed_count"], "TASK219D_NEW_SEEDS")
    _stop(oc["anchor_rows"] == exp["legacy_anchor_rows"], "TASK219D_OLD_ANCHORS")
    _stop(oc["unique_identities"] == exp["legacy_unique_identities"], "TASK219D_OLD_UNIQUE")
    _stop(oc["unique_by_modality"] == exp["legacy_unique_by_modality"], "TASK219D_OLD_MODALITIES")
    _stop(oc["edital_identity_keys"] == exp["legacy_edital_identity_keys"], "TASK219D_OLD_EDITAL_KEYS")

    old_keys = {identity_key(r) for r in old}
    new_keys = {identity_key(r) for r in new}
    overlap = old_keys & new_keys
    combined = old_keys | new_keys
    combined_by_modality = {
        str(mid): sum(1 for k in combined if k[0] == mid)
        for mid in (6, 8, 9)
    }
    _stop(len(overlap) == exp["overlap_unique_identities"], "TASK219D_OVERLAP")
    _stop(len(new_keys - old_keys) == exp["new_only_unique_identities"], "TASK219D_NEW_ONLY")
    _stop(len(combined) == exp["combined_unique_identities"], "TASK219D_COMBINED")
    _stop(combined_by_modality == exp["combined_unique_by_modality"], "TASK219D_COMBINED_MODALITIES")

    index = build_index(old, new)
    seeds = build_search_seeds(old, new)
    edital_combined = sum(1 for row in index["identities"] if row["has_edital_seed"])
    _stop(edital_combined == exp["combined_edital_identity_keys"], "TASK219D_COMBINED_EDITAL")
    _stop(seeds["seed_count"] == exp["combined_search_seed_count"], "TASK219D_COMBINED_SEEDS")

    outputs = cfg["outputs"]
    out_new = root / outputs["new_anchor_fixture"]
    out_index = root / outputs["combined_index"]
    out_seeds = root / outputs["search_seeds"]
    out_evidence = root / outputs["evidence"]
    for p in (out_new, out_index, out_seeds, out_evidence):
        p.parent.mkdir(parents=True, exist_ok=True)

    out_new.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in new),
        encoding="utf-8",
    )
    out_index.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_seeds.write_text(json.dumps(seeds, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence = {
        "task": "TASK_219D_JOM_BIDDING_IDENTITY_CANONIZATION",
        "issue": 691,
        "source": {
            "task219a_run_id": source["run_id"],
            "task219a_artifact_id": source["artifact_id"],
            "events_sha256": source["events_sha256"],
            "legacy_fixture": cfg["legacy_fixture"],
            "legacy_fixture_sha256": cfg["legacy_fixture_sha256"],
        },
        "counts": {
            "new": nc,
            "legacy": oc,
            "overlap_unique_identities": len(overlap),
            "new_only_unique_identities": len(new_keys - old_keys),
            "combined_unique_identities": len(combined),
            "combined_unique_by_modality": combined_by_modality,
            "combined_edital_identity_keys": edital_combined,
            "combined_daily_search_seed_count": seeds["seed_count"],
        },
        "overlap": [
            {"modality_id": k[0], "bidding_number": k[1], "bidding_year": k[2]}
            for k in sorted(overlap)
        ],
        "scientific_adjudication": {
            "identity_grain": ["modality_id", "bidding_number", "bidding_year"],
            "publication_date_role": "SEARCH_SCOPE_ONLY_NOT_IDENTITY",
            "supplier_is_identity": False,
            "weak_match_allowed": False,
            "pncp_match_proven_by_this_task": False,
            "end_to_end_jom_pncp_tce_chain_proven": False,
            "question_promotion_performed": False,
            "contextual_paths_before": 34,
            "contextual_paths_after": 34,
            "next_step": "BOUNDED_DAILY_PNCP_PUBLICATION_LOOKUP_FOR_35_MODALITY_DATE_SEEDS",
        },
        "outputs": {
            "new_anchor_fixture": outputs["new_anchor_fixture"],
            "new_anchor_fixture_sha256": sha256_path(out_new),
            "combined_index": outputs["combined_index"],
            "combined_index_sha256": sha256_path(out_index),
            "search_seeds": outputs["search_seeds"],
            "search_seeds_sha256": sha256_path(out_seeds),
        },
        "remote_effects": cfg["remote_effects"],
    }
    out_evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        raise SystemExit("usage: python -m robo_dados_publicos.research.task219d_jom_bidding_identity_canonization ARTIFACT_DIR")
    result = canonize(Path(args[0]))
    print("TASK219D_STATUS=PASS_BIDDING_IDENTITY_CANONIZATION")
    print("TASK219D_COMBINED_IDENTITIES=" + str(result["counts"]["combined_unique_identities"]))
    print("TASK219D_DAILY_SEARCH_SEEDS=" + str(result["counts"]["combined_daily_search_seed_count"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
