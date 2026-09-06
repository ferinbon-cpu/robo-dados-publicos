from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/bi/observatory_query_product_serving.v1.json"
TASK176_CONTRACT = ROOT / "config/observatory_query_products.v1.json"
LEGACY_SERVING_CONTRACT = ROOT / "config/bi/serving.v1.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class Task177Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task177Stop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "OBSERVATORY_QUERY_PRODUCT_SERVING_V1", "TASK177_CONTRACT_SCHEMA")
    _stop(obj.get("tier") == "T0_OFFLINE_IMPLEMENTATION_REVIEW", "TASK177_CONTRACT_TIER")
    _stop(obj.get("parent_path") == "13_BI/02_SERVING", "TASK177_PARENT")
    _stop(obj.get("tabs") == ["DATA", "META"], "TASK177_TABS")
    _stop(obj.get("active_authorization") is None, "TASK177_ACTIVE_AUTH")
    _stop(obj.get("remote_execution_authorized") is False, "TASK177_REMOTE_AUTH")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK177_REMOTE_EFFECT")
    return obj


def validate_contract(
    path: str | Path = DEFAULT_CONTRACT,
    task176_path: str | Path = TASK176_CONTRACT,
    legacy_serving_path: str | Path = LEGACY_SERVING_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(path)
    task176 = json.loads(Path(task176_path).read_text(encoding="utf-8"))
    legacy = json.loads(Path(legacy_serving_path).read_text(encoding="utf-8"))

    expected_products = set(task176["products"])
    mapping = contract["product_mapping"]
    _stop(set(mapping) == expected_products, "TASK177_PRODUCT_MAPPING")
    _stop(len(set(mapping.values())) == 6, "TASK177_SERVING_NAMES_UNIQUE")
    _stop(
        all(name.startswith("OBS_") and name.endswith("__SERVING") for name in mapping.values()),
        "TASK177_SERVING_NAMESPACE",
    )
    _stop(
        legacy["dataset_allowlist"] == [
            "BI_SIOPE_SERIES",
            "BI_JORNAL_EVENTOS",
            "BI_RECONCILIACAO",
            "BI_FONTES_STATUS",
            "BI_EXECUCOES_ROBO",
            "BI_DICIONARIO",
        ],
        "TASK177_LEGACY_ALLOWLIST_CHANGED",
    )
    _stop(
        not (set(legacy["serving_names"]) & set(mapping.values())),
        "TASK177_NAMESPACE_COLLISION",
    )
    auth = contract["authorization_contract"]
    _stop(auth["task"] == "TASK_177_OBSERVATORY_QUERY_PRODUCT_SERVING_MATERIALIZATION", "TASK177_AUTH_TASK")
    _stop(auth["scope"] == "SINGLE_PINNED_QUERY_PRODUCT_SNAPSHOT_TO_STABLE_SERVING", "TASK177_AUTH_SCOPE")
    _stop(contract["guards"]["prior_bi_authorization_reuse"] is False, "TASK177_PRIOR_AUTH_REUSE")
    _stop(contract["guards"]["looker_publication_separate"] is True, "TASK177_LOOKER_SEPARATE")
    return {
        "schema": "TASK177_SERVING_CONTRACT_VALIDATION_V1",
        "status": "PASS",
        "product_count": len(mapping),
        "legacy_bi_allowlist_unchanged": True,
        "network": False,
        "drive_write": False,
        "serving_write": False,
    }


def _row_type(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "NUMBER"
    if isinstance(value, (list, dict)):
        return "JSON"
    return "TEXT"


def _type_profile(rows: list[Mapping[str, Any]], columns: list[str]) -> dict[str, str]:
    profile: dict[str, str] = {}
    for column in columns:
        kinds = {_row_type(row.get(column)) for row in rows if row.get(column) is not None}
        if not kinds:
            profile[column] = "UNKNOWN"
        elif kinds <= {"NUMBER"}:
            profile[column] = "NUMBER"
        elif len(kinds) == 1:
            profile[column] = next(iter(kinds))
        else:
            raise Task177Stop(f"TASK177_MIXED_TYPE_{column}")
    return profile


def _content_rows(product: Mapping[str, Any]) -> list[dict[str, Any]]:
    product_name = str(product.get("product_name") or "")
    rows = [dict(row) for row in product.get("rows", [])]
    if product_name == "QUERY_PRODUCT_CATALOG":
        for row in rows:
            row.pop("catalog_snapshot_id", None)
    else:
        for row in rows:
            row.pop("snapshot_id", None)
    return rows


def validate_product_snapshot(product: Mapping[str, Any]) -> dict[str, Any]:
    contract = load_contract()
    task176 = json.loads(TASK176_CONTRACT.read_text(encoding="utf-8"))
    product_name = str(product.get("product_name") or "")
    _stop(product_name in contract["product_mapping"], "TASK177_UNKNOWN_PRODUCT")
    expected_schema = task176["products"][product_name]["schema"]
    _stop(product.get("product_schema") == expected_schema, "TASK177_PRODUCT_SCHEMA")
    rows = list(product.get("rows") or [])
    _stop(product.get("row_count") == len(rows), "TASK177_ROW_COUNT")
    canonical_rows = _content_rows(product)
    content_sha256 = _sha(canonical_rows)
    _stop(product.get("content_sha256") == content_sha256, "TASK177_CONTENT_HASH")
    _stop(product.get("snapshot_id") == content_sha256[:24], "TASK177_SNAPSHOT_ID")
    _stop(bool(product.get("generated_at")), "TASK177_GENERATED_AT")
    _stop(bool(product.get("software_version")), "TASK177_SOFTWARE_VERSION")
    return {
        "product_name": product_name,
        "snapshot_id": product["snapshot_id"],
        "content_sha256": content_sha256,
        "row_count": len(rows),
        "status": "PASS",
    }


def _ordered_columns(product: Mapping[str, Any]) -> list[str]:
    rows = [dict(row) for row in product.get("rows", [])]
    columns = sorted({key for row in rows for key in row})
    if columns:
        return columns
    task176 = json.loads(TASK176_CONTRACT.read_text(encoding="utf-8"))
    spec = task176["products"][product["product_name"]]
    if product["product_name"] == "QUERY_PRODUCT_CATALOG":
        return sorted(spec["required_fields"] + ["catalog_snapshot_id", "generated_at", "software_version", "caution"])
    common = [
        "product_schema",
        "snapshot_id",
        "observation_period",
        "generated_at",
        "software_version",
        "source_family",
        "source_sha256",
        "provenance_ref",
        "quality_status",
        "caution",
    ]
    return sorted(set(spec["required_fields"] + common))


def schema_fingerprint(product: Mapping[str, Any]) -> str:
    validate_product_snapshot(product)
    rows = [dict(row) for row in product.get("rows", [])]
    columns = _ordered_columns(product)
    bound = {
        "product_name": product["product_name"],
        "product_schema": product["product_schema"],
        "ordered_columns": columns,
        "type_profile": _type_profile(rows, columns),
    }
    return _sha(bound)


def _source_families(product: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            str(row.get("source_family"))
            for row in product.get("rows", [])
            if row.get("source_family")
        }
    )


def _cautions(product: Mapping[str, Any]) -> list[str]:
    cautions = sorted(
        {
            str(row.get("caution"))
            for row in product.get("rows", [])
            if row.get("caution")
        }
    )
    if "DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH" not in cautions:
        cautions.append("DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH")
    return sorted(cautions)


@dataclass(frozen=True)
class QueryServingTarget:
    product_name: str
    serving_name: str
    snapshot_id: str
    content_sha256: str
    product_schema: str
    schema_fingerprint_sha256: str
    ordered_columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    meta: dict[str, str]

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass(frozen=True)
class QueryServingPlan:
    operation: str
    target: QueryServingTarget
    logical_batch_update_count: int
    clear_rows: int
    clear_columns: int
    semantic_readback_required: bool


def build_target(product: Mapping[str, Any]) -> QueryServingTarget:
    validate_product_snapshot(product)
    contract = load_contract()
    columns = _ordered_columns(product)
    rows_dict = [dict(row) for row in product.get("rows", [])]
    fingerprint = schema_fingerprint(product)
    matrix = tuple(tuple(row.get(column) for column in columns) for row in rows_dict)
    meta = {
        "product_name": str(product["product_name"]),
        "product_schema": str(product["product_schema"]),
        "serving_contract_version": "1",
        "snapshot_id": str(product["snapshot_id"]),
        "content_sha256": str(product["content_sha256"]),
        "schema_fingerprint_sha256": fingerprint,
        "row_count": str(product["row_count"]),
        "column_count": str(len(columns)),
        "ordered_columns_json": json.dumps(columns, ensure_ascii=False, separators=(",", ":")),
        "generated_at": str(product["generated_at"]),
        "software_version": str(product["software_version"]),
        "source_families_json": json.dumps(_source_families(product), ensure_ascii=False, separators=(",", ":")),
        "cautions_json": json.dumps(_cautions(product), ensure_ascii=False, separators=(",", ":")),
        "source_role": "DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH",
    }
    _stop(list(meta) == contract["meta_keys"], "TASK177_META_KEYS")
    return QueryServingTarget(
        product_name=str(product["product_name"]),
        serving_name=contract["product_mapping"][product["product_name"]],
        snapshot_id=str(product["snapshot_id"]),
        content_sha256=str(product["content_sha256"]),
        product_schema=str(product["product_schema"]),
        schema_fingerprint_sha256=fingerprint,
        ordered_columns=tuple(columns),
        rows=matrix,
        meta=meta,
    )


def _serialize_value(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, bool):
        return {"userEnteredValue": {"boolValue": value}}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {"userEnteredValue": {"numberValue": float(value)}}
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"userEnteredValue": {"stringValue": str(value)}}


