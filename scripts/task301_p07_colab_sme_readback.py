# TASK301: read-only Google Drive SME P07 audit. Run in a Google Colab notebook.
import hashlib, io, json, re, subprocess, sys, tempfile, zipfile
from pathlib import Path
from google.colab import auth
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

BRONZE = "1XQ0Yp5c6Ms7eu3gCIwCMwE0fqIjimwEd"
DRIVE_FILES = {
 "manifest": ("1NckZM66TAf2v8MaQVAyCW6r04bUFPZda", 1737, "e43ce3a88a796d020b41902b94c88b129624d776c05ad4f3fe783a79e5525657"),
 1: ("1iN8QGOujreAw0kW1UbDNucd11lL4XN9c", 73401284, "3f62a277565e41c3cfffc08ba114c7a6f6c8481a18135966b3aa90c06e0ad830"),
 2: ("1Bz373xRd32VScb95LA-c5H7Cj_KyCJVV", 73401284, "433dd308c5106d04a3614ade233170351d96abd973273bb501224f9a5cb6fd9c"),
 3: ("1Lx737WKsYZPLLIXqnXNUPrOS_cOJtCwS", 73401284, "0c903c59135bb0631573d42f1151f19c29e43cac63a1174a9f91b7c570e2f15"),
 4: ("13uHcLw7XcGNkzvn4Uj7XtKnY7nRXphtm", 73401284, "91a364642011f648f44485100ba54ff542eb375e08ae8b9aea4342b8d6ab12ad"),
 5: ("1-jl2LfBOUU7HC_LDqGAi45tsjpjvvtdy", 73401284, "fe3b18ebc4a84445de027cd3bce82a306c6342927a870140e1300a0017e73399"),
 6: ("1V8c84fyaIRLRdhXLipJ49AVvPxJXUSFP", 44103336, "64b0c88da5c77385ca69151e4c650abb70d787210f3e338759364f7261c209af")
}
EDITIONS = (7278, 7279, 7280, 7281, 7282, 7285, 7286, 7295, 7296)

def gate(ok, label):
    if not ok:
        raise RuntimeError("STOP_TASK301_" + label)

def hash_path(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

print("Autorize a conta Google que tenha acesso à pasta SME_LIMEIRA.")
auth.authenticate_user()
credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
drive = build("drive", "v3", credentials=credentials, cache_discovery=False)

def fetch_drive(key, base):
    fileid, size, digest = DRIVE_FILES[key]
    metadata = drive.files().get(fileId=fileid, fields="id,name,size,parents,mimeType", supportsAllDrives=True).execute()
    gate(BRONZE in metadata.get("parents", []), "BRONZE_PARENT_" + str(key))
    gate(int(metadata.get("size", -1)) == size, "BRONZE_SIZE_" + str(key))
    dest = base / ("p07_drive_" + str(key) + ".zip")
    request = drive.files().get_media(fileId=fileid, supportsAllDrives=True)
    with dest.open("wb") as target:
        dl = MediaIoBaseDownload(target, request, chunksize=4*1024*1024)
        done = False
        while not done:
            _, done = dl.next_chunk(num_retries=0)
    gate(dest.stat().st_size == size, "BYTES_" + str(key))
    actual = hash_path(dest)
    gate(actual == digest, "SHA256_" + str(key))
    print("PASS DRIVE SHA256", key, size)
    return dest, {"index": str(key), "id": fileid, "bytes": size, "sha256": actual}

try:
    import fitz
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "-q", "install", "pymupdf"])
    import fitz

