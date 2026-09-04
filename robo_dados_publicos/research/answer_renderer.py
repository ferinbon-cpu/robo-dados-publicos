from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from robo_dados_publicos.research.ontology import ASSERTION_STATUSES


SECTION_ORDER = (
    "QUERY",
    "EPISTEMIC_SUMMARY",
    "CLAIMS",
    "INSTITUTIONALIZATION_MATRIX",
    "INSTITUTIONALIZATION_GAPS",
    "HISTORICAL_ACQUISITION_GAPS",
    "GUARDRAILS",
)

REMOTE_EFFECT_KEYS = (
    "network",
    "drive_read",
    "drive_write",
    "source_acquisition",
    "ocr",
    "state_registry_write",
    "queue_write",
    "serving",
    "publication",
    "retry",
    "recurrence",
    "schedule",
)

STATUS_DISPLAY_ORDER = (
    "PROVEN",
    "CORROBORATED",
    "CANDIDATE",
    "UNKNOWN",
    "CONFLICTED",
    "REFUTED",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ResearchAnswerRenderStop(RuntimeError):
    """Fail-closed deterministic research-answer rendering error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ResearchAnswerRenderStop(code)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _validate_evidence_packet(packet: dict[str, Any]) -> None:
    _require(isinstance(packet, dict), "TASK100_EVIDENCE_OBJECT")
    _require(str(packet.get("evidence_id") or "").startswith("EVIDENCE:"), "TASK100_EVIDENCE_ID")
    _require(
        str(packet.get("source_document_id") or "").startswith("DOC:"),
        "TASK100_SOURCE_DOCUMENT_ID",
    )
    _require(bool(str(packet.get("source_document_label") or "").strip()), "TASK100_SOURCE_DOCUMENT_LABEL")
    locator = packet.get("locator")
    _require(isinstance(locator, dict) and locator, "TASK100_EVIDENCE_LOCATOR")


def validate_query_result(result: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(result, dict), "TASK100_RESULT_OBJECT")
    _require(result.get("schema") == "RESEARCH_QUERY_RESULT_V1", "TASK100_RESULT_SCHEMA")

    query = result.get("query")
    subject = result.get("subject")
    claims = result.get("claims")
    _require(isinstance(query, dict) and query, "TASK100_QUERY")
    _require(isinstance(subject, dict) and subject, "TASK100_SUBJECT")
    _require(isinstance(claims, list), "TASK100_CLAIMS")
    _require(bool(str(query.get("query_id") or "").strip()), "TASK100_QUERY_ID")
    _require(bool(str(query.get("query_type") or "").strip()), "TASK100_QUERY_TYPE")
    _require(bool(str(subject.get("id") or "").strip()), "TASK100_SUBJECT_ID")
    _require(bool(str(subject.get("label") or "").strip()), "TASK100_SUBJECT_LABEL")

    for claim in claims:
        _require(isinstance(claim, dict), "TASK100_CLAIM_OBJECT")
        _require(str(claim.get("claim_id") or "").startswith("CLAIM:"), "TASK100_CLAIM_ID")
        _require(isinstance(claim.get("text"), str), "TASK100_CLAIM_TEXT")
        _require(claim.get("status") in ASSERTION_STATUSES, "TASK100_CLAIM_STATUS")
        evidence_ids = claim.get("evidence_ids")
        _require(isinstance(evidence_ids, list), "TASK100_CLAIM_EVIDENCE_IDS")
        if "evidence" in claim:
            _require(isinstance(claim["evidence"], list), "TASK100_CLAIM_EVIDENCE")
            for packet in claim["evidence"]:
                _validate_evidence_packet(packet)

    for key, code in (
        ("institutionalization_dimensions", "TASK100_MATRIX"),
        ("institutionalization_gaps", "TASK100_MATRIX_GAPS"),
        ("historical_acquisition_gaps", "TASK100_HISTORICAL_GAPS"),
        ("unresolved_claims", "TASK100_UNRESOLVED_CLAIMS"),
    ):
        _require(isinstance(result.get(key), list), code)

    for dimension in result["institutionalization_dimensions"]:
        _require(isinstance(dimension, dict), "TASK100_MATRIX_ITEM")
        _require(bool(str(dimension.get("dimension") or "").strip()), "TASK100_MATRIX_DIMENSION")
        _require(dimension.get("status") in ASSERTION_STATUSES, "TASK100_MATRIX_STATUS")

    for gap in result["institutionalization_gaps"]:
        _require(isinstance(gap, dict), "TASK100_MATRIX_GAP_ITEM")
        _require(bool(str(gap.get("dimension") or "").strip()), "TASK100_MATRIX_GAP_DIMENSION")
        _require(gap.get("status") in ASSERTION_STATUSES, "TASK100_MATRIX_GAP_STATUS")

    for gap in result["historical_acquisition_gaps"]:
        _require(isinstance(gap, dict), "TASK100_HISTORICAL_GAP_ITEM")
        _require(bool(str(gap.get("period") or "").strip()), "TASK100_HISTORICAL_PERIOD")
        required = gap.get("required_before_promotion")
        _require(isinstance(required, list) and required, "TASK100_HISTORICAL_REQUIREMENTS")
        _require(all(bool(str(item).strip()) for item in required), "TASK100_HISTORICAL_REQUIREMENT_ITEM")

    _require(result.get("status_promotions_performed") == 0, "TASK100_STATUS_PROMOTION")
    _require(result.get("financial_identity_created") is False, "TASK100_FINANCIAL_IDENTITY")
    _require(result.get("causal_effect_created") is False, "TASK100_CAUSAL_EFFECT")
    _require(
        result.get("natural_language_generation_performed") is False,
        "TASK100_UPSTREAM_NATURAL_LANGUAGE_GENERATION",
    )

    result_sha256 = str(result.get("result_sha256") or "")
    _require(bool(_SHA256_RE.fullmatch(result_sha256)), "TASK100_RESULT_SHA256")
    return deepcopy(result)


def _status_counts(claims: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts = {status: 0 for status in STATUS_DISPLAY_ORDER}
    for claim in claims:
        counts[claim["status"]] += 1
    return [(status, counts[status]) for status in STATUS_DISPLAY_ORDER if counts[status] > 0]


def _render_claim(claim: dict[str, Any]) -> list[str]:
    lines = [
        f"### {claim['claim_id']}",
        "",
        f"- **Status:** {claim['status']}",
        f"- **Texto original:** {claim['text']}",
    ]

    evidence_ids = claim.get("evidence_ids") or []
    lines.append(
        "- **Evidence IDs:** " + (", ".join(evidence_ids) if evidence_ids else "nenhuma")
    )

    if "evidence" in claim:
        evidence = claim["evidence"]
        lines.extend(["", "**Evidências:**"])
        if not evidence:
            lines.append("- nenhuma")
        for packet in evidence:
            line = (
                f"- {packet['evidence_id']} | "
                f"{packet['source_document_label']} | "
                f"{packet['source_document_id']} | "
                f"source_role={packet.get('source_role')} | "
                f"locator={_canonical_json(packet['locator'])}"
            )
            content_hash = packet.get("content_sha256")
            if content_hash:
                line += f" | content_sha256={content_hash}"
            lines.append(line)
    return lines


def _render_matrix_dimension(item: dict[str, Any]) -> str:
    extras = {
        key: value
        for key, value in item.items()
        if key not in {"dimension", "status"}
    }
    suffix = f" | detail={_canonical_json(extras)}" if extras else ""
    return f"- **{item['dimension']}** — {item['status']}{suffix}"


def render_research_answer_markdown(result: dict[str, Any]) -> dict[str, Any]:
    validated = validate_query_result(result)
    subject = validated["subject"]
    query = validated["query"]

    lines: list[str] = [
        f"# Research answer — {subject['label']}",
        "",
        "Renderização determinística e offline de um pacote de consulta já validado.",
        "",
        "## Consulta",
        "",
        f"- **Query ID:** {query['query_id']}",
        f"- **Query type:** {query['query_type']}",
        f"- **Subject:** {subject['label']} ({subject['id']})",
        f"- **Query packet SHA-256:** {validated['result_sha256']}",
        "",
        "## Síntese epistemológica",
        "",
        f"- **Afirmações retornadas:** {validated['claim_count']}",
        f"- **Referências de evidência:** {validated['evidence_reference_count']}",
    ]

    for status, count in _status_counts(validated["claims"]):
        lines.append(f"- **{status}:** {count}")

    lines.extend(
        [
            f"- **Status promotions performed:** {validated['status_promotions_performed']}",
            f"- **Financial identity created:** {str(validated['financial_identity_created']).lower()}",
            f"- **Causal effect created:** {str(validated['causal_effect_created']).lower()}",
            "",
            "## Afirmações",
            "",
        ]
    )

    if not validated["claims"]:
        lines.append("Nenhuma afirmação retornada pelo pacote de consulta.")
    else:
        for index, claim in enumerate(validated["claims"]):
            if index:
                lines.append("")
            lines.extend(_render_claim(claim))

    lines.extend(["", "## Matriz de institucionalização", ""])
    if not validated["institutionalization_dimensions"]:
        lines.append("Nenhuma dimensão de institucionalização incluída neste tipo de consulta.")
    else:
        for item in validated["institutionalization_dimensions"]:
            lines.append(_render_matrix_dimension(item))

    lines.extend(["", "## Lacunas de institucionalização", ""])
    if not validated["institutionalization_gaps"]:
        lines.append("Nenhuma lacuna de institucionalização incluída neste pacote.")
    else:
        for gap in validated["institutionalization_gaps"]:
            lines.append(_render_matrix_dimension(gap))

    lines.extend(["", "## Lacunas históricas de aquisição", ""])
    if not validated["historical_acquisition_gaps"]:
        lines.append("Nenhuma lacuna histórica de aquisição incluída neste pacote.")
    else:
        for gap in validated["historical_acquisition_gaps"]:
            lines.append(f"### {gap['period']}")
            lines.append("")
            for requirement in gap["required_before_promotion"]:
                lines.append(f"- {requirement}")
            lines.append("")
        if lines[-1] == "":
            lines.pop()

    lines.extend(
        [
            "",
            "## Salvaguardas",
            "",
            "- O renderer não promove status epistemológico.",
            "- O renderer não cria identidade financeira.",
            "- O renderer não cria efeito causal.",
            "- O renderer não executa geração livre ou chamada a LLM.",
            "- O renderer não realiza rede, Drive, serving ou publicação.",
        ]
    )

    markdown = "\n".join(lines).rstrip() + "\n"
    return {
        "schema": "RESEARCH_ANSWER_RENDER_V1",
        "source_result_sha256": validated["result_sha256"],
        "format": "MARKDOWN",
        "markdown": markdown,
        "markdown_sha256": sha256(markdown.encode("utf-8")).hexdigest(),
        "status_promotions_performed": 0,
        "financial_identity_created": False,
        "causal_effect_created": False,
        "free_form_generation_performed": False,
        "remote_effects_performed": False,
    }


def load_renderer_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(data.get("schema") == "RESEARCH_ANSWER_RENDERER_V1", "TASK100_CONTRACT_SCHEMA")
    _require(data.get("input_schema") == "RESEARCH_QUERY_RESULT_V1", "TASK100_CONTRACT_INPUT_SCHEMA")
    _require(data.get("output_schema") == "RESEARCH_ANSWER_RENDER_V1", "TASK100_CONTRACT_OUTPUT_SCHEMA")
    _require(data.get("format") == "MARKDOWN", "TASK100_CONTRACT_FORMAT")
    _require(tuple(data.get("section_order") or ()) == SECTION_ORDER, "TASK100_CONTRACT_SECTIONS")

    remote = data.get("remote_effects")
    _require(isinstance(remote, dict), "TASK100_CONTRACT_REMOTE_EFFECT_OBJECT")
    _require(set(remote) == set(REMOTE_EFFECT_KEYS), "TASK100_CONTRACT_REMOTE_EFFECT_KEYS")
    _require(all(value is False for value in remote.values()), "TASK100_CONTRACT_REMOTE_EFFECT")

    invariants = data.get("invariants")
    _require(isinstance(invariants, list) and invariants, "TASK100_CONTRACT_INVARIANTS")
    return data
