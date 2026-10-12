"""Bounded offline lossless reconstruction test for TASK299."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from scripts import repackage_task299_p05_existing_artifact as t

class TestTask299RoundTrip(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            source=base/"source"
            original=source/"originals"
            original.mkdir(parents=True)
            expected=t.batch_map()["P05"]
            rows=[]
            for row in expected:
                edition=row["edition"]
                raw=b"%PDF-"+str(edition).encode()+b"X"*3500
                name=f"JOM_{edition}_2026_ORIGINAL.pdf"
                (original/name).write_bytes(raw)
                rows.append({"edition_candidate":edition,"url":row["url"],
                             "file_name":name,"bytes":len(raw),"pages":1,
                             "sha256":hashlib.sha256(raw).hexdigest(),
                             "status":"VALIDATED_ORIGINAL_IN_ARTIFACT_ONLY",
                             "request_attempts":1,"cover_edition_verified":True,
                             "custodied_in_sme":False})
            manifest={"schema":t.SOURCE_SCHEMA,"batch":"P05","github_sha":t.SOURCE_HEAD,
                      "status":"PASS_ALL_PDFS_IN_TEMP_ARTIFACT",
                      "requested_count":9,"validated_count":9,"failed_count":0,
                      "get_attempts":9,"retry_count":0,"drive_write_count":0,
                      "publication_count":0,"documents":rows}
            (source/"manifest.json").write_text(json.dumps(manifest))
            out=base/"out"
            with patch.object(t,"inspect_pdf",return_value=1),patch.object(t,"PART_BYTES",8192),patch.object(t,"MAX_BUNDLE_BYTES",40960):
                report=t.create_parts(source,out)
            self.assertEqual(report["verified_pdfs"],9)
            self.assertEqual(len(report["parts"]),5)
            reconstructed=b""
            for i,part in enumerate(report["parts"],1):
                pkg=out/"parts"/part["file"]
                self.assertEqual(t.sha256_file(pkg),part["sha256"])
                with zipfile.ZipFile(pkg) as z:
                    chunk=z.read(f"{t.BUNDLE_NAME}.part{i:02d}")
                    meta=json.loads(z.read("manifest_part.json"))
                    self.assertEqual(hashlib.sha256(chunk).hexdigest(),meta["part_sha256"])
                    reconstructed+=chunk
            self.assertEqual(hashlib.sha256(reconstructed).hexdigest(),report["bundle_sha256"])
            with zipfile.ZipFile(out/t.BUNDLE_NAME) as z:
                for record in rows:
                    pdf=z.read("originals/"+record["file_name"])
                    self.assertEqual(hashlib.sha256(pdf).hexdigest(),record["sha256"])
if __name__=="__main__":
    unittest.main()
