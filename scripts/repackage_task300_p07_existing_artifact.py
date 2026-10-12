"""TASK300: manually repackage the verified TASK296/P07 existing GitHub artifact.

Zero official-site GETs; zero Drive operations. Preserve exact original PDFs inside
a ZIP, then slice that ZIP into five lossless 70 MiB parts (one artifact per part).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.download_jom_2026_pending_manual import batch_map
from scripts.download_jom_loa2027_pilot import inspect_pdf

SOURCE_RUN = 38275577819
SOURCE_HEAD = "41993a2b1fb2ab41f13b455650ad898ea3678f2d"
SOURCE_ARTIFACT = "task296-jom-P07-originais-manifesto"
SOURCE_SCHEMA = "TASK296_JOM_PENDING_BATCH_RESULT_V1"
EDITIONS = (7278, 7279, 7280, 7281, 7282, 7285, 7286, 7295, 7296)
PART_BYTES = 70 * 1024 * 1024
PART_COUNT = 6
MAX_BUNDLE_BYTES = PART_BYTES * PART_COUNT
MAX_PDF = 200 * 1024 * 1024
BUNDLE_NAME = "TASK300_P07_NINE_EXACT_ORIGINALS.zip"


class Stop300(RuntimeError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise Stop300(code)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_owner_context(env: dict) -> None:
    require(
        env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_RUN_ATTEMPT") == "1"
        and env.get("TASK300_OWNER_CONFIRM") == "true"
        and env.get("TASK300_SOURCE_RUN") == str(SOURCE_RUN)
        and bool(re.fullmatch("[0-9a-f]{40}", env.get("GITHUB_SHA", ""))),
        "STOP_TASK300_OWNER_MANUAL_MAIN_GATE",
    )


def create_parts(source_dir: Path, output_dir: Path) -> dict:
    require(source_dir.is_dir() and not output_dir.exists(), "STOP_TASK300_PATH_PRECONDITION")
    manifest_path = source_dir / "manifest.json"
    try:
        mf = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Stop300("STOP_TASK300_SOURCE_MANIFEST_UNREADABLE") from exc
    require(
        mf.get("schema") == SOURCE_SCHEMA
        and mf.get("batch") == "P07"
        and mf.get("github_sha") == SOURCE_HEAD
        and mf.get("status") == "PASS_ALL_PDFS_IN_TEMP_ARTIFACT"
        and mf.get("requested_count") == 9
        and mf.get("validated_count") == 9
        and mf.get("failed_count") == 0
        and mf.get("get_attempts") == 9
        and mf.get("retry_count") == 0
        and mf.get("drive_write_count") == 0
        and mf.get("publication_count") == 0,
        "STOP_TASK300_SOURCE_PROVENANCE",
    )
    expected_rows = batch_map()["P07"]
    require(tuple(x["edition"] for x in expected_rows) == EDITIONS,
            "STOP_TASK300_FIXTURE_EDITION_DRIFT")
    rows = mf.get("documents")
    require(isinstance(rows, list) and len(rows) == 9 and
            tuple(x.get("edition_candidate") for x in rows) == EDITIONS,
            "STOP_TASK300_MANIFEST_EDITION_DRIFT")
    originals = source_dir / "originals"
    names = {f"JOM_{ed}_2026_ORIGINAL.pdf" for ed in EDITIONS}
    require(originals.is_dir() and
            {x.name for x in originals.iterdir()} == names,
            "STOP_TASK300_EXACT_ORIGINAL_FILE_SET")
    verified = []
    for expected, row in zip(expected_rows, rows):
        edition = expected["edition"]
        filename = f"JOM_{edition}_2026_ORIGINAL.pdf"
        file = originals / filename
        require(
            row.get("url") == expected["url"]
            and row.get("file_name") == filename
            and row.get("status") == "VALIDATED_ORIGINAL_IN_ARTIFACT_ONLY"
            and row.get("request_attempts") == 1
            and row.get("cover_edition_verified") is True
            and row.get("custodied_in_sme") is False
            and type(row.get("bytes")) is int
            and 100 < row["bytes"] <= MAX_PDF
            and file.is_file() and file.stat().st_size == row["bytes"]
            and bool(re.fullmatch("[a-f0-9]{64}", row.get("sha256", ""))),
            f"STOP_TASK300_METADATA_{edition}",
        )
        require(sha256_file(file) == row["sha256"],
                f"STOP_TASK300_SHA256_{edition}")
        require(inspect_pdf(file, edition) == row.get("pages"),
                f"STOP_TASK300_COVER_OR_PAGES_{edition}")
        verified.append((edition, file, row))

    # No output or upload until all nine source PDFs have passed all checks.
    output_dir.mkdir(parents=True, exist_ok=False)
    bundle = output_dir / BUNDLE_NAME
    bundle_manifest = {
        "schema": "TASK300_P07_LOSSLESS_ORIGINAL_BUNDLE_V1",
        "source_run": SOURCE_RUN, "source_head": SOURCE_HEAD,
        "source_artifact": SOURCE_ARTIFACT,
        "editions": list(EDITIONS),
        "documents": [
            {"edition": ed, "name": file.name, "bytes": row["bytes"],
             "pages": row["pages"], "sha256": row["sha256"],
             "url": row["url"]}
            for ed, file, row in verified
        ],
        "original_bytes_unchanged": True,
        "drive_custody": False,
    }
    with zipfile.ZipFile(bundle, "x", compression=zipfile.ZIP_STORED,
                         allowZip64=True) as zip_out:
        for _, file, _ in verified:
            zip_out.write(file, arcname="originals/" + file.name)
        zip_out.write(manifest_path, arcname="source_manifest_TASK296.json")
        zip_out.writestr(
            "manifest_TASK300_bundle.json",
            json.dumps(bundle_manifest, ensure_ascii=False, sort_keys=True, indent=2),
        )
    require(bundle.stat().st_size > (PART_COUNT - 1) * PART_BYTES
            and bundle.stat().st_size <= MAX_BUNDLE_BYTES,
            "STOP_TASK300_EXPECTED_EXACTLY_FIVE_PARTS")
    with zipfile.ZipFile(bundle, "r") as check:
        require(check.testzip() is None and
                {name for name in check.namelist() if name.endswith(".pdf")}
                == {"originals/" + file.name for _, file, _ in verified},
                "STOP_TASK300_BUNDLE_ZIP_VALIDATION")
    bundle_sha = sha256_file(bundle)
    package_dir = output_dir / "parts"
    package_dir.mkdir()
    parts = []
    with bundle.open("rb") as reader:
        for i in range(1, PART_COUNT + 1):
            part = reader.read(PART_BYTES)
            require(0 < len(part) <= PART_BYTES, "STOP_TASK300_PART_LENGTH")
            part_filename = f"{BUNDLE_NAME}.part{i:02d}"
            meta = {
                "schema": "TASK300_P07_SPLIT_PART_V1",
                "part_index": i, "total_parts": PART_COUNT,
                "source_run": SOURCE_RUN, "bundle_name": BUNDLE_NAME,
                "bundle_bytes": bundle.stat().st_size,
                "bundle_sha256": bundle_sha, "part_sha256": hashlib.sha256(part).hexdigest(),
                "part_bytes": len(part),
                "reconstruct": "binary concatenate all part files in ascending part_index order",
                "not_drive_custody": True,
            }
            dst = package_dir / f"TASK300_P07_PART_{i:02d}.zip"
            with zipfile.ZipFile(dst, "x", compression=zipfile.ZIP_STORED) as z:
                z.writestr(part_filename, part)
                z.writestr("manifest_part.json", json.dumps(meta, indent=2, sort_keys=True))
            require(dst.stat().st_size < 95 * 1024 * 1024,
                    "STOP_TASK300_PACKAGE_ABOVE_DRIVE_LIMIT")
            with zipfile.ZipFile(dst, "r") as verify:
                require(verify.testzip() is None,
                        "STOP_TASK300_PART_ZIP_CRC")
            parts.append({"file": dst.name, "bytes": dst.stat().st_size,
                          "sha256": sha256_file(dst),
                          "part_sha256": meta["part_sha256"]})
        require(reader.read(1) == b"", "STOP_TASK300_UNREAD_BUNDLE_BYTES")

    qa = {"schema": "TASK300_P07_FIVE_PART_PACKAGES_QA_V1",
          "status": "PASS_P07_9_ORIGINALS_IN_FIVE_LOSSLESS_PARTS",
          "source_run": SOURCE_RUN, "source_artifact": SOURCE_ARTIFACT,
          "source_head": SOURCE_HEAD, "verified_pdfs": 9,
          "bundle_name": BUNDLE_NAME, "bundle_bytes": bundle.stat().st_size,
          "bundle_sha256": bundle_sha,
          "originals": bundle_manifest["documents"], "parts": parts,
          "public_site_gets": 0, "drive_writes": 0,
          "not_drive_custody": True}
    (output_dir / "QA_TASK300_P07.json").write_text(
        json.dumps(qa, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return qa


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    validate_owner_context(os.environ)
    print(json.dumps(create_parts(args.source, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
