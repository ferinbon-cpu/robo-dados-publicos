#!/usr/bin/env python3
"""Offline evidence gate; no source access, financial arithmetic or authorization."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_245_SIOPE_OFFICIAL_TEMPORAL_CONTRACT_ACQUISITION_0.8.0.json"
CONTRACT = ROOT / "config/siope_historical_financial_semantic_versioning.v2.json"
SUPPORT = EVIDENCE.with_suffix(".support.json")
TASK241 = ROOT / "docs/evidence/TASK_241_SIOPE_2016_2025_SEMANTIC_COMPARABILITY_0.8.0.json"
BASE = "e4ecf87afba21717844db5b28415f13d52e1e48c"
DIMENSIONS = ["field_identity", "concept", "unit", "scope", "stage", "aggregation", "period"]
YEARS = list(range(2016, 2025))
GAPS = {"G1_TEMPORAL_FIELD_CROSSWALK", "G2_MONETARY_UNIT", "G3_AGGREGATION_BOUNDARY"}
PASS = "PASS_TASK245_PARTIAL_10_INPUTS_6_METRICS_THREE_EXPLICIT_GAPS"
PRESERVED = {
    "release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE",
    "closed_annual_series": "2016-2024", "gold_2025": "BLOCKED_NOT_CALCULATED",
    "financial_metrics_1_to_6": "PARTIAL", "per_capita_metrics_7_to_8": "NON_COMPARABLE",
    "gold_authorized": False, "series_inclusion_authorized": False,
    "release_promotion_authorized": False, "historical_rewrite_authorized": False,
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def assess(aliases, years, dimensions, claims, breaks, metric_inputs):
    """Compute coverage of reviewed claims, never infer it from an alias name.

    This pure evaluator does not authenticate new evidence. validate_objects
    separately binds the only reviewed claims in this acquisition snapshot.
    """
    cells = {}
    seen = set()
    for claim in claims:
        require(claim["id"] not in seen, "duplicate claim identity")
        seen.add(claim["id"])
        require(claim.get("source_id") and claim.get("value") is not None, "unsupported claim")
        require(claim["dimension"] in dimensions, "unknown evidence dimension")
        require(claim["aliases"] and set(claim["aliases"]) <= set(aliases), "claim alias scope drift")
        require(claim["years"] and set(claim["years"]) <= set(years), "claim temporal scope drift")
        for alias in claim["aliases"]:
            for year in claim["years"]:
                key = (alias, year, claim["dimension"])
                require(key not in cells or cells[key] == claim["value"], "conflicting semantic claims")
                cells[key] = claim["value"]
    broken = set()
    for claim in breaks:
        require(claim.get("source_id") and claim.get("positive_semantic_break") is True,
                "absence or unrelated change cannot prove a target break")
        require(claim["aliases"] and set(claim["aliases"]) <= set(aliases), "break alias scope drift")
        require(claim["years"] and set(claim["years"]) <= set(years), "break temporal scope drift")
        broken.update(claim["aliases"])
    result = {}
    for alias in aliases:
        for dimension in set(dimensions) - {"period"}:
            values = [cells[(alias, y, dimension)] for y in years if (alias, y, dimension) in cells]
            require(alias in broken or not values or all(v == values[0] for v in values),
                    "semantic values differ across years; explicit break/adaptation review required")
        missing = {d: [y for y in years if (alias, y, d) not in cells] for d in dimensions}
        missing = {d: ys for d, ys in missing.items() if ys}
        status = "NOT_COMPARABLE" if alias in broken else "PARTIAL" if missing else "PROVEN_COMPARABLE"
        result[alias] = {"status": status, "missing": missing}
    metrics = {}
    for name, inputs in metric_inputs.items():
        require(inputs and set(inputs) <= set(aliases), "metric input drift")
        statuses = {result[a]["status"] for a in inputs}
        metrics[name] = ("NOT_COMPARABLE" if "NOT_COMPARABLE" in statuses else
                         "PARTIAL" if "PARTIAL" in statuses else "PROVEN_COMPARABLE")
    return {"inputs": result, "metrics": metrics}


def validate_objects(evidence, contract, support, task241):
    require(evidence.get("evidence_schema") == "TASK245_OFFICIAL_TEMPORAL_CONTRACT_ACQUISITION_V1", "evidence schema drift")
    require(contract.get("schema") == "SIOPE_HISTORICAL_FINANCIAL_SEMANTIC_VERSIONING_V2", "contract schema drift")
    require(evidence.get("base_main_sha") == contract.get("base_main_sha") == BASE, "base drift")
    aliases = [r["alias"] for r in task241["financial_inputs"]]
    metric_inputs = {r["id"]: r["inputs"] for r in task241["financial_gold_metrics_1_to_6"]}
    require(len(set(aliases)) == 10 and len(metric_inputs) == 6, "TASK241 scope drift")
    require(contract.get("aliases") == aliases and contract.get("metric_inputs") == metric_inputs, "input/dependency drift")
    require(contract.get("required_dimensions") == DIMENSIONS, "proof standard weakened")
    require(contract.get("historical_years") == YEARS and contract.get("reference_year") == 2025, "temporal range narrowed")
    scope = evidence.get("scope", {})
    require(scope.get("historical_years") == YEARS and scope.get("reference_year") == 2025 and scope.get("reference_period") == 6, "evidence temporal scope drift")
    require(contract.get("automatic_future_acquisition_authorized") is False, "future acquisition authorized")
    require(evidence.get("authorization", {}).get("automatic_future_acquisition_authorized") is False, "authorization scope drift")

    payload = (json.dumps(support, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    require(evidence.get("support_sha256") == contract.get("support_sha256") == digest, "reviewed support integrity failure")
    require(support.get("schema") == "TASK245_REVIEWED_OFFICIAL_SUPPORT_V1", "support schema drift")
    sources = support.get("sources", [])
    require(len(sources) == 8 and len({s["id"] for s in sources}) == 8, "source inventory drift")
    for source in sources:
        url = urlparse(source["official_url"])
        require(url.scheme == "https" and url.hostname in {"www.fnde.gov.br", "www.gov.br"}, "non-official source")
        require(url.hostname != "www.gov.br" or url.path.startswith("/fnde/"), "authority path drift")
        require(source["authority"] == "FNDE" and len(source["raw_sha256"]) == 64 and source["bytes"] > 0, "missing source fingerprint")
        int(source["raw_sha256"], 16)
        require(source.get("retrieved_at", "").startswith("2026-09-15T"), "acquisition timestamp drift")
    dictionary = support["dictionary"]
    require(dictionary["period_rule"] == {"annual_p1_through": 2016, "annual_p6_from": 2017}, "P1/P6 boundary drift")
    require(dictionary["unit_explicit"] is False and dictionary["exact_odata_alias_crosswalk_explicit"] is False,
            "dictionary promoted beyond its explicit statements")
    require(support["olinda"]["effective_year_range_stated"] is False and support["olinda"]["semantic_change_history_stated"] is False,
            "v1 or current metadata used as temporal proof")
    props = support["olinda"]["properties"]
    require(len(props) == 10 and {p["localizacao"]["nome"] for p in props} == set(aliases), "public property set drift")
    require(all(p["localizacao"]["descricao"] == p["localizacao"]["titulo"] == "" for p in props), "empty public semantics rewritten")
    require(all(p["tipo"] == ("texto" if p["localizacao"]["nome"].startswith("VAL_") else "decimal") for p in props), "observed transport types drift")
    require(support["analytical_catalog"]["exercise_ranges"] == [[2008, 2016], [2017, 2017], [2018, 2018], [2019, 2019]], "archive temporal association drift")
    require(support["analytical_catalog"]["archive_bytes_or_headers_acquired"] is False, "unread archive treated as acquired")
    require(support["metadata_catalog"]["package_contents_proven_by_listing"] is False, "catalog listing used as package contents")
    require(support["installer_catalog"]["complete_semantic_changelog"] is False, "release dates used as exhaustive change history")
    require(all(r["target_alias_break_proven"] is False for r in support["change_screening"]["observed_changes"]), "unrelated statutory change promoted to break")

    # The semantic review of these artifacts supports annual period roles only
    # at the exact historical alias/year layer. Vocabulary/UI anchors are kept
    # separately; they cannot silently fill the absent crosswalk, unit or scope.
    reviewed = [
        {"id": "ANNUAL_PERIOD_2016", "source_id": "DICTIONARY_2019", "dimension": "period", "aliases": aliases, "years": [2016], "value": {"period": 1, "role": "ANNUAL"}},
        {"id": "ANNUAL_PERIOD_2017_2024", "source_id": "DICTIONARY_2019", "dimension": "period", "aliases": aliases, "years": YEARS[1:], "value": {"period": 6, "role": "ANNUAL"}},
    ]
    require(evidence.get("temporal_claims") == contract.get("reviewed_temporal_claims") == reviewed,
            "unreviewed temporal proposition promoted")
    require(evidence.get("positive_target_breaks") == contract.get("reviewed_positive_target_breaks") == [], "target break fabricated")
    result = assess(aliases, YEARS, DIMENSIONS, reviewed, [], metric_inputs)
    rows = evidence.get("financial_inputs", [])
    require([r["alias"] for r in rows] == aliases, "missing/duplicate alias")
    stages = ["PREVISAO_ATUALIZADA", "REALIZADA", "DOTACAO_ATUALIZADA", "EMPENHADA", "LIQUIDADA", "PAGA", "DOTACAO_ATUALIZADA", "EMPENHADA", "LIQUIDADA", "PAGA"]
    scopes = ["RECEITA_TOTAL"] * 2 + ["DESPESA_TOTAL"] * 4 + ["DESPESA_EDUCACAO_FUNCAO_12"] * 4
    for i, row in enumerate(rows):
        require(row["reference_2025_concept"] == task241["financial_inputs"][i]["concept"], "accepted B2 concept drift")
        require(row["reference_2025_B2"] == "PROVEN_ALIAS_TO_CONCEPT_PRESERVED", "B2 reopened")
        require(row["crosswalk_status"] == "EXPECTED_TARGET_NOT_A_PROVEN_HISTORICAL_IDENTITY", "name similarity used as identity")
        require(row["expected_dictionary_column_literal"] == dictionary["literal_columns"][i], "dictionary field alignment drift")
        require(row["expected_stage"] == stages[i] and row["expected_scope"] == scopes[i], "stage or aggregation scope conflated")
        require(row["unit"] == {"historical_proof": "MISSING", "transport_type": "texto" if i < 6 else "decimal"}, "transport encoding used as monetary-unit proof")
        require(row["temporal_status"] == result["inputs"][row["alias"]]["status"], "input conclusion disagrees with coverage")
        require(set(row["missing_gap_ids"]) == GAPS, "input gap hidden")
    require(len(evidence["metrics"]) == 6 and {m["id"]: m["inputs"] for m in evidence["metrics"]} == metric_inputs, "metric mapping drift")
    require(all(m["status"] == result["metrics"][m["id"]] for m in evidence["metrics"]), "metric promoted with unresolved input")
    gaps = evidence.get("gaps", [])
    require(len(gaps) == 3 and {g["id"] for g in gaps} == GAPS, "closing propositions lost")
    require(all(g["years"] == YEARS and g["aliases"] == aliases and g["specific_missing_intervals"] and g["closing_artifact"] for g in gaps), "gap interval or closing artifact omitted")
    require(evidence["minimum_closing_evidence"]["artifact_status"] == "REQUIRED_CONTENT_SPECIFICATION_NOT_LOCATED_DOCUMENT", "required document misrepresented as found")
    require(evidence["minimum_closing_evidence"]["internal_implementation_required"] is False, "unjustified backend escalation")
    require(evidence["decision"]["status"] == contract["decision"] == "PARTIAL", "global decision drift")
    require(evidence["decision"]["financial_inputs_partial"] == sum(r["status"] == "PARTIAL" for r in result["inputs"].values())
            and evidence["decision"]["financial_metrics_partial"] == sum(s == "PARTIAL" for s in result["metrics"].values()),
            "decision totals disagree with coverage")
    require(evidence["decision"]["positive_semantic_break_proven"] is False, "summary fabricates a semantic break")
    require(evidence["decision"]["absence_of_change_is_continuity_proof"] is False, "absence promoted to proof")
    require(evidence.get("preserved_state") == contract.get("preserved_state") == PRESERVED, "protected current state drift")
    require(evidence["effects"] == {"official_document_reads": True, "financial_data_rows_collected": 0, "gold_calculations": 0, "drive_writes": 0, "external_publication": 0, "recurrence_created": 0, "installers_executed": 0}, "effects expanded")
    return result


def validate():
    evidence = load(EVIDENCE)
    validate_objects(evidence, load(CONTRACT), load(SUPPORT), load(TASK241))
    require(len(evidence["historical_snapshots"]) == 8, "historical preservation manifest drift")
    for snapshot in evidence["historical_snapshots"]:
        require(hashlib.sha256((ROOT / snapshot["path"]).read_bytes()).hexdigest() == snapshot["sha256"], "historical snapshot rewritten")
    return PASS


if __name__ == "__main__":
    print(validate())
