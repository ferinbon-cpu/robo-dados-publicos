from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_siope_2025_official_alias_documentary_discovery_review_gate.py"
REVIEW = ROOT / "config" / "siope_2025_official_alias_documentary_discovery_review.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_009E_L_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_RUN_1_0.8.0.json"
AUTH = ROOT / "config" / "siope_2025_official_alias_documentary_discovery_authorization.v1.json"

spec = importlib.util.spec_from_file_location("review_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _base() -> tuple[dict, dict, dict]:
    return _load(REVIEW), _load(EVIDENCE), _load(AUTH)


def test_current_review_passes() -> None:
    review, evidence, auth = _base()
    assert module.validate(review, evidence, auth) == module.PASS


@pytest.mark.parametrize(
    ("mutation", "target"),
    [
        (lambda x: x["execution"].__setitem__("official_document_open_count", 13), "evidence"),
        (lambda x: x["execution"].__setitem__("retry_count", 1), "evidence"),
        (lambda x: x["execution"].__setitem__("authentication_attempt_count", 1), "evidence"),
        (lambda x: x["execution"].__setitem__("sharepoint_401_route_reuse_count", 1), "evidence"),
        (lambda x: x["execution"].__setitem__("limeira_financial_data_query_count", 1), "evidence"),
        (lambda x: x["execution"].__setitem__("binary_package_download_count", 1), "evidence"),
        (lambda x: x["question_results"]["S1_NUM_POPU"].__setitem__("status", "PROVEN"), "evidence"),
        (lambda x: x["question_results"]["S1_NUM_POPU"].__setitem__("official_primary_vintage_rule_found", True), "evidence"),
        (lambda x: x["question_results"]["S2_FINANCIAL_ALIAS_BRIDGE"].__setitem__("status", "PROVEN"), "evidence"),
        (lambda x: x["question_results"]["S2_FINANCIAL_ALIAS_BRIDGE"].__setitem__("current_alias_identity_proven_count", 10), "evidence"),
        (lambda x: x.__setitem__("promotion_performed", True), "evidence"),
        (lambda x: x["authorization_consumption"].__setitem__("rerun_authorized", True), "evidence"),
        (lambda x: x.__setitem__("authorization_consumed", False), "auth"),
        (lambda x: x.__setitem__("rerun_authorized", True), "auth"),
        (lambda x: x.__setitem__("decision", "PROMOTE"), "review"),
        (lambda x: x["resulting_state"].__setitem__("semantic_comparability_status", "PROVEN"), "review"),
        (lambda x: x["resulting_state"].__setitem__("annual_closure_status", "PROVEN"), "review"),
        (lambda x: x["resulting_state"].__setitem__("closed_annual_series_last_year", 2025), "review"),
        (lambda x: x["resulting_state"].__setitem__("gold_metrics_status", "PROVEN"), "review"),
        (lambda x: x["resulting_state"].__setitem__("year_2026_status", "PROVEN"), "review"),
        (lambda x: x["guards"].__setitem__("future_remote_discovery_authorized", True), "review"),
    ],
)
def test_fail_closed_mutations(mutation, target: str) -> None:  # noqa: ANN001
    review, evidence, auth = _base()
    review = copy.deepcopy(review)
    evidence = copy.deepcopy(evidence)
    auth = copy.deepcopy(auth)
    obj = {"review": review, "evidence": evidence, "auth": auth}[target]
    mutation(obj)
    with pytest.raises(module.ReviewGateError):
        module.validate(review, evidence, auth)


def test_blocked_sharepoint_route_cannot_appear_in_session_attempts() -> None:
    review, evidence, auth = _base()
    evidence = copy.deepcopy(evidence)
    evidence["official_url_attempts"][0]["url"] = (
        "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip"
    )
    with pytest.raises(module.ReviewGateError):
        module.validate(review, evidence, auth)
