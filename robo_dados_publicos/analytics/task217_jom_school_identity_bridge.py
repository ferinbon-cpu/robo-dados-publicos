from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task217_jom_school_identity_bridge.v1.json"


class Task217Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task217Stop(code)


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def _contains(text: str, phrase: str) -> bool:
    return f" {normalize_text(phrase)} " in f" {normalize_text(text)} "


def infrastructure_markers_for_text(
    text: str,
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> list[str]:
    """Return physical-infrastructure markers after deterministic abstract-usage exclusions."""
    cfg = load_config(config_path)
    normalized = normalize_text(text)
    out = []
    exclusions = cfg.get("infrastructure_marker_exclusions", {})
    for marker in cfg["infrastructure_markers"]:
        if not _contains(normalized, marker):
            continue
        if any(_contains(normalized, phrase) for phrase in exclusions.get(marker, [])):
            continue
        out.append(marker)
    return sorted(out)


def _alias_has_school_context(field_text: str, alias: str, cfg: Mapping[str, Any]) -> bool:
    """Require a school/unit anchor near the exact alias.

    Exact person/place names alone are insufficient because Limeira has non-school
    entities that share names with municipal schools (for example streets and a
    stadium). This is a deterministic disambiguation guard, not fuzzy matching.
    """
    tokens = normalize_text(field_text).split()
    alias_tokens = normalize_text(alias).split()
    if not tokens or not alias_tokens or len(alias_tokens) > len(tokens):
        return False
    window = int(cfg["school_identity"]["school_context_window_tokens"])
    anchors = [normalize_text(x) for x in cfg["school_identity"]["school_context_anchors"]]
    for start in range(0, len(tokens) - len(alias_tokens) + 1):
        if tokens[start : start + len(alias_tokens)] != alias_tokens:
            continue
        lo = max(0, start - window)
        hi = min(len(tokens), start + len(alias_tokens) + window)
        local = " ".join(tokens[lo:hi])
        if any(_contains(local, anchor) for anchor in anchors):
            return True
    return False


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK217_JOM_SCHOOL_IDENTITY_BRIDGE_V1", "TASK217_SCHEMA")
    _stop(obj.get("issue") == 680, "TASK217_ISSUE")
    _stop(
        obj.get("base_main_sha") == "34f93eb9f89e6a3ab4231bba2ad8c38155353ad1",
        "TASK217_BASE",
    )
    _stop(obj["school_identity"]["expected_school_count"] == 69, "TASK217_ROSTER_COUNT")
    _stop(obj["school_identity"]["fuzzy_matching_creates_identity"] is False, "TASK217_FUZZY_GUARD")
    _stop(obj["school_identity"]["semantic_similarity_creates_identity"] is False, "TASK217_SEMANTIC_GUARD")
    _stop(
        obj["promotion_policy"]["task018_consumed_authorization_may_be_silently_reused"] is False,
        "TASK217_AUTH_REUSE_GUARD",
    )
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK217_REMOTE_EFFECT")
    return obj


def _csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))


def load_school_roster(path: str | Path = DEFAULT_CONFIG) -> list[dict[str, str]]:
    cfg = load_config(path)
    strong = _csv_rows(ROOT / cfg["sources"]["roster_strong_57"])
    held = _csv_rows(ROOT / cfg["sources"]["roster_spatial_held_12"])
    _stop(len(strong) == cfg["school_identity"]["strong_spatial_rows"], "TASK217_STRONG_ROWS")
    _stop(len(held) == cfg["school_identity"]["spatial_held_rows"], "TASK217_HELD_ROWS")

    rows: list[dict[str, str]] = []
    for source_status, source_rows in (("SPATIAL_STRONG", strong), ("SPATIAL_HELD", held)):
        for row in source_rows:
            rows.append(
                {
                    "school_code": str(row["codigo_inep"]).strip(),
                    "school_name": " ".join(str(row["unidade"]).split()),
                    "spatial_status": source_status,
                }
            )
    rows.sort(key=lambda x: x["school_code"])
    _stop(len(rows) == cfg["school_identity"]["expected_school_count"], "TASK217_69_ROWS")
    _stop(len({r["school_code"] for r in rows}) == len(rows), "TASK217_UNIQUE_INEP")
    _stop(all(len(r["school_code"]) == 8 and r["school_code"].isdigit() for r in rows), "TASK217_INEP_FORMAT")
    return rows


