"""TASK289: Offline audit and bounded repackage of an EXISTING B06 run artifact.

No official-site network, no source recollection, no Drive IO. The caller must
fetch precisely GitHub Actions run 38067488083 artifact from this same repo.
This script only verifies and stages nine original PDFs (unchanged bytes).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.download_jom_2026_archive_batch import batch_map, BATCH_IDS
from scripts.download_jom_loa2027_pilot import inspect_pdf

RUN_ID = 38067488083
SOURCE_ARTIFACT = "jom2026-originais-B06-manifesto"
GITHUB_HEAD_SHA = "9ebfb5c1d26f570429c40790842cae928b29b8ed"
OUTPUT_CAP_BYTES = 100 * 1024 * 1024
EXACT_EDITIONS = (7244, 7245, 7246, 7247, 7248, 7249, 7250, 7251, 7252)


class RepackStop(RuntimeError):
    pass


def validate_context(env: dict) -> None:
    if not (
        env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_RUN_ATTEMPT") == "1"
        and env.get("JOM_B06_OWNER_CONFIRM") == "true"
        and env.get("JOM_B06_EXISTING_RUN") == str(RUN_ID)
        and re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))
    ):
        raise RepackStop("STOP_REPACK_B06_MANUAL_MAIN_CONTEXT")


def stage_existing_archive(source_dir: Path, out_dir: Path) -> dict:
    if out_dir.exists():
        raise RepackStop("STOP_OUTPUT_EXISTS")
    if not source_dir.is_dir():
        raise RepackStop("STOP_ARCHIVE_DIRECTORY_MISSING")
    manifest_file = source_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise RepackStop("STOP_MANIFEST_NOT_READABLE")

    if not (
        manifest.get("schema") == "LOA2027_JOM_2026_BATCH_9_ORIGINALS_V1"
        and manifest.get("batch") == "B06"
        and manifest.get("github_sha") == GITHUB_HEAD_SHA
        and manifest.get("validated_count") == 9
        and manifest.get("failed_count") == 0
        and manifest.get("source_get_attempts") == 9
        and manifest.get("drive_write_count") == 0
        and manifest.get("publication_count") == 0
        and len(manifest.get("documents", [])) == 9
    ):
        raise RepackStop("STOP_B06_SOURCE_RUN_IDENTITY")
    selected = batch_map()["B06"]
    if tuple(int(r["edition"]) for r in selected) != EXACT_EDITIONS:
        raise RepackStop("STOP_B06_EDITION_LIST_DRIFT")

    expected_urls = {int(r["edition"]): r["document_url"] for r in selected}
    rows = {int(r["edition"]): r for r in manifest["documents"]}
    if set(rows) != set(EXACT_EDITIONS):
        raise RepackStop("STOP_B06_MANIFEST_EDITIONS")
    if {x.name for x in (source_dir / "originals").iterdir()} != {
        f"JOM_{edition}_2026_ORIGINAL.pdf" for edition in EXACT_EDITIONS
    }:
        raise RepackStop("STOP_B06_UNEXPECTED_ORIGINALS")

    # Full validation happens before first staging write; no partial product.
    validated = []
    for edition in EXACT_EDITIONS:
        r = rows[edition]
        file_name = f"JOM_{edition}_2026_ORIGINAL.pdf"
        path = source_dir / "originals" / file_name
        if not (
            r.get("status") == "VALIDATED_ORIGINAL"
            and r.get("file_name") == file_name
            and r.get("url") == expected_urls[edition]
            and r.get("source_id") == f"LIMEIRA_JO_{edition:05d}"
            and r.get("cover_edition_verified") is True
            and r.get("request_attempts") == 1
        ):
            raise RepackStop(f"STOP_B06_SOURCE_METADATA_{edition}")
        data_size = path.stat().st_size
        if data_size != r.get("bytes") or not 0 < data_size < OUTPUT_CAP_BYTES:
            raise RepackStop(f"STOP_B06_OUTPUT_BYTE_CAP_{edition}")
        h = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        if h.hexdigest() != r.get("sha256"):
            raise RepackStop(f"STOP_B06_ORIGINAL_HASH_{edition}")
        pages = inspect_pdf(path, edition)
        if pages != r.get("pages"):
            raise RepackStop(f"STOP_B06_PAGES_{edition}")
        validated.append((edition, path, r))

    out_dir.mkdir(parents=True, exist_ok=False)
    for edition, path, row in validated:
        target_folder = out_dir / str(edition)
        target_folder.mkdir()
        target = target_folder / path.name
        try:
            os.link(path, target)
        except OSError:
            # Fallback only on local file system; content was validated above.
            shutil.copyfile(path, target)
        (target_folder / "manifest_excerpt.json").write_text(
            json.dumps({
                "schema": "LOA2027_TASK289_B06_ARTIFACT_PROVENANCE_V1",
                "original_github_run_id": RUN_ID,
                "original_artifact_name": SOURCE_ARTIFACT,
                "source_github_sha": GITHUB_HEAD_SHA,
                "document": row,
                "no_source_gets": True,
                "no_drive_writes": True,
                "non_mutating_repackage": True,
            }, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "status": "PASS_TASK289_B06_9_SPLIT_ARTIFACTS",
        "input_run_id": RUN_ID,
        "target_editions": list(EXACT_EDITIONS),
        "validated_count": len(validated),
        "source_site_gets": 0,
        "drive_writes": 0,
        "planned_artifacts": 9,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    validate_context(os.environ)
    result = stage_existing_archive(args.source, args.out)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
