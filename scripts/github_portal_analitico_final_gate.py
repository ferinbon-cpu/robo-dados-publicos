#!/usr/bin/env python3
"""Final fail-closed offline gate for the Data Studio + Google Sites portal design."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_STATUS = "PASS_PORTAL_ANALITICO_FINAL_OFFLINE_READY_FOR_BUILD"
EXPECTED_BASE = "260bd81ba58aca4fba5efced81b410e54c81a074"
EXPECTED_DATASETS = (
    "BI_SIOPE_SERIES",
    "BI_JORNAL_EVENTOS",
    "BI_RECONCILIACAO",
    "BI_FONTES_STATUS",
    "BI_EXECUCOES_ROBO",
    "BI_DICIONARIO",
)
EXPECTED_NAMES = {f"{dataset}__SERVING" for dataset in EXPECTED_DATASETS}


def load(path: str) -> dict:
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise SystemExit(f"STOP_PORTAL_INVALID_JSON:{path}") from exc


def _as_fields(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def schema_fields(analytics: dict) -> dict[str, set[str]]:
    result = {}
    for dataset in analytics.get("datasets", []):
        dataset_id = dataset.get("dataset_id")
        fields = dataset.get("fields", [])
        if not isinstance(dataset_id, str) or not isinstance(fields, list):
            continue
        result[dataset_id] = {
            field.get("name") for field in fields
            if isinstance(field, dict) and isinstance(field.get("name"), str)
        }
    return result


def validate_field_references(contract: dict, analytics: dict) -> list[str]:
    """Return errors for any portal source/field not present in BI-001."""
    errors: list[str] = []
    fields = schema_fields(analytics)
    known_sources = set(fields)
    calculated_by_source: dict[str, set[str]] = {source: set() for source in known_sources}

    for calc in contract.get("calculated_fields", []):
        if not isinstance(calc, dict):
            errors.append("calculated_fields:malformed")
            continue
        source = calc.get("source")
        name = calc.get("name")
        if source not in known_sources:
            errors.append(f"calculated_field:{name}:unknown_source:{source}")
        elif not isinstance(name, str) or not name:
            errors.append(f"calculated_field:invalid_name:{name}")
        else:
            calculated_by_source[source].add(name)

    def allowed(source: str) -> set[str]:
        return fields.get(source, set()) | calculated_by_source.get(source, set())

    for section in ("charts", "tables", "filters"):
        for item in contract.get(section, []):
            if not isinstance(item, dict):
                errors.append(f"{section}:malformed")
                continue
            item_id = item.get("id") or item.get("name") or "unnamed"
            source = item.get("source")
            if source not in known_sources:
                errors.append(f"{section}:{item_id}:unknown_source:{source}")
                continue
            refs = []
            if section == "charts":
                refs.extend(_as_fields(item.get("dimension")))
                refs.extend(_as_fields(item.get("metric")))
                refs.extend(_as_fields(item.get("filter")))
            elif section == "tables":
                refs.extend(_as_fields(item.get("columns")))
            else:
                refs.extend(_as_fields(item.get("field")))
            for field in refs:
                if not isinstance(field, str) or field not in allowed(source):
                    errors.append(f"{section}:{item_id}:unknown_field:{field}:source:{source}")

    for page in contract.get("pages", []):
        page_id = page.get("id", "unnamed") if isinstance(page, dict) else "malformed"
        for source in page.get("sources", []) if isinstance(page, dict) else []:
            if source not in known_sources:
                errors.append(f"pages:{page_id}:unknown_source:{source}")

    return errors


def main() -> bool:
    contract = load("config/bi/portal_analitico_final.v1.json")
    evidence = load("docs/evidence/PORTAL_ANALITICO_FINAL_0.8.0.json")
    analytics = load("config/bi/analytics_output.v1.json")
    docs = [
        ROOT / "docs/bi/PORTAL_ANALITICO_FINAL.md",
        ROOT / "docs/bi/DATA_STUDIO_BUILD_RUNBOOK.md",
        ROOT / "docs/bi/GOOGLE_SITES_BUILD_RUNBOOK.md",
        ROOT / "docs/bi/PORTAL_QA_CHECKLIST.md",
    ]
    doc_text = "\n".join(path.read_text(encoding="utf-8") for path in docs if path.exists())
    effects = contract.get("remote_effects", {})
    names = {item.get("serving_name") for item in contract.get("datasets", [])}
    dataset_ids = {item.get("dataset_id") for item in contract.get("datasets", [])}
    analytics_ids = {item.get("dataset_id") for item in analytics.get("datasets", [])}
    cautions = set(contract.get("semantic_cautions", []))
    field_errors = validate_field_references(contract, analytics)
    workflow = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    future = (
        contract.get("workspace_studio_future", {}),
        contract.get("bigquery_future", {}),
        contract.get("appsheet_future", {}),
    )

    checks = {
        "base_sha_exact": contract.get("base_main_sha") == evidence.get("base_main_sha") == EXPECTED_BASE,
        "tier": contract.get("tier") == evidence.get("tier") == "T0_OFFLINE_PORTAL_ANALYTICS_DESIGN",
        "status": contract.get("status") == evidence.get("status") == EXPECTED_STATUS,
        "six_exact_servings": (
            contract.get("dataset_count") == evidence.get("dataset_count") == 6
            and len(contract.get("datasets", [])) == 6
            and names == EXPECTED_NAMES
            and dataset_ids == analytics_ids == set(EXPECTED_DATASETS)
            and all(item.get("analytical_tab") == "DATA" and item.get("audit_tab") == "META"
                    for item in contract.get("datasets", []))
        ),
        "five_pages": (
            contract.get("data_studio_report", {}).get("page_count")
            == evidence.get("data_studio_page_count") == 5
            and len(contract.get("pages", [])) == 5
        ),
        "schema_field_references": not field_errors,
        "no_calculated_fields_v1": contract.get("calculated_fields") == [],
        "sites_planned": contract.get("google_sites", {}).get("planned") is evidence.get("google_sites_planned") is True,
        "serving_complete": contract.get("serving_layer_complete") is evidence.get("serving_layer_complete") is True,
        "zero_effects": (
            bool(effects) and all(value == 0 for value in effects.values())
            and evidence.get("remote_effects") == 0
            and all(value == 0 for value in evidence.get("remote_effects_breakdown", {}).values())
        ),
        "no_authorization": contract.get("active_authorization") is evidence.get("active_authorization") is None,
        "siope_2025_blocked": "SIOPE_2025_BLOCKED" in cautions,
        "candidate_caution": (
            "MATCH_CANDIDATE != FINANCIAL_IDENTITY" in cautions
            and "MATCH_CANDIDATE NÃO REPRESENTA IDENTIDADE FINANCEIRA COMPROVADA." in cautions
        ),
        "source_truth_separate": (
            contract.get("product_role") == "DERIVED_ANALYTICAL_PRODUCT_NOT_SOURCE_OF_TRUTH"
            and contract.get("provenance_contract", {}).get("portal_modifies_source_of_truth") is False
        ),
        "future_only": (
            future[0].get("status") == future[1].get("status") == future[2].get("status") == "NOT_IMPLEMENTED"
            and future[0].get("active_automation") is False
            and future[0].get("schedule") is False
            and future[0].get("recurrence") is False
            and future[1].get("used") is False
            and future[2].get("used") is False
        ),
        "build_not_performed": (
            contract.get("data_studio_report", {}).get("build_performed") is False
            and contract.get("google_sites", {}).get("build_performed") is False
            and contract.get("google_sites", {}).get("publication_performed") is False
        ),
        "docs_complete": (
            len(docs) == sum(path.exists() for path in docs)
            and "PORTAL_ANALITICO_FINAL encerra a fase de engenharia" in doc_text
        ),
        "ci_entrypoints": (
            "python scripts/github_bi_005_generalized_serving_executor_gate.py" in workflow
            and "python scripts/github_portal_analitico_final_gate.py" in workflow
        ),
    }
    failed = [key for key, value in checks.items() if not value]
    payload = {
        "status": EXPECTED_STATUS if not failed else "STOP_PORTAL_ANALITICO_FINAL",
        "checks": checks,
        "failed_checks": failed,
        "field_reference_errors": field_errors,
    }
    print(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    return bool(failed)


if __name__ == "__main__":
    raise SystemExit(main())
