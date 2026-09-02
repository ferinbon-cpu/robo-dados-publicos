from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import json


class OfficialEquivalenceStop(ValueError):
    """Fail-closed stop for the bounded official-equivalence probe design."""


def load_official_equivalence_contract(path: str | Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("mode") != "T0_OFFLINE_IMPLEMENTATION_BOUNDARY":
        raise OfficialEquivalenceStop("STOP_LOA_OFFICIAL_EQUIVALENCE_BAD_MODE")
    probe = raw.get("future_probe") or {}
    if len(probe.get("initial_urls", [])) > int(probe.get("max_initial_urls", 0)):
        raise OfficialEquivalenceStop("STOP_LOA_OFFICIAL_EQUIVALENCE_INITIAL_BUDGET")
    if any((raw.get("authorization") or {}).values()):
        raise OfficialEquivalenceStop("STOP_LOA_OFFICIAL_EQUIVALENCE_AUTHORIZATION_EMBEDDED")
    return raw


def build_probe_plan(contract: dict) -> dict:
    probe = contract["future_probe"]
    requests = [
        {
            "ordinal": i + 1,
            "url": url,
            "method": "GET",
            "purpose": "DISCOVERY_PAGE_ONLY",
        }
        for i, url in enumerate(probe["initial_urls"])
    ]
    return {
        "status": "PLANNED_NOT_AUTHORIZED",
        "requests": requests,
        "max_requests": probe["max_requests"],
        "candidate_followups_reserved": probe["max_candidate_followups"],
        "network_called": False,
        "downloads": 0,
    }


def _host_allowed(contract: dict, url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in set(contract["future_probe"]["allowed_hosts"])


def _extension(url: str) -> str:
    path = urlparse(url).path.lower()
    name = path.rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1]


def _identity_signal_score(contract: dict, text: str) -> int:
    normalized = (text or "").upper()
    return sum(1 for signal in contract.get("required_identity_signals", []) if signal.upper() in normalized)


def classify_official_observations(contract: dict, observations: list[dict]) -> dict:
    probe = contract["future_probe"]
    if len(observations) > int(probe["max_requests"]):
        raise OfficialEquivalenceStop("STOP_LOA_OFFICIAL_EQUIVALENCE_REQUEST_BUDGET")

    formats = contract["candidate_formats"]
    classes = contract["classification"]
    candidates: list[dict] = []
    rejected: list[dict] = []

    for observation in observations:
        page_url = str(observation.get("url", ""))
        if not _host_allowed(contract, page_url):
            raise OfficialEquivalenceStop("STOP_LOA_OFFICIAL_EQUIVALENCE_OBSERVATION_HOST")
        page_context = " ".join(
            str(observation.get(key, "")) for key in ("title", "text")
        )
        surface = str(observation.get("surface", ""))
        for link in observation.get("links") or []:
            url = str(link.get("url", ""))
            label = str(link.get("text", ""))
            context = " ".join((page_context, label, url))
            score = _identity_signal_score(contract, context)
            ext = _extension(url)
            content_hint = str(link.get("content_type_hint", "")).lower()

            if not _host_allowed(contract, url):
                rejected.append({"url": url, "reason": "HOST_NOT_ALLOWED"})
                continue

            if score < 2:
                if surface == "TRANSPARENCIA_EXECUCAO":
                    candidates.append({
                        "url": url,
                        "classification": classes["generic_execution"],
                        "identity_signal_score": score,
                        "equivalence_proven": False,
                    })
                continue

            if ext in formats["machine_readable"] or any(
                token in content_hint
                for token in ("csv", "spreadsheet", "json", "xml", "opendocument")
            ):
                classification = classes["machine_candidate"]
            elif ext in formats["archive_review"] or "zip" in content_hint:
                classification = classes["archive_candidate"]
            elif ext in formats["document_only"] or "pdf" in content_hint:
                classification = classes["pdf_candidate"]
            elif ext in formats["text_review"] or content_hint.startswith("text/"):
                classification = classes["text_candidate"]
            else:
                continue

            candidates.append({
                "url": url,
                "classification": classification,
                "identity_signal_score": score,
                "equivalence_proven": False,
            })

    if len(candidates) > int(probe["max_candidate_links"]):
        raise OfficialEquivalenceStop("STOP_LOA_OFFICIAL_EQUIVALENCE_CANDIDATE_BUDGET")

    machine = [c for c in candidates if c["classification"] == classes["machine_candidate"]]
    status = (
        "MACHINE_READABLE_CANDIDATE_DETECTED_REVIEW_REQUIRED"
        if machine
        else classes["none_observed"]
    )
    return {
        "status": status,
        "candidates": candidates,
        "machine_candidates": machine,
        "rejected": rejected,
        "equivalence_proven": False,
        "absence_proven": False,
        "followup_authorized": False,
        "downloads": 0,
    }


def evaluate_candidate_proof(contract: dict, candidate: dict, proofs: dict) -> dict:
    required = contract.get("equivalence_proof_required", [])
    missing = [name for name in required if proofs.get(name) is not True]
    if missing:
        return {
            "status": "CANDIDATE_EQUIVALENCE_NOT_PROVEN",
            "missing_proofs": missing,
            "promotion_authorized": False,
        }
    return {
        "status": "CANDIDATE_PROOF_COMPLETE_REQUIRES_SEPARATE_AUTHORIZATION",
        "missing_proofs": [],
        "promotion_authorized": False,
    }