def serialize_target(target: QueryServingTarget) -> dict[str, Any]:
    header = [{"userEnteredValue": {"stringValue": column}} for column in target.ordered_columns]
    data = [header] + [
        [_serialize_value(value) for value in row]
        for row in target.rows
    ]
    meta_header = [
        {"userEnteredValue": {"stringValue": "key"}},
        {"userEnteredValue": {"stringValue": "value"}},
    ]
    meta = [meta_header] + [
        [_serialize_value(key), _serialize_value(target.meta[key])]
        for key in load_contract()["meta_keys"]
    ]
    return {
        "tabs": {"DATA": data, "META": meta},
        "value_input_option": "RAW",
    }


def _validate_existing(existing: Mapping[str, Any], target: QueryServingTarget) -> None:
    _stop(existing.get("tabs") == ["DATA", "META"], "TASK177_EXISTING_TABS")
    _stop(existing.get("formula_present") is not True, "TASK177_FORMULA_PRESENT")
    _stop(existing.get("extra_cells") is not True, "TASK177_EXTRA_CELLS")
    _stop(existing.get("headers") == list(target.ordered_columns), "TASK177_HEADERS")
    _stop(existing.get("meta") == target.meta, "TASK177_EXISTING_META")
    _stop(existing.get("rows") == [list(row) for row in target.rows], "TASK177_EXISTING_ROWS")


