"""TASK297: Repackage the verified TASK296 P01 artifact in 3 Drive-safe ZIPs.

No public source GETs, Drive access, retries or mutation of source files.
The JOM 7159 PDF is losslessly split into two binary chunks, both SHA-checked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts.download_jom_loa2027_pilot import inspect_pdf

SOURCE_RUN=38184075627
SOURCE_HEAD="5869fbdfb803e06737696e4f487b814cea663bc3"
SOURCE_ARTIFACT="task296-jom-P01-originais-manifesto"
SOURCE_SCHEMA="TASK296_JOM_PENDING_BATCH_RESULT_V1"
EDITIONS=tuple(range(7152,7161))
CHUNK=70*1024*1024
MAX_OUTPUT=95*1024*1024

class Stop297(RuntimeError):pass
def need(ok,code):
    if not ok:raise Stop297(code)
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
    return h.hexdigest()

def validate_context(env):
    need(env.get("GITHUB_EVENT_NAME")=="workflow_dispatch" and
         env.get("GITHUB_REF")=="refs/heads/main" and
         env.get("GITHUB_RUN_ATTEMPT")=="1" and
         env.get("TASK297_OWNER_CONFIRM")=="true" and
         env.get("TASK297_SOURCE_RUN")==str(SOURCE_RUN) and
         bool(re.fullmatch("[0-9a-f]{40}",env.get("GITHUB_SHA",""))),
         "STOP_TASK297_MANUAL_MAIN_CONFIRMATION")

def build(source:Path,out:Path)->dict:
    need(not out.exists(),"STOP_OUTPUT_EXISTS")
    need(source.is_dir(),"STOP_SOURCE_DIR_MISSING")
    try:m=json.loads((source/"manifest.json").read_text(encoding="utf-8"))
    except (OSError,ValueError) as e:raise Stop297("STOP_SOURCE_MANIFEST_UNREADABLE") from e
    need(m.get("schema")==SOURCE_SCHEMA and m.get("github_sha")==SOURCE_HEAD and
         m.get("batch")=="P01" and m.get("requested_count")==9 and
         m.get("validated_count")==9 and m.get("failed_count")==0 and
         m.get("get_attempts")==9 and m.get("retry_count")==0 and
         m.get("drive_write_count")==0, "STOP_SOURCE_RUN_PROVENANCE")
    rows=m.get("documents")
    need(isinstance(rows,list) and len(rows)==9 and
         tuple(x.get("edition_candidate") for x in rows)==EDITIONS, "STOP_SOURCE_EDITIONS")
    names={f"JOM_{e}_2026_ORIGINAL.pdf" for e in EDITIONS}
    original_dir=source/"originals"
    need(original_dir.is_dir() and {x.name for x in original_dir.iterdir()}==names,
         "STOP_SOURCE_FILES_DRIFT")
    # Validate every source PDF before any output is created.
    for row in rows:
        ed=row["edition_candidate"]
        name=f"JOM_{ed}_2026_ORIGINAL.pdf"
        p=original_dir/name
        need(row.get("status")=="VALIDATED_ORIGINAL_IN_ARTIFACT_ONLY" and
             row.get("file_name")==name and row.get("cover_edition_verified") is True and
             row.get("request_attempts")==1 and row.get("custodied_in_sme") is False,
             f"STOP_DOCUMENT_METADATA_{ed}")
        need(p.stat().st_size==row.get("bytes") and
             sha(p)==row.get("sha256") and
             inspect_pdf(p,ed)==row.get("pages"),f"STOP_PRIMARY_BYTES_OR_COVER_{ed}")
    out.mkdir(parents=True,exist_ok=False)
    src_manifest=source/"manifest.json"
    small=[e for e in EDITIONS if e!=7159]
    part_manifest={
        "schema":"TASK297_P01_GROUPED_ORIGINALS_V1",
        "source_run":SOURCE_RUN,"source_artifact":SOURCE_ARTIFACT,
        "source_sha":SOURCE_HEAD,
        "editions":small,"originals":[r for r in rows if r["edition_candidate"]!=7159],
        "no_original_bytes_changed":True,
    }
    smallzip=out/"TASK297_P01_EIGHT_ORIGINALS.zip"
    with zipfile.ZipFile(smallzip,"x",compression=zipfile.ZIP_STORED) as z:
        for ed in small:
            name=f"JOM_{ed}_2026_ORIGINAL.pdf"
            z.write(original_dir/name,arcname=f"originals/{name}")
        z.write(src_manifest,arcname="manifest_task296.json")
        z.writestr("manifest_task297_group8.json",json.dumps(part_manifest,ensure_ascii=False,sort_keys=True,indent=2))
    big=original_dir/"JOM_7159_2026_ORIGINAL.pdf"
    bigrow=next(r for r in rows if r["edition_candidate"]==7159)
    sizes=[]; outputs=[smallzip]
    with big.open("rb") as f:
        for index in (1,2):
            payload=f.read(CHUNK)
            need(bool(payload) and len(payload)<=CHUNK,"STOP_BIG_CHUNK_EMPTY_OR_OVERSIZE")
            sizes.append(len(payload))
            extra={
                "schema":"TASK297_P01_LOSSLESS_PART_V1",
                "source_run":SOURCE_RUN,"source_artifact":SOURCE_ARTIFACT,
                "source_head":SOURCE_HEAD,"edition":7159,
                "original_file":big.name,"original_sha256":bigrow["sha256"],
                "original_bytes":bigrow["bytes"],"part_number":index,
                "part_count":2,"part_size":len(payload),
                "part_sha256":hashlib.sha256(payload).hexdigest(),
                "reassemble_using_binary_concatenation_in_ascending_part_number":True,
            }
            dst=out/f"TASK297_P01_JOM7159_PART{index:02}.zip"
            with zipfile.ZipFile(dst,"x",compression=zipfile.ZIP_STORED) as z:
                z.writestr(f"{big.name}.part{index:02}",payload)
                z.writestr("manifest_task297_part.json",json.dumps(extra,ensure_ascii=False,sort_keys=True,indent=2))
            outputs.append(dst)
        need(f.read(1)==b"","STOP_BIG_TRAILING_BYTES")
    need(sum(sizes)==big.stat().st_size,"STOP_BIG_TOTAL_MISMATCH")
    result=[]
    for p in outputs:
        need(p.stat().st_size<MAX_OUTPUT,"STOP_OUTPUT_MORE_THAN_95MIB")
        with zipfile.ZipFile(p) as z:need(z.testzip() is None,"STOP_PACKAGED_ZIP_CRC")
        result.append({"name":p.name,"sha256":sha(p),"bytes":p.stat().st_size})
    report={"schema":"TASK297_P01_3_PACKAGES_V1","status":"PASS_REPACK_ONLY",
       "source_run":SOURCE_RUN,"source_artifact":SOURCE_ARTIFACT,"source_head":SOURCE_HEAD,
       "pdfs_checked":9,"source_gets":0,"drive_writes":0,"packages":result,
       "all_three_packages_below_95mib":True,"not_sme_custody":True}
    (out/"QA_TASK297_MANIFEST.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    validate_context(os.environ)
    print(json.dumps(build(args.source,args.out),sort_keys=True))
if __name__=="__main__":main()
