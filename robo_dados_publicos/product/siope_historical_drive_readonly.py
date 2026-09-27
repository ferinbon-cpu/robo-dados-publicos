from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Iterable

from robo_dados_publicos.product import build_product_report, write_product_bundle
from robo_dados_publicos.product.siope_historical import build_siope_historical_answers
from robo_dados_publicos.storage.drive_rest import DriveRESTClient, OAuthCredentials, TokenProvider

ERROR = "STOP_M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY"
PASS = "PASS_M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY"
GOLD_FOLDER_ID = "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4"
MIME_TYPE = "application/json"
REVIEW_PATH = "docs/evidence/M7_SIOPE_POST_GENERALIZATION_OFFLINE_REVIEW_0.8.0.json"
REVIEW_BLOB_SHA = "a547b17edeb8e1865f519ea64a3caddee77820dc"
SOURCE_ID = "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA"


def _spec(year: int, period: int, size: int, sha256: str) -> dict:
    return {
        "year": year,
        "period": period,
        "bytes": size,
        "sha256": sha256,
        "name": (
            f"{SOURCE_ID}__Dados_Gerais_Siope__Limeira_SP__{year}_P{period}__352690__"
            f"{sha256[:12]}__gold_v1.json"
        ),
    }


EXPECTED_GOLD_SPECS = (
    _spec(2016, 1, 1615, "7f84500f5915b21210fda36c638a6d1fecdf1fb1ef0a5a4f9431c5273659d2bd"),
    _spec(2017, 6, 1616, "d9a62de4345c42a8c02a8b97e7c5ccb129b203b1c75f3b4074f09ddf96783d0e"),
    _spec(2018, 6, 1619, "b479a4801a83f3d1f3086ea57b10f25ff393b69714b3a00ea7e6b0256e03ce02"),
    _spec(2019, 6, 1620, "d843f61c37f84d978de8488243492cd8fe09c3a9ad3856c856e314e5063ab19c"),
    _spec(2020, 6, 1621, "073e5e823ad9d37431ef4e89876236ff545c2211a4e9167000c01cef96eab7fa"),
    _spec(2021, 6, 1620, "e8b4888b243aee21af0ba4654a481d502150a45bbbecebfcb5239f5d338d5ef5"),
    _spec(2022, 6, 1623, "4057aac2b18dc7184db992ee989d64c8732c4ad858cc6e8b7520cd50c4d37f68"),
    _spec(2023, 6, 1623, "a4da994fd2a04ef0b3133d9a20855e6809922f19366075d48aab3296ca488272"),
    _spec(2024, 6, 1612, "d6a35db7c42129569c73f19de789d871d0d285929d8eb3fe2a04d5ef03fdd6e0"),
)


class SiopeHistoricalDriveReadonlyError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeHistoricalDriveReadonlyError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def _load_review(root: str | Path) -> dict:
    raw = (Path(root) / REVIEW_PATH).read_bytes()
    _require(_git_blob_sha(raw), REVIEW_BLOB_SHA, "REVIEW_BLOB_SHA")
    try:
        review = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SiopeHistoricalDriveReadonlyError(f"{ERROR}_REVIEW_JSON") from exc
    _require(review.get("status"), "PASS_POST_GENERALIZATION_OFFLINE_REVIEW", "REVIEW_STATUS")
    coverage = review.get("coverage") or {}
    _require(coverage.get("years"), list(range(2016, 2025)), "REVIEW_YEARS")
    _require(coverage.get("year_count"), 9, "REVIEW_YEAR_COUNT")
    _require(coverage.get("verified_layer_objects"), 27, "REVIEW_LAYER_OBJECTS")
    _require(coverage.get("gold_metric_observations"), 72, "REVIEW_GOLD_OBSERVATIONS")
    decision = review.get("decision") or {}
    _require(decision.get("collect_2015_or_earlier_now"), False, "REVIEW_OLDER_YEARS")
    _require(decision.get("future_batch_execution_authorized"), False, "REVIEW_FUTURE_BATCH")
    _require(decision.get("automatic_compliance_claims_authorized"), False, "REVIEW_COMPLIANCE")
    return review


def _validate_specs(specs: Iterable[dict]) -> tuple[dict, ...]:
    rows = tuple(dict(item) for item in specs)
    _require(len(rows), 9, "SPEC_COUNT")
    _require([row.get("year") for row in rows], list(range(2016, 2025)), "SPEC_YEARS")
    _require([row.get("period") for row in rows], [1, 6, 6, 6, 6, 6, 6, 6, 6], "SPEC_PERIODS")
    for row in rows:
        year = row["year"]
        sha256 = row.get("sha256")
        _require(isinstance(sha256, str) and len(sha256) == 64, True, f"SPEC_SHA_{year}")
        _require(isinstance(row.get("bytes"), int) and row["bytes"] > 0, True, f"SPEC_BYTES_{year}")
        expected_name = (
            f"{SOURCE_ID}__Dados_Gerais_Siope__Limeira_SP__{year}_P{row['period']}__352690__"
            f"{sha256[:12]}__gold_v1.json"
        )
        _require(row.get("name"), expected_name, f"SPEC_NAME_{year}")
    return rows


def describe_gate(*, root: str | Path, specs: Iterable[dict] = EXPECTED_GOLD_SPECS) -> dict:
    _load_review(root)
    rows = _validate_specs(specs)
    return {
        "status": f"{PASS}_DESIGN",
        "gate_id": "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY_0_8_0",
        "years": [row["year"] for row in rows],
        "year_count": 9,
        "gold_count": 9,
        "gold_metric_count_per_year": 8,
        "gold_metric_observations": 72,
        "drive_lookup_count": 9,
        "drive_download_count": 9,
        "drive_write_count": 0,
        "source_get_count": 0,
        "source_network_authorized": False,
        "publication_authorized": False,
        "future_batch_execution_authorized": False,
        "retry_authorized": False,
        "pagination_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "imputation_authorized": False,
        "automatic_compliance_claims_authorized": False,
        "drive_target": "08_OUTPUTS",
    }