def plan_serving(
    target: QueryServingTarget,
    existing: Mapping[str, Any] | None,
    *,
    snapshot_validated: bool,
) -> QueryServingPlan:
    _stop(snapshot_validated, "TASK177_SNAPSHOT_NOT_VALIDATED")
    if existing is None:
        return QueryServingPlan(
            operation="CREATE_INITIAL_SERVING",
            target=target,
            logical_batch_update_count=1,
            clear_rows=target.row_count + 1,
            clear_columns=len(target.ordered_columns),
            semantic_readback_required=True,
        )

    if existing.get("tabs") != ["DATA", "META"]:
        raise Task177Stop("TASK177_EXISTING_TABS")
    _stop(existing.get("formula_present") is not True, "TASK177_FORMULA_PRESENT")
    _stop(existing.get("extra_cells") is not True, "TASK177_EXTRA_CELLS")
    meta = existing.get("meta")
    _stop(isinstance(meta, dict), "TASK177_EXISTING_META")
    _stop(meta.get("product_name") == target.product_name, "TASK177_PRODUCT_MISMATCH")
    if meta.get("schema_fingerprint_sha256") != target.schema_fingerprint_sha256:
        raise Task177Stop("TASK177_SCHEMA_DRIFT_REQUIRES_MIGRATION")

    same_snapshot = (
        meta.get("snapshot_id") == target.snapshot_id
        and meta.get("content_sha256") == target.content_sha256
    )
    if same_snapshot:
        _validate_existing(existing, target)
        return QueryServingPlan(
            operation="NO_CHANGE_IDEMPOTENT",
            target=target,
            logical_batch_update_count=0,
            clear_rows=0,
            clear_columns=0,
            semantic_readback_required=False,
        )

    rows = max(len(existing.get("rows") or []), target.row_count) + 1
    columns = max(len(existing.get("headers") or []), len(target.ordered_columns))
    return QueryServingPlan(
        operation="REPLACE_SERVING_FROM_NEW_SNAPSHOT",
        target=target,
        logical_batch_update_count=1,
        clear_rows=rows,
        clear_columns=columns,
        semantic_readback_required=True,
    )


