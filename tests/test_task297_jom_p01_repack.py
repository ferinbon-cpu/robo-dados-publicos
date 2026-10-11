"""TASK297 repackage: offline, tiny synthetic fixture, zero remote calls."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import repackage_task297_jom_p01 as task

class Task297Tests(unittest.TestCase):
    def setup_source(self,root:Path):
        src=root/"source"
        (src/"originals").mkdir(parents=True)
        docs=[]
        for ed in task.EDITIONS:
            blob=b"%PDF-"+bytes(str(ed),"ascii")+(b"x"*130 if ed==7159 else b"y"*10)
            filename=f"JOM_{ed}_2026_ORIGINAL.pdf"
            (src/"originals"/filename).write_bytes(blob)
            docs.append({
                "edition_candidate":ed,"status":"VALIDATED_ORIGINAL_IN_ARTIFACT_ONLY",
                "file_name":filename,"sha256":hashlib.sha256(blob).hexdigest(),
                "bytes":len(blob),"pages":1,
                "cover_edition_verified":True,"request_attempts":1,
                "custodied_in_sme":False,
            })
        manifest={
            "schema":task.SOURCE_SCHEMA,"github_sha":task.SOURCE_HEAD,
            "batch":"P01","requested_count":9,"validated_count":9,
            "failed_count":0,"get_attempts":9,"retry_count":0,
            "drive_write_count":0,"documents":docs,
        }
        (src/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
        return src

    def test_manual_context(self):
        env={
            "GITHUB_EVENT_NAME":"workflow_dispatch","GITHUB_REF":"refs/heads/main",
            "GITHUB_RUN_ATTEMPT":"1","TASK297_OWNER_CONFIRM":"true",
            "TASK297_SOURCE_RUN":str(task.SOURCE_RUN),"GITHUB_SHA":"a"*40,
        }
        task.validate_context(env)
        for k,v in [
            ("TASK297_OWNER_CONFIRM","false"),("GITHUB_EVENT_NAME","push"),
            ("GITHUB_REF","refs/heads/other"),("TASK297_SOURCE_RUN","other"),
            ("GITHUB_RUN_ATTEMPT","2")]:
            changed={**env,k:v}
            with self.subTest(k=k),self.assertRaises(task.Stop297):
                task.validate_context(changed)

    @patch.object(task,"CHUNK",75)
    @patch.object(task,"inspect_pdf",return_value=1)
    def test_three_archives_reassemble_and_hash(self,_):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            src=self.setup_source(base)
            out=base/"out"
            result=task.build(src,out)
            self.assertEqual(result["status"],"PASS_REPACK_ONLY")
            self.assertEqual(result["pdfs_checked"],9)
            self.assertEqual(len(result["packages"]),3)
            self.assertEqual(result["source_gets"],0)
            import zipfile
            pieces=[]
            for n in (1,2):
                with zipfile.ZipFile(out/f"TASK297_P01_JOM7159_PART{n:02}.zip") as z:
                    data=z.read(f"JOM_7159_2026_ORIGINAL.pdf.part{n:02}")
                    md=json.loads(z.read("manifest_task297_part.json"))
                    self.assertEqual(hashlib.sha256(data).hexdigest(),md["part_sha256"])
                    pieces.append(data)
            original=(src/"originals/JOM_7159_2026_ORIGINAL.pdf").read_bytes()
            self.assertEqual(b"".join(pieces),original)
            with zipfile.ZipFile(out/"TASK297_P01_EIGHT_ORIGINALS.zip") as z:
                self.assertEqual(len([x for x in z.namelist() if x.endswith(".pdf")]),8)

    @patch.object(task,"CHUNK",75)
    @patch.object(task,"inspect_pdf",return_value=1)
    def test_hash_mismatch_stop_before_creating_outputs(self,_):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);src=self.setup_source(b)
            p=src/"originals/JOM_7158_2026_ORIGINAL.pdf"
            p.write_bytes(p.read_bytes()+b"tampered")
            with self.assertRaisesRegex(task.Stop297,"STOP_PRIMARY_BYTES_OR_COVER_7158"):
                task.build(src,b/"out")
            self.assertFalse((b/"out").exists())

    @patch.object(task,"CHUNK",75)
    @patch.object(task,"inspect_pdf",return_value=1)
    def test_oversize_output_stop(self,_):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);src=self.setup_source(b)
            with patch.object(task,"MAX_OUTPUT",10):
                with self.assertRaisesRegex(task.Stop297,"STOP_OUTPUT_MORE_THAN_95MIB"):
                    task.build(src,b/"out")

if __name__=="__main__":
    unittest.main()
