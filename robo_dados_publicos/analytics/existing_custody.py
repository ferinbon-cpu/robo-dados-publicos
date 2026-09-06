from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "config/existing_custody_corpus_registry.v1.json"
DEFAULT_CROSSWALK = ROOT / "config/existing_custody_product_ingestion_crosswalk.v1.json"
DEFAULT_ONTOLOGY = ROOT / "config/observatory_question_ontology.v1.json"


class Task179Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task179Stop(code)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_contracts(
    registry_path: str | Path = DEFAULT_REGISTRY,
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _load(registry_path), _load(crosswalk_path), _load(ontology_path)


def validate_contracts(
    registry_path: str | Path = DEFAULT_REGISTRY,
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
) -> dict[str, Any]:
    registry, crosswalk, ontology = load_contracts(registry_path, crosswalk_path, ontology_path)
    _stop(registry.get("schema") == "EXISTING_CUSTODY_CORPUS_REGISTRY_V1", "TASK179_REGISTRY_SCHEMA")
    _stop(crosswalk.get("schema") == "EXISTING_CUSTODY_PRODUCT_INGESTION_CROSSWALK_V1", "TASK179_CROSSWALK_SCHEMA")
    _stop(ontology.get("schema") == "LIMEIRA_OBSERVATORY_QUESTION_ONTOLOGY_V1", "TASK179_ONTOLOGY_SCHEMA")

    assets = {row["id"]: row for row in registry["assets"]}
    _stop(len(assets) == len(registry["assets"]), "TASK179_DUPLICATE_ASSET")
    required_assets = {
        "INDICATORS_COLLECTION_2026_PUBLICATION",
        "BASE_MESTRA_LIMEIRA_V05",
        "CAMADA_ANALITICA_V06_40_ESCOLAS_V08",
        "CEREBRO_NORMATIVO_GESTAO_ESCOLAR_LIMEIRA",
        "MD_01_2_BASE_UNIFICADA_FISCAL_ORCAMENTARIA_LIMEIRA",
        "MD_01_3B_CORPUS",
        "MD_00_V17",
        "MD_00_1_V02",
    }
    _stop(required_assets <= set(assets), "TASK179_REQUIRED_ASSET_MISSING")

    _stop(
        registry["precedence"]["school_numeric"][:2]
        == ["BASE_MESTRA_LIMEIRA_V05", "CAMADA_ANALITICA_V06_40_ESCOLAS_V08"],
        "TASK179_SCHOOL_PRECEDENCE",
    )
    _stop(
        registry["precedence"]["normative"][0] == "EXACT_OFFICIAL_NORMATIVE_DOCUMENT",
        "TASK179_NORMATIVE_PRECEDENCE",
    )
    _stop(
        registry["precedence"]["fiscal"][0] == "OFFICIAL_STRUCTURED_TCE_SIOPE_SICONFI_FUNDEB",
        "TASK179_FISCAL_PRECEDENCE",
    )

    collection = assets["INDICATORS_COLLECTION_2026_PUBLICATION"]
    _stop(collection["version"] == "SYNCHRONIZED_I_V07_II_V06_III_V07", "TASK179_COLLECTION_VERSION")
    _stop(collection["coverage"]["school_universe_2025"] == 69, "TASK179_SCHOOL_UNIVERSE")
    _stop(collection["coverage"]["primary_years_schools"] == 40, "TASK179_PRIMARY_SCHOOLS")
    _stop(collection["coverage"]["early_childhood_only_or_other_profiles"] == 29, "TASK179_EI_SCHOOLS")
    _stop("READY_FOR_PARTIAL_STRUCTURED_EXTRACTION" in collection["readiness"], "TASK179_COLLECTION_PARTIAL_READY")
    _stop(
        "VOLUME_I_NARRATIVE_MUST_NOT_OVERWRITE_CANONICAL_STRUCTURED_ROWS" in collection["constraints"],
        "TASK179_COLLECTION_NUMERIC_PRECEDENCE_GUARD",
    )

    base = assets["BASE_MESTRA_LIMEIRA_V05"]
    _stop(base["custody"] == "DISCOVERED_AND_READABLE_IN_USER_LIBRARY", "TASK179_BASE_CUSTODY")
    _stop("READY_FOR_FULL_STRUCTURED_ROW_MATERIALIZATION" in base["readiness"], "TASK179_BASE_READY")
    _stop(
        base.get("sha256") == "4d352dc55537240a4c1ffb3c37337e9c029577ab611f851f2ec925d0178b9eda",
        "TASK179_BASE_SHA",
    )
    extension = assets["CAMADA_ANALITICA_V06_40_ESCOLAS_V08"]
    _stop(extension["custody"] == "DISCOVERED_AND_READABLE_IN_USER_LIBRARY", "TASK179_EXTENSION_CUSTODY")
    _stop("READY_FOR_FULL_STRUCTURED_ROW_MATERIALIZATION" in extension["readiness"], "TASK179_EXTENSION_READY")
    _stop(
        extension.get("sha256_xlsx") == "0516868e06685aebe8254b11ca6488ef26b03dea61f927ff637840cf2a21e865",
        "TASK179_EXTENSION_SHA",
    )
    _stop(extension.get("coverage", {}).get("reconciliation_2025_divergences") == 0, "TASK179_EXTENSION_QA")

    brain = assets["CEREBRO_NORMATIVO_GESTAO_ESCOLAR_LIMEIRA"]
    _stop("SYNTHESIS_NE_LEGAL_PROOF" in brain["constraints"], "TASK179_NORMATIVE_PROOF_GUARD")
    md = assets["MD_01_2_BASE_UNIFICADA_FISCAL_ORCAMENTARIA_LIMEIRA"]
    _stop("INTERPRETATION_NE_NUMERIC_TRUTH" in md["constraints"], "TASK179_FISCAL_TRUTH_GUARD")

    expected_products = {
        "SCHOOL_INDICATOR_SERIES",
        "PLANNING_DOCUMENT_INDEX",
        "FISCAL_SERIES",
        "JOM_EVENT_INDEX",
        "ACCOUNTING_LEDGER",
        "REVENUE_LEDGER",
        "QUERY_PRODUCT_CATALOG",
    }
    _stop(set(crosswalk["products"]) == expected_products, "TASK179_PRODUCT_SET")
    _stop(
        crosswalk["products"]["SCHOOL_INDICATOR_SERIES"]["current_status"] == "READY_FROM_EXISTING_CUSTODY",
        "TASK179_SCHOOL_STATUS",
    )
    _stop(
        crosswalk["products"]["PLANNING_DOCUMENT_INDEX"]["current_status"] == "READY_FROM_EXISTING_CUSTODY",
        "TASK179_DOCUMENT_STATUS",
    )
    _stop(
        crosswalk["noncanonical_task_note"]["task_178_remote_serving_should_wait"] is True,
        "TASK179_TASK178_WAIT",
    )
    _stop(crosswalk["handoff_priority"][0]["asset_id"] == "MD_01_3B_CORPUS", "TASK179_HANDOFF_PRIORITY")

    ontology_ids = {row["id"] for row in ontology["domains"]}
    _stop(len(ontology_ids) == 15, "TASK179_DOMAIN_COUNT")
    effects = list(registry["remote_effects"].values()) + list(crosswalk["remote_effects"].values())
    _stop(all(value is False for value in effects), "TASK179_REMOTE_EFFECT")
    return {
        "schema": "TASK179_EXISTING_CUSTODY_VALIDATION_V1",
        "status": "PASS",
        "asset_count": len(assets),
        "product_count": len(expected_products),
        "domain_count": len(ontology_ids),
        "network": False,
        "drive_write": False,
        "serving": False,
    }


def _asset_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in registry["assets"]}