def _school_aliases(name: str, cfg: Mapping[str, Any]) -> list[str]:
    generic = {normalize_text(x) for x in cfg["generic_school_references"]} | {"limeira"}
    raw = {normalize_text(name)}
    head = normalize_text(name.split(",", 1)[0].split("(", 1)[0])
    if head:
        raw.add(head)

    aliases: set[str] = set()
    prefixes = [normalize_text(x) + " " for x in cfg["school_identity"]["prefixes"]]
    min_tokens = int(cfg["school_identity"]["minimum_alias_tokens"])
    min_chars = int(cfg["school_identity"]["minimum_alias_chars"])

    def accept(value: str) -> None:
        if value in generic:
            return
        if len(value) < min_chars or len(value.split()) < min_tokens:
            return
        aliases.add(value)

    for value in raw:
        accept(value)
        for prefix in prefixes:
            if value.startswith(prefix):
                accept(value[len(prefix):].strip())
    return sorted(aliases)


def build_alias_index(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(path)
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for school in load_school_roster(path):
        for alias in _school_aliases(school["school_name"], cfg):
            index[alias].append(school)

    ambiguous = {
        alias: sorted({row["school_code"] for row in rows})
        for alias, rows in index.items()
        if len({row["school_code"] for row in rows}) > 1
    }
    _stop(
        len(index) == cfg["school_identity"]["expected_unique_alias_count"],
        "TASK217_ALIAS_COUNT_DRIFT",
    )
    _stop(
        len(ambiguous) == cfg["school_identity"]["expected_ambiguous_alias_count"],
        "TASK217_ALIAS_AMBIGUITY_DRIFT",
    )
    return {"aliases": dict(index), "ambiguous": ambiguous}


def load_jom_events(path: str | Path = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    cfg = load_config(path)
    rows = [
        json.loads(line)
        for line in (ROOT / cfg["sources"]["jom_fixture"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _stop(len(rows) == cfg["scope"]["current_jom_rows"], "TASK217_JOM_ROWS")
    _stop(len({row["event_id"] for row in rows}) == len(rows), "TASK217_JOM_EVENT_ID")
    _stop(min(row["publication_date"] for row in rows) == cfg["scope"]["publication_min"], "TASK217_JOM_MIN")
    _stop(max(row["publication_date"] for row in rows) == cfg["scope"]["publication_max"], "TASK217_JOM_MAX")
    return rows


def classify_event_school_identity(
    event: Mapping[str, Any],
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    alias_index = build_alias_index(config_path)["aliases"]
    accepted_fields = cfg["school_identity"]["accepted_fields"]

    school_hits: dict[str, dict[str, Any]] = {}
    for field in accepted_fields:
        field_text = normalize_text(event.get(field))
        if not field_text:
            continue
        padded = f" {field_text} "
        for alias, schools in alias_index.items():
            if f" {alias} " not in padded:
                continue
            if not _alias_has_school_context(field_text, alias, cfg):
                continue
            for school in schools:
                hit = school_hits.setdefault(
                    school["school_code"],
                    {
                        "school_code": school["school_code"],
                        "school_name": school["school_name"],
                        "spatial_status": school["spatial_status"],
                        "matches": [],
                    },
                )
                hit["matches"].append(
                    {
                        "field": field,
                        "alias": alias,
                        "school_context_guard": "PASS_NEARBY_SCHOOL_ANCHOR",
                    }
                )

    combined_text = " ".join(normalize_text(event.get(field)) for field in accepted_fields)
    infrastructure_markers = infrastructure_markers_for_text(
        combined_text,
        config_path=config_path,
    )
    generic_markers = [
        marker for marker in cfg["generic_school_references"] if _contains(combined_text, marker)
    ]

    if len(school_hits) == 1:
        status = "RESOLVED_EXACT_SCHOOL"
        resolved = next(iter(school_hits.values()))
    elif len(school_hits) > 1:
        status = "AMBIGUOUS_EXACT_SCHOOL"
        resolved = None
    elif generic_markers:
        status = "GENERIC_SCHOOL_REFERENCE"
        resolved = None
    else:
        status = "NO_SCHOOL_REFERENCE"
        resolved = None

    return {
        "event_id": event.get("event_id"),
        "edition": event.get("edition"),
        "publication_date": event.get("publication_date"),
        "page_number": event.get("page_number"),
        "source_sha256": event.get("source_sha256"),
        "school_identity_status": status,
        "resolved_school": resolved,
        "candidate_schools": sorted(school_hits.values(), key=lambda x: x["school_code"]),
        "generic_school_markers": sorted(generic_markers),
        "infrastructure_candidate": bool(infrastructure_markers),
        "infrastructure_markers": sorted(infrastructure_markers),
        "school_identity_created_by_fuzzy_matching": False,
        "infrastructure_text_created_school_identity": False,
        "contextual_school_anchor_required": True,
        "bare_alias_created_school_identity": False,
    }


def build_current_corpus_audit(
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    classified = [
        classify_event_school_identity(row, config_path=config_path)
        for row in load_jom_events(config_path)
    ]

    def count(status: str) -> int:
        return sum(row["school_identity_status"] == status for row in classified)

    exact_infra = [
        row
        for row in classified
        if row["school_identity_status"] == "RESOLVED_EXACT_SCHOOL"
        and row["infrastructure_candidate"]
    ]
    generic_infra = [
        row
        for row in classified
        if row["school_identity_status"] == "GENERIC_SCHOOL_REFERENCE"
        and row["infrastructure_candidate"]
    ]
    infra = [row for row in classified if row["infrastructure_candidate"]]
    expected = cfg["expected_current_corpus_audit"]

    observed = {
        "exact_school_event_count": count("RESOLVED_EXACT_SCHOOL"),
        "ambiguous_school_event_count": count("AMBIGUOUS_EXACT_SCHOOL"),
        "infrastructure_candidate_count": len(infra),
        "exact_school_infrastructure_count": len(exact_infra),
        "generic_school_infrastructure_count": len(generic_infra),
        "generic_school_infrastructure_event_ids": [row["event_id"] for row in generic_infra],
    }
    _stop(observed == expected, "TASK217_CURRENT_CORPUS_AUDIT_DRIFT")

    generic_evidence = [
        {
            "event_id": row["event_id"],
            "edition": row["edition"],
            "publication_date": row["publication_date"],
            "page_number": row["page_number"],
            "source_sha256": row["source_sha256"],
            "generic_school_markers": row["generic_school_markers"],
            "infrastructure_markers": row["infrastructure_markers"],
        }
        for row in generic_infra
    ]

    material = {
        "schema": "TASK217A_JOM_SCHOOL_IDENTITY_AUDIT_V1",
        "scope": dict(cfg["scope"]),
        "roster": {
            "school_count": len(load_school_roster(config_path)),
            "unique_alias_count": len(build_alias_index(config_path)["aliases"]),
            "ambiguous_alias_count": len(build_alias_index(config_path)["ambiguous"]),
        },
        "observed": observed,
        "resolved_infrastructure_events": exact_infra,
        "generic_unassigned_infrastructure_events": generic_evidence,
        "promotion": {
            "question_id": "INFRA_Q2",
            "status": "BLOCKED_NO_EXACT_NAMED_SCHOOL_INFRASTRUCTURE_EVENT_IN_CURRENT_CORPUS",
            "contextual_paths_before": cfg["promotion_policy"]["contextual_paths_before"],
            "contextual_paths_after": cfg["promotion_policy"]["contextual_paths_after"],
            "live_expansion_required_for_next_evidence": True,
            "live_expansion_authorized_by_this_task": False,
        },
        "guards": {
            "generic_reference_assigned_to_school": False,
            "fuzzy_identity_used": False,
            "semantic_similarity_identity_used": False,
            "task018_consumed_authorization_reused": False,
            "absence_beyond_current_corpus_inferred": False,
        },
        "remote_effects": dict(cfg["remote_effects"]),
    }
    canonical = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**material, "audit_sha256": hashlib.sha256(canonical).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(build_current_corpus_audit(), ensure_ascii=False, indent=2, sort_keys=True))