with tempfile.TemporaryDirectory(prefix="task301_p07_") as temp_name:
    temp = Path(temp_name)
    report = {"schema": "TASK301_P07_SME_DRIVE_READBACK_V1", "status": "STOP",
              "github_run_id": 38278885620, "bronze_folder_id": BRONZE,
              "source_site_gets": 0, "drive_writes": 0, "packages": [], "documents": []}
    outer_manifest, manifest_evidence = fetch_drive("manifest", temp)
    report["manifest"] = manifest_evidence
    with zipfile.ZipFile(outer_manifest) as archive:
        gate(archive.testzip() is None, "MANIFEST_CRC")
        qa = json.loads(archive.read("QA_TASK300_P07.json"))
    gate(qa.get("schema") == "TASK300_P07_SIX_PART_PACKAGES_QA_V1", "MANIFEST_SCHEMA")
    gate(qa.get("status") == "PASS_P07_9_ORIGINALS_IN_SIX_LOSSLESS_PARTS", "MANIFEST_STATUS")
    gate(qa.get("source_run") == 38275577819 and qa.get("verified_pdfs") == 9, "SOURCE_RUN")
    gate(qa.get("public_site_gets") == 0 and qa.get("drive_writes") == 0, "SOURCE_EFFECTS")
    gate(len(qa.get("parts", [])) == 6 and len(qa.get("originals", [])) == 9, "COUNTS")
    gate(tuple(x["edition"] for x in qa["originals"]) == EDITIONS, "EDITION_ORDER")
    bundle = temp / qa["bundle_name"]
    bundle_hash = hashlib.sha256()
    with bundle.open("wb") as joined:
        for idx in range(1, 7):
            p, evidence = fetch_drive(idx, temp)
            expected = qa["parts"][idx - 1]
            gate(evidence["sha256"] == expected["sha256"] and evidence["bytes"] == expected["bytes"], "PACKAGE_" + str(idx))
            with zipfile.ZipFile(p) as artifact:
                gate(artifact.testzip() is None, "OUTER_CRC_" + str(idx))
                internal_name = "TASK300_P07_PART_%02d.zip" % idx
                gate(artifact.namelist() == [internal_name], "OUTER_NAMES_" + str(idx))
                with zipfile.ZipFile(io.BytesIO(artifact.read(internal_name))) as inner:
                    gate(inner.testzip() is None, "INNER_CRC_" + str(idx))
                    meta = json.loads(inner.read("manifest_part.json"))
                    gate(meta["part_index"] == idx and meta["total_parts"] == 6, "PART_INDEX_" + str(idx))
                    gate(meta["part_sha256"] == expected["part_sha256"], "PART_META_" + str(idx))
                    name = qa["bundle_name"] + ".part%02d" % idx
                    ph = hashlib.sha256()
                    with inner.open(name) as inp:
                        for block in iter(lambda: inp.read(4*1024*1024), b""):
                            ph.update(block)
                            bundle_hash.update(block)
                            joined.write(block)
                    gate(ph.hexdigest() == expected["part_sha256"], "PART_SHA_" + str(idx))
            report["packages"].append(evidence)
    gate(bundle.stat().st_size == qa["bundle_bytes"], "BUNDLE_BYTES")
    gate(bundle_hash.hexdigest() == qa["bundle_sha256"], "BUNDLE_SHA256")
    print("PASS BUNDLE SHA256 E RECONSTRUÇÃO")
    with zipfile.ZipFile(bundle) as z:
        gate(z.testzip() is None, "BUNDLE_CRC")
        names = {n for n in z.namelist() if n.endswith(".pdf")}
        gate(names == {"originals/JOM_%s_2026_ORIGINAL.pdf" % e for e in EDITIONS}, "ORIGINAL_SET")
        for row in qa["originals"]:
            ed = row["edition"]
            b = z.read("originals/JOM_%s_2026_ORIGINAL.pdf" % ed)
            gate(b.startswith(b"%PDF-"), "PDF_SIGNATURE_" + str(ed))
            gate(len(b) == row["bytes"], "PDF_LENGTH_" + str(ed))
            gate(hashlib.sha256(b).hexdigest() == row["sha256"], "PDF_HASH_" + str(ed))
            with fitz.open(stream=b, filetype="pdf") as pdf:
                gate(len(pdf) == row["pages"], "PDF_PAGES_" + str(ed))
                front = " ".join(pdf[i].get_text() for i in range(min(2, len(pdf))))
                gate(re.search(r"(?<!\d)%s(?!\d)" % ed, front) is not None, "PDF_COVER_" + str(ed))
            report["documents"].append({"edition": ed, "sha256": row["sha256"], "bytes": row["bytes"],
                                        "pages": row["pages"], "url": row["url"], "status": "PASS"})
            print("PASS DOCUMENTO", ed)
    gate(len(report["packages"]) == 6 and len(report["documents"]) == 9, "FINAL_COUNT")
    report["bundle_sha256"] = qa["bundle_sha256"]
    report["status"] = "PASS_P07_SIX_DRIVE_READBACKS_AND_NINE_EXACT_PDFS"
    result = Path("/content/TASK301_P07_SME_READBACK_PASS.json")
    result.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS FINAL. Relatório na sessão Colab:", result)
    print("Envie o JSON para concluir a matriz SME; não altere a matriz automaticamente.")