def product_readiness(
    product_name: str,
    registry_path: str | Path = DEFAULT_REGISTRY,
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
) -> dict[str, Any]:
    registry = _load(registry_path)
    crosswalk = _load(crosswalk_path)
    _stop(product_name in crosswalk["products"], "TASK179_UNKNOWN_PRODUCT")
    assets = _asset_map(registry)
    spec = crosswalk["products"][product_name]

    referenced = []
    for key, value in spec.items():
        if key.endswith("_inputs") or key.endswith("_sources") or key in {
            "canonical_inputs",
            "currently_readable_inputs",
            "full_materialization_requires",
            "preferred_optional_extension",
            "enrichment_inputs_needing_handoff",
            "optional_context_inputs",
            "catalog_inputs",
        }:
            if isinstance(value, list):
                referenced.extend(value)
        elif key == "existing_system_source" and isinstance(value, str):
            referenced.append(value)

    asset_rows = []
    for ref in referenced:
        asset_id = ref.split(":", 1)[0]
        if asset_id in assets:
            asset = assets[asset_id]
            asset_rows.append(
                {
                    "asset_id": asset_id,
                    "custody": asset["custody"],
                    "readiness": list(asset["readiness"]),
                    "role": asset["role"],
                }
            )
        else:
            asset_rows.append(
                {
                    "asset_id": asset_id,
                    "custody": "EXISTING_SYSTEM_OR_EXTERNAL_SOURCE",
                    "readiness": ["OUTSIDE_TASK179_CUSTODY_REGISTRY"],
                    "role": "SYSTEM_SOURCE",
                }
            )

    blocking_refs = {
        str(ref).split(":", 1)[0]
        for ref in (spec.get("full_materialization_requires") or [])
    }
    optional_refs = {
        str(ref).split(":", 1)[0]
        for ref in (
            list(spec.get("enrichment_inputs_needing_handoff") or [])
            + list(spec.get("preferred_optional_extension") or [])
        )
    }
    needs_handoff = sorted(
        {
            row["asset_id"]
            for row in asset_rows
            if row["asset_id"] in blocking_refs
            and "NEEDS_BASE_STRUCTURED_FILE_HANDOFF" in row["readiness"]
        }
    )
    optional_handoffs = sorted(
        {
            row["asset_id"]
            for row in asset_rows
            if row["asset_id"] in optional_refs
            and "NEEDS_BASE_STRUCTURED_FILE_HANDOFF" in row["readiness"]
        }
    )
    return {
        "schema": "TASK179_PRODUCT_READINESS_V1",
        "product_name": product_name,
        "status": spec["current_status"],
        "target_domains": list(spec.get("target_domains") or []),
        "asset_rows": asset_rows,
        "needs_handoff": needs_handoff,
        "optional_handoffs": optional_handoffs,
        "full_materialization_ready": (
            spec["current_status"] in {"READY_FROM_EXISTING_CUSTODY", "NO_NEW_CUSTODY_INPUT_REQUIRED"}
            and not needs_handoff
        ),
    }


