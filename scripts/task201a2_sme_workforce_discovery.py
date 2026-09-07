from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
import os
import re
import urllib.parse
from pathlib import Path
from typing import Any

from scripts.task201_workforce_live_probe import (
    Task201Stop,
    _fetch_bytes,
    _norm,
    _plain_html_text,
    parse_contracted_aggregate,
    parse_sme_bonds,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task201_workforce_live_probe.v2.json"


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task201Stop(code)


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK201_WORKFORCE_LIVE_PROBE_V2", "TASK201A2_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_SME_WORKFORCE_DISCOVERY", "TASK201A2_MODE")
    _stop(obj.get("authorization_issue") == 639, "TASK201A2_ISSUE")
    _stop(obj["prior_inep_probe"]["status"] == "TRANSPORT_BLOCKED", "TASK201A2_INEP_STATUS")
    _stop(obj["prior_inep_probe"]["retry_in_task201a2"] is False, "TASK201A2_NO_INEP_RETRY")
    for key in ("sme_home", "sme_app_menu", "sme_contracted"):
        source = obj["sources"][key]
        parsed = urllib.parse.urlparse(source["url"])
        _stop(parsed.scheme == "https", f"TASK201A2_{key.upper()}_SCHEME")
        _stop(parsed.hostname in set(source["allowed_hosts"]), f"TASK201A2_{key.upper()}_HOST")
        _stop(source["max_http_attempts"] == 2, f"TASK201A2_{key.upper()}_ATTEMPTS")
    _stop(obj["privacy"]["aggregate_only"] is True, "TASK201A2_AGGREGATE_ONLY")
    _stop(obj["privacy"]["person_level_input_ephemeral_only"] is True, "TASK201A2_EPHEMERAL")
    _stop(
        all(
            obj["privacy"][key] is False
            for key in (
                "raw_sme_html_persisted",
                "raw_sme_html_artifact",
                "names_persisted",
                "cpf_persisted",
                "matricula_persisted",
                "person_hashes_persisted",
            )
        ),
        "TASK201A2_PRIVACY_PERSISTENCE",
    )
    _stop(obj["output"]["staff_count_materialized"] is False, "TASK201A2_NO_STAFF")
    _stop(obj["output"]["employment_bond_materialized"] is False, "TASK201A2_NO_BOND")
    _stop(
        all(
            obj["output"][key] is False
            for key in (
                "raw_html_persisted",
                "drive_write",
                "serving",
                "publication",
                "schedule",
                "recurrence",
            )
        ),
        "TASK201A2_REMOTE_EFFECT",
    )
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj = _load(contract_path)
    _stop(len(main_sha) == 40 and all(ch in "0123456789abcdef" for ch in main_sha.lower()), "TASK201A2_AUTH_SHA")
    return (
        "TASK201A2_SME_WORKFORCE_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} "
        "sme_attempts=2 raw_persist=0 pii_persist=0"
    )


class _HrefParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.casefold() != "a":
            return
        for key, value in attrs:
            if key.casefold() == "href" and value:
                self.hrefs.append(value)


def discover_sme_paths(data: bytes, *, base_url: str, obj: dict[str, Any]) -> list[str]:
    parser = _HrefParser()
    parser.feed(data.decode("utf-8", errors="replace"))
    allowed_hosts = {
        "sme.limeira.sp.gov.br",
        "www.sme.limeira.sp.gov.br",
    }
    keywords = [_norm(x) for x in obj["discovery"]["allowed_href_keywords"]]
    result: set[str] = set()
    for href in parser.hrefs:
        absolute = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            continue
        path = parsed.path or "/"
        if not any(keyword in _norm(path) for keyword in keywords):
            continue
        result.add(path)
        if len(result) >= int(obj["discovery"]["max_paths"]):
            break
    return sorted(result)


def _assert_sanitized(result: dict[str, Any]) -> None:
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    lowered = _norm(encoded)
    for token in ('"cpf"', '"matricula"', '"person_name"', "registration_value"):
        _stop(token not in lowered, "TASK201A2_PERSON_LEVEL_KEY")
    _stop(not re.search(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", encoded), "TASK201A2_CPF_PATTERN")


def derive_sanitized_result(
    *,
    home_bytes: bytes,
    app_menu_bytes: bytes,
    contracted_bytes: bytes,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = _load(contract_path)
    bonds = parse_sme_bonds(home_bytes)
    contracted = parse_contracted_aggregate(
        contracted_bytes,
        obj["sources"]["sme_contracted"]["expected_title"],
    )
    paths = sorted(set(
        discover_sme_paths(home_bytes, base_url=obj["sources"]["sme_home"]["url"], obj=obj)
        + discover_sme_paths(app_menu_bytes, base_url=obj["sources"]["sme_app_menu"]["url"], obj=obj)
    ))
    result = {
        "schema": "TASK201A2_SME_WORKFORCE_SANITIZED_DISCOVERY_V1",
        "status": "PASS",
        "inep_transport": {
            "status": obj["prior_inep_probe"]["status"],
            "run_id": obj["prior_inep_probe"]["run_id"],
            "retry_in_this_task": False,
            "missing_is_zero": False,
        },
        "sme_bond_taxonomy": bonds,
        "sme_contracted_aggregate": contracted,
        "sme_discovered_paths": {
            "count": len(paths),
            "paths": paths,
            "semantic": "SAME_HOST_NON_PERSONAL_PATH_DISCOVERY_ONLY",
        },
        "guards": {
            "assignment_rows_are_not_unique_people": True,
            "clt_is_not_all_non_effective_bonds": True,
            "person_level_output": False,
            "raw_html_persisted": False,
            "staff_count_materialized": False,
            "employment_bond_materialized": False,
            "drive_write": False,
            "serving": False,
            "publication": False,
            "schedule": False,
            "recurrence": False,
        },
    }
    _assert_sanitized(result)
    return result


def run_live(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(contract_path)
    main_sha = str(os.environ.get("GITHUB_SHA") or "")
    checked = str(os.environ.get("TASK201A2_CHECKED_OUT_SHA") or "")
    comment = str(os.environ.get("TASK201A2_AUTH_COMMENT") or "")
    issue = str(os.environ.get("TASK201A2_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK201A2_CHECKOUT")
    _stop(issue == str(obj["authorization_issue"]), "TASK201A2_RUNTIME_ISSUE")
    _stop(comment == exact_auth_comment(main_sha, contract_path), "TASK201A2_AUTH_COMMENT")

    fetched: dict[str, dict[str, Any]] = {}
    payloads: dict[str, bytes] = {}
    for key in ("sme_home", "sme_app_menu", "sme_contracted"):
        source = obj["sources"][key]
        got = _fetch_bytes(
            source["url"],
            allowed_hosts=set(source["allowed_hosts"]),
            attempts=source["max_http_attempts"],
            accept="text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
            user_agent="robo-dados-publicos-task201a2/0.8.0",
            timeout=60,
        )
        payloads[key] = got.pop("data")
        fetched[key] = got

    result = derive_sanitized_result(
        home_bytes=payloads["sme_home"],
        app_menu_bytes=payloads["sme_app_menu"],
        contracted_bytes=payloads["sme_contracted"],
        contract_path=contract_path,
    )
    result["source"] = {
        key: {
            "url": obj["sources"][key]["url"],
            "html_sha256": fetched[key]["sha256"],
            "html_bytes": fetched[key]["bytes"],
            "attempts_used": fetched[key]["attempts_used"],
        }
        for key in fetched
    }
    result["authorization"] = {
        "issue": obj["authorization_issue"],
        "main_sha": main_sha,
        "exact_comment_verified": True,
    }
    _assert_sanitized(result)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    result = run_live(args.output, args.contract)
    print(json.dumps({
        "status": result["status"],
        "bond_categories": result["sme_bond_taxonomy"]["bond_categories"],
        "contracted_assignment_rows": result["sme_contracted_aggregate"]["assignment_row_count"],
        "unique_contracted_teachers": result["sme_contracted_aggregate"]["unique_contracted_teacher_count"],
        "discovered_path_count": result["sme_discovered_paths"]["count"],
        "person_level_output": result["guards"]["person_level_output"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
