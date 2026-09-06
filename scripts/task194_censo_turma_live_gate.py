from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task194_censo_turma_2025_live_recovery.v1.json"


class Task194Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194Stop(code)


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194_CENSO_TURMA_2025_LIVE_RECOVERY_V1", "TASK194_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_PRIMARY_SOURCE_RECOVERY", "TASK194_MODE")
    source = obj["source"]
    parsed = urllib.parse.urlparse(source["url"])
    _stop(parsed.scheme == "https", "TASK194_SOURCE_SCHEME")
    _stop(parsed.hostname == source["allowed_host"], "TASK194_SOURCE_HOST")
    _stop(source["max_http_attempts"] == 3, "TASK194_HTTP_ATTEMPT_BUDGET")
    _stop(source["expected_turma_md5"] == "438A3A3FC37F28E7E50E57D7CD8B9DAC", "TASK194_TURMA_MD5_CONTRACT")
    _stop(obj["limeira_filter"]["expected_active_school_count"] == 69, "TASK194_EXPECTED_SCHOOLS")
    _stop(obj["ai40_seed"]["expected_count"] == 40, "TASK194_EXPECTED_AI40")
    _stop(obj["reconciliation"]["expected_ei_only_count"] == 29, "TASK194_EXPECTED_EI29")
    _stop(obj["reconciliation"]["expected_ei_only_qt_tur_bas_sum"] == 294, "TASK194_EXPECTED_EI29_CLASSES")
    output = obj["output"]
    _stop(output["sanitized_json_only"] is True, "TASK194_SANITIZED_ONLY")
    _stop(output["raw_zip_persisted"] is False, "TASK194_RAW_ZIP_PERSISTENCE")
    _stop(output["raw_csv_persisted"] is False, "TASK194_RAW_CSV_PERSISTENCE")
    _stop(output["raw_artifact_uploaded"] is False, "TASK194_RAW_ARTIFACT")
    _stop(all(output[k] is False for k in ("drive_write", "serving", "publication", "schedule", "recurrence")), "TASK194_REMOTE_EFFECT")
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj = _load(contract_path)
    _stop(len(main_sha) == 40 and all(ch in "0123456789abcdef" for ch in main_sha.lower()), "TASK194_AUTH_SHA")
    return (
        "TASK194_CENSO_TURMA_2025_LIVE_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} "
        f"max_http_attempts={obj['source']['max_http_attempts']} raw_persist=0"
    )


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_host: str):
        super().__init__()
        self.allowed_host = allowed_host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        host = urllib.parse.urlparse(newurl).hostname
        if host != self.allowed_host:
            raise Task194Stop("TASK194_CROSS_HOST_REDIRECT")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_once(url: str, destination: Path, *, allowed_host: str) -> tuple[str, int]:
    opener = urllib.request.build_opener(_SameHostRedirect(allowed_host))
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "robo-dados-publicos-task194/0.8.0",
            "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
        },
        method="GET",
    )
    sha256 = hashlib.sha256()
    size = 0
    with opener.open(request, timeout=180) as response, destination.open("wb") as out:
        final_host = urllib.parse.urlparse(response.geturl()).hostname
        _stop(final_host == allowed_host, "TASK194_FINAL_HOST")
        while True:
            chunk = response.read(4 * 1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            sha256.update(chunk)
            size += len(chunk)
    _stop(size > 0, "TASK194_EMPTY_PACKAGE")
    return sha256.hexdigest(), size


def download_official_package(destination: Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(contract_path)
    source = obj["source"]
    errors: list[str] = []
    for attempt in range(1, int(source["max_http_attempts"]) + 1):
        try:
            destination.unlink(missing_ok=True)
            package_sha256, package_bytes = _download_once(
                source["url"],
                destination,
                allowed_host=source["allowed_host"],
            )
            return {
                "attempts_used": attempt,
                "package_sha256": package_sha256,
                "package_bytes": package_bytes,
            }
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Task194Stop) as exc:
            destination.unlink(missing_ok=True)
            errors.append(type(exc).__name__)
            if isinstance(exc, Task194Stop) and str(exc) in {"TASK194_CROSS_HOST_REDIRECT", "TASK194_FINAL_HOST"}:
                raise
            if attempt < int(source["max_http_attempts"]):
                time.sleep(2 * attempt)
    raise Task194Stop("TASK194_DOWNLOAD_FAILED:" + ",".join(errors))


def _find_member(zf: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name for name in zf.namelist()
        if Path(name).name.casefold() == basename.casefold()
    ]
    _stop(len(matches) == 1, f"TASK194_MEMBER_{basename}_COUNT")
    return matches[0]


def _member_hashes(zf: zipfile.ZipFile, member: str) -> tuple[str, str, int]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    size = 0
    with zf.open(member, "r") as handle:
        while True:
            chunk = handle.read(4 * 1024 * 1024)
            if not chunk:
                break
            md5.update(chunk)
            sha256.update(chunk)
            size += len(chunk)
    return md5.hexdigest().upper(), sha256.hexdigest(), size


def _normalized_int(value: Any, *, code: str) -> int:
    text = str(value or "").strip()
    _stop(bool(text), code)
    try:
        number = int(float(text.replace(",", ".")))
    except ValueError as exc:
        raise Task194Stop(code) from exc
    return number


def _normalized_code(value: Any) -> str:
    text = str(value or "").strip()
    _stop(bool(text), "TASK194_EMPTY_CODE")
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _read_ai40_codes(path: Path, expected_count: int) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _stop(reader.fieldnames is not None and "codigo_inep" in reader.fieldnames, "TASK194_AI40_HEADER")
        codes = {_normalized_code(row["codigo_inep"]) for row in reader}
    _stop(len(codes) == expected_count, "TASK194_AI40_COUNT")
    return codes


def _active_limeira_municipal_codes(
    zf: zipfile.ZipFile,
    member: str,
    obj: dict[str, Any],
) -> set[str]:
    required = {
        "CO_ENTIDADE",
        "CO_MUNICIPIO",
        "TP_DEPENDENCIA",
        "TP_SITUACAO_FUNCIONAMENTO",
    }
    result: set[str] = set()
    with zf.open(member, "r") as raw, io.TextIOWrapper(raw, encoding="latin-1", newline="") as text:
        reader = csv.DictReader(text, delimiter=";")
        _stop(reader.fieldnames is not None and required.issubset(set(reader.fieldnames)), "TASK194_ESCOLA_HEADER")
        for row in reader:
            if _normalized_code(row.get("CO_MUNICIPIO")) != obj["limeira_filter"]["co_municipio"]:
                continue
            if _normalized_int(row.get("TP_DEPENDENCIA"), code="TASK194_DEPENDENCIA") != obj["limeira_filter"]["tp_dependencia_municipal"]:
                continue
            if _normalized_int(row.get("TP_SITUACAO_FUNCIONAMENTO"), code="TASK194_SITUACAO") != obj["limeira_filter"]["tp_situacao_funcionamento_active"]:
                continue
            code = _normalized_code(row.get("CO_ENTIDADE"))
            _stop(code not in result, "TASK194_DUPLICATE_ACTIVE_SCHOOL")
            result.add(code)
    _stop(len(result) == obj["limeira_filter"]["expected_active_school_count"], "TASK194_ACTIVE_SCHOOL_COUNT")
    return result


def _turma_values(
    zf: zipfile.ZipFile,
    member: str,
    active_codes: set[str],
) -> dict[str, int]:
    required = {"CO_ENTIDADE", "QT_TUR_BAS"}
    values: dict[str, int] = {}
    with zf.open(member, "r") as raw, io.TextIOWrapper(raw, encoding="latin-1", newline="") as text:
        reader = csv.DictReader(text, delimiter=";")
        _stop(reader.fieldnames is not None and required.issubset(set(reader.fieldnames)), "TASK194_TURMA_HEADER")
        for row in reader:
            code = _normalized_code(row.get("CO_ENTIDADE"))
            if code not in active_codes:
                continue
            _stop(code not in values, "TASK194_DUPLICATE_TURMA_ROW")
            value = _normalized_int(row.get("QT_TUR_BAS"), code="TASK194_QT_TUR_BAS")
            _stop(value >= 0, "TASK194_NEGATIVE_TURMAS")
            values[code] = value
    _stop(set(values) == active_codes, "TASK194_TURMA_ACTIVE_COVERAGE")
    return values


def derive_sanitized_aggregate(
    package_path: str | Path,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
    expected_turma_md5: str | None = None,
    ai40_seed_path: str | Path | None = None,
) -> dict[str, Any]:
    obj = _load(contract_path)
    package_path = Path(package_path)
    _stop(package_path.is_file(), "TASK194_PACKAGE_MISSING")
    with zipfile.ZipFile(package_path, "r") as zf:
        escola_member = _find_member(zf, obj["source"]["expected_escola_basename"])
        turma_member = _find_member(zf, obj["source"]["expected_turma_basename"])
        md5_member = _find_member(zf, obj["source"]["expected_md5_manifest_basename"])

        turma_md5, turma_sha256, turma_bytes = _member_hashes(zf, turma_member)
        expected_md5 = (expected_turma_md5 or obj["source"]["expected_turma_md5"]).upper()
        _stop(turma_md5 == expected_md5, "TASK194_TURMA_MD5_MISMATCH")

        manifest_text = zf.read(md5_member).decode("latin-1", errors="replace").upper()
        _stop(expected_md5 in manifest_text, "TASK194_MD5_NOT_IN_OFFICIAL_MANIFEST")
        _stop(obj["source"]["expected_turma_basename"].upper() in manifest_text, "TASK194_TURMA_NOT_IN_MD5_MANIFEST")

        active_codes = _active_limeira_municipal_codes(zf, escola_member, obj)
        seed = Path(ai40_seed_path) if ai40_seed_path is not None else ROOT / obj["ai40_seed"]["path"]
        ai40_codes = _read_ai40_codes(seed, obj["ai40_seed"]["expected_count"])
        _stop(ai40_codes.issubset(active_codes), "TASK194_AI40_NOT_SUBSET_ACTIVE")
        ei29_codes = active_codes - ai40_codes
        _stop(len(ei29_codes) == obj["reconciliation"]["expected_ei_only_count"], "TASK194_EI29_COUNT")

        turma_by_school = _turma_values(zf, turma_member, active_codes)
        ai40_sum = sum(turma_by_school[code] for code in ai40_codes)
        ei29_sum = sum(turma_by_school[code] for code in ei29_codes)
        total = sum(turma_by_school.values())
        _stop(ei29_sum == obj["reconciliation"]["expected_ei_only_qt_tur_bas_sum"], "TASK194_EI29_CLASS_RECONCILIATION")
        _stop(total == ai40_sum + ei29_sum, "TASK194_CLASS_SUM_RECONCILIATION")

        active_codes_sha256 = hashlib.sha256(
            "\n".join(sorted(active_codes)).encode("ascii")
        ).hexdigest()
        ai40_codes_sha256 = hashlib.sha256(
            "\n".join(sorted(ai40_codes)).encode("ascii")
        ).hexdigest()
        ei29_codes_sha256 = hashlib.sha256(
            "\n".join(sorted(ei29_codes)).encode("ascii")
        ).hexdigest()

        return {
            "schema": "TASK194_CENSO_TURMA_2025_SANITIZED_RESULT_V1",
            "status": "PASS",
            "source": {
                "official_url": obj["source"]["url"],
                "turma_member_basename": obj["source"]["expected_turma_basename"],
                "turma_md5": turma_md5,
                "turma_md5_expected": expected_md5,
                "turma_md5_verified": True,
                "turma_sha256": turma_sha256,
                "turma_uncompressed_bytes": turma_bytes,
                "official_md5_manifest_verified": True,
            },
            "scope": {
                "period": "2025",
                "municipality_code": obj["limeira_filter"]["co_municipio"],
                "network": "MUNICIPAL",
                "active_school_count": len(active_codes),
                "active_school_codes_sha256": active_codes_sha256,
            },
            "class_count": {
                "metric_id": "CLASS_COUNT",
                "source_column": "QT_TUR_BAS",
                "semantic": obj["reconciliation"]["class_metric_semantic"],
                "network_value": total,
                "ai40_school_count": len(ai40_codes),
                "ai40_class_count": ai40_sum,
                "ai40_codes_sha256": ai40_codes_sha256,
                "ei29_school_count": len(ei29_codes),
                "ei29_class_count": ei29_sum,
                "ei29_codes_sha256": ei29_codes_sha256,
                "ei29_expected_class_count": obj["reconciliation"]["expected_ei_only_qt_tur_bas_sum"],
                "turma_rows_for_active_schools": len(turma_by_school),
            },
            "guards": {
                "all_active_69_have_turma_row": len(turma_by_school) == 69,
                "ai40_subset_verified": True,
                "ei29_reconciliation_verified": True,
                "class_count_is_sum_qt_tur_bas_not_row_count": True,
                "raw_bytes_persisted": False,
                "drive_write": False,
                "serving": False,
                "publication": False,
                "schedule": False,
                "recurrence": False,
            },
        }


def run_live(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(contract_path)
    main_sha = str(os.environ.get("GITHUB_SHA") or "")
    checked_out_sha = str(os.environ.get("TASK194_CHECKED_OUT_SHA") or "")
    auth_comment = str(os.environ.get("TASK194_AUTH_COMMENT") or "")
    issue_number = str(os.environ.get("TASK194_ISSUE_NUMBER") or "")
    _stop(main_sha == checked_out_sha, "TASK194_CHECKOUT_SHA")
    _stop(issue_number == str(obj["authorization_issue"]), "TASK194_ISSUE")
    _stop(auth_comment == exact_auth_comment(main_sha, contract_path), "TASK194_AUTH_COMMENT")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task194-") as td:
        package = Path(td) / "microdados_censo_escolar_2025_.zip"
        download_meta = download_official_package(package, contract_path)
        result = derive_sanitized_aggregate(package, contract_path=contract_path)
        result["source"]["package_sha256"] = download_meta["package_sha256"]
        result["source"]["package_bytes"] = download_meta["package_bytes"]
        result["source"]["http_attempts_used"] = download_meta["attempts_used"]
        result["authorization"] = {
            "issue": obj["authorization_issue"],
            "main_sha": main_sha,
            "exact_comment_verified": True,
        }
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _stop(output_path.is_file(), "TASK194_OUTPUT_MISSING")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    result = run_live(args.output, args.contract)
    print(json.dumps({
        "status": result["status"],
        "active_school_count": result["scope"]["active_school_count"],
        "class_count": result["class_count"]["network_value"],
        "ei29_class_count": result["class_count"]["ei29_class_count"],
        "turma_md5_verified": result["source"]["turma_md5_verified"],
        "raw_bytes_persisted": result["guards"]["raw_bytes_persisted"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