def domain_coverage(
    registry_path: str | Path = DEFAULT_REGISTRY,
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
) -> dict[str, Any]:
    registry, crosswalk, ontology = load_contracts(registry_path, crosswalk_path, ontology_path)
    ontology_ids = [row["id"] for row in ontology["domains"]]
    domain_products: dict[str, list[str]] = {domain_id: [] for domain_id in ontology_ids}
    for product_name, spec in crosswalk["products"].items():
        for domain_id in spec.get("target_domains") or []:
            _stop(domain_id in domain_products, "TASK179_UNKNOWN_TARGET_DOMAIN")
            domain_products[domain_id].append(product_name)

    rows = []
    counts = {"COVERED_OR_PARTIAL": 0, "EXPLICIT_GAP": 0}
    for domain_id in ontology_ids:
        products = domain_products[domain_id]
        if products:
            status = "COVERED_OR_PARTIAL"
        else:
            status = "EXPLICIT_GAP"
        counts[status] += 1
        rows.append(
            {
                "domain_id": domain_id,
                "status": status,
                "products": sorted(products),
            }
        )

    gaps = [row["domain_id"] for row in rows if row["status"] == "EXPLICIT_GAP"]
    return {
        "schema": "TASK179_EXISTING_CUSTODY_DOMAIN_COVERAGE_V1",
        "domain_count": len(rows),
        "counts": counts,
        "covered_or_partial_count": counts["COVERED_OR_PARTIAL"],
        "explicit_gap_count": counts["EXPLICIT_GAP"],
        "explicit_gaps": gaps,
        "domains": rows,
        "all_domains_explicit": len(rows) == 15,
    }


def recommended_handoffs(
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
) -> dict[str, Any]:
    crosswalk = _load(crosswalk_path)
    rows = sorted(crosswalk["handoff_priority"], key=lambda row: row["rank"])
    return {
        "schema": "TASK179_HANDOFF_PRIORITY_V1",
        "priorities": rows,
        "first": rows[0],
        "remote_execution_should_wait": crosswalk["noncanonical_task_note"]["task_178_remote_serving_should_wait"],
    }


def summary() -> dict[str, Any]:
    validation = validate_contracts()
    coverage = domain_coverage()
    handoffs = recommended_handoffs()
    products = [
        product_readiness(product_name)
        for product_name in _load(DEFAULT_CROSSWALK)["products"]
    ]
    return {
        "schema": "TASK179_EXISTING_CUSTODY_SUMMARY_V1",
        "validation": validation,
        "coverage": coverage,
        "products": products,
        "handoffs": handoffs,
    }


if __name__ == "__main__":
    print(json.dumps(summary(), ensure_ascii=False, indent=2, sort_keys=True))