def _preflight_metadata(drive, specs: tuple[dict, ...]) -> list[tuple[dict, str]]:  # noqa: ANN001
    prepared: list[tuple[dict, str]] = []
    for spec in specs:
        year = spec["year"]
        matches = drive.find_by_name(GOLD_FOLDER_ID, spec["name"])
        _require(len(matches), 1, f"REMOTE_NAME_MATCH_COUNT_{year}")
        metadata = matches[0]
        _require(metadata.get("name"), spec["name"], f"REMOTE_NAME_{year}")
        _require(metadata.get("mimeType"), MIME_TYPE, f"REMOTE_MIME_{year}")
        _require(str(metadata.get("size")), str(spec["bytes"]), f"REMOTE_SIZE_{year}")
        _require(GOLD_FOLDER_ID in (metadata.get("parents") or []), True, f"REMOTE_PARENT_{year}")
        file_id = metadata.get("id")
        if not isinstance(file_id, str) or not file_id:
            raise SiopeHistoricalDriveReadonlyError(f"{ERROR}_REMOTE_ID_{year}")
        prepared.append((spec, file_id))
    return prepared


def _download_payloads(drive, prepared: list[tuple[dict, str]]) -> list[dict]:  # noqa: ANN001
    payloads: list[dict] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for spec, file_id in prepared:
            year = spec["year"]
            destination = root / f"gold_{year}.json"
            downloaded = drive.get(file_id, destination)
            raw = destination.read_bytes()
            actual_sha = hashlib.sha256(raw).hexdigest()
            _require(downloaded.get("bytes"), spec["bytes"], f"DOWNLOADED_BYTES_{year}")
            _require(downloaded.get("sha256"), spec["sha256"], f"DOWNLOADED_SHA_{year}")
            _require(len(raw), spec["bytes"], f"READBACK_BYTES_{year}")
            _require(actual_sha, spec["sha256"], f"READBACK_SHA_{year}")
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise SiopeHistoricalDriveReadonlyError(f"{ERROR}_READBACK_JSON_{year}") from exc
            if not isinstance(payload, dict):
                raise SiopeHistoricalDriveReadonlyError(f"{ERROR}_READBACK_OBJECT_{year}")
            payloads.append(payload)
    return payloads


def run_readonly_gate(
    *,
    root: str | Path,
    output_dir: str | Path,
    generated_at: str,
    drive=None,  # noqa: ANN001
    specs: Iterable[dict] = EXPECTED_GOLD_SPECS,
) -> dict:
    design = describe_gate(root=root, specs=specs)
    rows = _validate_specs(specs)
    if drive is None:
        drive = DriveRESTClient(TokenProvider(OAuthCredentials.from_env()))

    # All nine remote identities are checked before the first download.
    prepared = _preflight_metadata(drive, rows)
    payloads = _download_payloads(drive, prepared)
    answers = build_siope_historical_answers(payloads)
    _require(len(answers), 8, "ANSWER_ROW_COUNT")

    report = build_product_report(
        answers,
        report_id="SIOPE_LIMEIRA_HISTORICAL_2016_2024",
        title="SIOPE Limeira — série histórica 2016–2024",
        scope="FNDE/SIOPE Dados_Gerais_Siope — Limeira/SP — Gold aritmético validado — 2016–2024",
        generated_at=generated_at,
        limitations=(
            "Não constitui auditoria fiscal nem conclusão de cumprimento de MDE/Fundeb.",
            "Valores por habitante não são deflacionados neste adaptador.",
            "A apresentação não substitui os Gold e suas proveniências.",
        ),
        notes="2016 usa período anual P1; 2017–2024 usam P6.",
        software_version="0.8.0",
    )
    manifest = write_product_bundle(report, output_dir)
    _require(report["report_card"]["row_count"], 8, "REPORT_ROW_COUNT")
    _require(manifest.get("publication_status"), "LOCAL_ONLY_NOT_PUBLISHED", "PUBLICATION_STATUS")
    _require(manifest.get("drive_target"), "08_OUTPUTS", "DRIVE_TARGET")
    file_names = [item.get("name") for item in manifest.get("files", [])]
    _require(
        file_names,
        ["report.json", "report_card.json", "table.csv", "report.md", "report.html", "report.pdf"],
        "BUNDLE_FILES",
    )

    return {
        "status": PASS,
        "gate_id": design["gate_id"],
        "years": design["years"],
        "year_count": 9,
        "gold_count": 9,
        "metric_row_count": 8,
        "gold_metric_observations": 72,
        "drive_lookup_count": 9,
        "drive_download_count": 9,
        "drive_write_count": 0,
        "source_get_count": 0,
        "source_network_called": False,
        "drive_network_called": True,
        "remote_file_id_persisted": False,
        "report_status": report["report_card"]["status"],
        "publication_status": manifest["publication_status"],
        "publication_authorized": False,
        "drive_target": manifest["drive_target"],
        "bundle_files": [item["name"] for item in manifest["files"]] + ["manifest.json"],
        "future_batch_execution_authorized": False,
        "retry_authorized": False,
        "pagination_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "imputation_performed": False,
        "compliance_claims_authorized": False,
        "next_gate": "M8_SIOPE_HISTORICAL_PRODUCT_OUTPUT_PUBLICATION_REVIEW_0_8_0",
    }