def validate_remote_preflight(
    target: QueryServingTarget,
    *,
    parent: str,
    title: str | None,
    remote_matches: int,
    mime: str | None,
    snapshot_validated: bool,
) -> None:
    contract = load_contract()
    _stop(parent == contract["parent_path"], "TASK177_REMOTE_PARENT")
    if title is not None:
        _stop(title == target.serving_name, "TASK177_REMOTE_TITLE")
    _stop(isinstance(remote_matches, int) and remote_matches >= 0, "TASK177_REMOTE_STATE")
    _stop(remote_matches <= 1, "TASK177_DUPLICATE_REMOTE_NAME")
    if remote_matches == 1:
        _stop(mime == contract["google_sheets_mime"], "TASK177_REMOTE_MIME")
    _stop(snapshot_validated, "TASK177_SNAPSHOT_NOT_VALIDATED")


def validate_authorization(
    auth: Mapping[str, Any] | None,
    *,
    implementation_sha: str,
    target: QueryServingTarget,
) -> str:
    contract = load_contract()
    _stop(isinstance(auth, Mapping), "TASK177_T3_NOT_AUTHORIZED")
    _stop(auth.get("authorized") is True, "TASK177_T3_NOT_AUTHORIZED")
    _stop(auth.get("serving_mutation_authorized") is True, "TASK177_T3_NOT_AUTHORIZED")
    required = {
        "authorization_id",
        "authorized",
        "repository",
        "tier",
        "drive_root",
        "parent_path",
        "task",
        "scope",
        "implementation_sha",
        "selected_product",
        "selected_snapshot_id",
        "consumed",
        "test_only",
        "serving_mutation_authorized",
        "looker_publication_authorized",
    }
    _stop(set(auth) == required, "TASK177_AUTH_SHAPE")
    _stop(HEX40.fullmatch(str(implementation_sha or "")) is not None, "TASK177_IMPLEMENTATION_SHA")
    _stop(auth.get("implementation_sha") == implementation_sha, "TASK177_AUTH_IMPLEMENTATION_SHA")
    expected = contract["authorization_contract"]
    for key in ("repository", "tier", "drive_root", "parent_path", "task", "scope"):
        _stop(auth.get(key) == expected[key], f"TASK177_AUTH_{key.upper()}")
    _stop(auth.get("selected_product") == target.product_name, "TASK177_AUTH_PRODUCT")
    _stop(auth.get("selected_snapshot_id") == target.snapshot_id, "TASK177_AUTH_SNAPSHOT")
    _stop(auth.get("consumed") is False, "TASK177_AUTH_CONSUMED")
    _stop(auth.get("test_only") is False, "TASK177_AUTH_TEST_ONLY")
    _stop(auth.get("looker_publication_authorized") is False, "TASK177_AUTH_LOOKER")
    _stop(bool(str(auth.get("authorization_id") or "").strip()), "TASK177_AUTH_ID")
    return "PASS_TASK177_T3_AUTHORIZATION_VALID"


def semantic_readback(target: QueryServingTarget, readback: Mapping[str, Any]) -> str:
    _validate_existing(readback, target)
    return "PASS_TASK177_SEMANTIC_READBACK_VERIFIED"


def generation_manifest(
    plan: QueryServingPlan,
    *,
    authorization_id: str,
    implementation_sha: str,
) -> dict[str, Any]:
    _stop(bool(authorization_id.strip()), "TASK177_AUTH_ID")
    _stop(HEX40.fullmatch(implementation_sha) is not None, "TASK177_IMPLEMENTATION_SHA")
    return {
        "product_name": plan.target.product_name,
        "serving_name": plan.target.serving_name,
        "selected_snapshot_id": plan.target.snapshot_id,
        "content_sha256": plan.target.content_sha256,
        "schema_fingerprint_sha256": plan.target.schema_fingerprint_sha256,
        "row_count": plan.target.row_count,
        "column_count": len(plan.target.ordered_columns),
        "authorization_id": authorization_id,
        "implementation_sha": implementation_sha,
        "operation": plan.operation,
        "semantic_readback_verified": True,
        "generation_manifest_create_only": True,
        "source_snapshot_modified": False,
        "source_layers_replaced": False,
        "looker_publication": False,
        "recurrence": False,
        "schedule": False,
        "filename": (
            f"{plan.target.product_name}__serving_generation__"
            f"{plan.target.snapshot_id}__manifest.json"
        ),
    }


if __name__ == "__main__":
    print(json.dumps(validate_contract(), ensure_ascii=False, indent=2, sort_keys=True))
