import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from robo_dados_publicos.sources.inventory import SourceSpec, load_source_inventory
from robo_dados_publicos.sources.collector import SourceCollector
from robo_dados_publicos.state.registry import StateRegistry


PAYLOAD = b"col_a,col_b\n1,2\n"
ETAG = '"source-v1"'


class CsvHandler(BaseHTTPRequestHandler):
    content_type = "text/csv; charset=utf-8"
    def do_GET(self):
        if self.headers.get("If-None-Match") == ETAG:
            self.send_response(304)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", self.content_type)
        self.send_header("ETag", ETAG)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)
    def log_message(self, *args):
        pass


class MemoryDrive:
    def __init__(self):
        self.seq = 0
        self.items = []
        self.bytes = {}
    def put(self, local_path, remote_name, parent_id=None, mime_type="application/octet-stream"):
        self.seq += 1
        fid = f"F{self.seq}"
        self.items.append({"id": fid, "name": remote_name, "parent": parent_id, "mimeType": mime_type})
        self.bytes[fid] = Path(local_path).read_bytes()
        return {"id": fid, "name": remote_name}


class CountingHTTP:
    def __init__(self):
        self.calls = 0
    def download(self, *args, **kwargs):
        self.calls += 1
        raise AssertionError("network should not be called in dry-run")


class TestM4ESources(unittest.TestCase):
    def test_inventory_contract_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sources.json"
            p.write_text(json.dumps({"version": 1, "sources": [
                {"source_id": "S1", "url": "https://example.org/a.csv", "logical_key": "a", "file_name": "a.csv"},
                {"source_id": "S1", "url": "https://example.org/b.csv", "logical_key": "b", "file_name": "b.csv"},
            ]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "DUPLICATE_IDS"):
                load_source_inventory(p)

    def test_inventory_requires_https(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sources.json"
            p.write_text(json.dumps({"version": 1, "sources": [
                {"source_id": "S1", "url": "http://example.org/a.csv", "logical_key": "a", "file_name": "a.csv"}
            ]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "HTTPS_REQUIRED"):
                load_source_inventory(p)

    def test_inventory_rejects_bad_immutable_contract(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sources.json"
            p.write_text(json.dumps({"version": 1, "sources": [{
                "source_id": "S1",
                "url": "https://example.org/a.pdf",
                "logical_key": "a",
                "file_name": "a.pdf",
                "expected_sha256": "not-a-sha",
                "expected_bytes": 0,
            }]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "BAD_SHA256"):
                load_source_inventory(p)

    def test_dry_run_has_no_network_or_writes(self):
        spec = SourceSpec("S1", "https://example.org/a.csv", "a", "a.csv", True, ("text/csv",))
        from robo_dados_publicos.sources.inventory import SourceInventory
        inv = SourceInventory(1, (spec,))
        drive = MemoryDrive(); http = CountingHTTP()
        with tempfile.TemporaryDirectory() as td, StateRegistry(Path(td)/"state.sqlite") as st:
            out = SourceCollector(drive, "BRONZE", "Q", http=http).collect_inventory(inv, st, dry_run=True)
        self.assertEqual("DRY_RUN", out["status"])
        self.assertEqual(0, http.calls)
        self.assertEqual([], drive.items)

    def test_new_payload_goes_to_immutable_bronze_then_304(self):
        server = HTTPServer(("127.0.0.1", 0), CsvHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/a.csv"
            spec = SourceSpec("S1", url, "a", "a.csv", True, ("text/csv",))
            drive = MemoryDrive()
            with tempfile.TemporaryDirectory() as td, StateRegistry(Path(td)/"state.sqlite") as st:
                collector = SourceCollector(drive, "BRONZE", "Q")
                first = collector.collect_one(spec, st)
                second = collector.collect_one(spec, st)
                state = st.get_source_state("S1")
                files = list(st.con.execute("SELECT sha256,logical_key,file_name,status FROM files"))
            self.assertEqual("DOWNLOADED_NEW", first["status"])
            self.assertEqual("BRONZE", drive.items[0]["parent"])
            self.assertIn(first["sha256"][:12], drive.items[0]["name"])
            self.assertEqual("NOT_MODIFIED", second["status"])
            self.assertEqual(1, len(drive.items))
            self.assertEqual("NOT_MODIFIED", state["last_status"])
            self.assertEqual(1, len(files))
            self.assertEqual("BRONZE_REMOTE", files[0][3])
        finally:
            server.shutdown(); server.server_close()

    def test_unexpected_content_type_is_quarantined_and_stops(self):
        class HtmlHandler(CsvHandler):
            content_type = "text/html"
        server = HTTPServer(("127.0.0.1", 0), HtmlHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/a.csv"
            spec = SourceSpec("S1", url, "a", "a.csv", True, ("text/csv",))
            from robo_dados_publicos.sources.inventory import SourceInventory
            drive = MemoryDrive()
            with tempfile.TemporaryDirectory() as td, StateRegistry(Path(td)/"state.sqlite") as st:
                out = SourceCollector(drive, "BRONZE", "Q").collect_inventory(SourceInventory(1,(spec,)), st)
                files = list(st.con.execute("SELECT * FROM files"))
            self.assertEqual("STOP_SOURCE_COLLECTION", out["status"])
            self.assertEqual("STOP_SOURCE_CONTRACT", out["results"][0]["status"])
            self.assertEqual("Q", drive.items[0]["parent"])
            self.assertEqual([], files)
        finally:
            server.shutdown(); server.server_close()

    def test_immutable_artifact_mismatch_is_quarantined_and_stops(self):
        server = HTTPServer(("127.0.0.1", 0), CsvHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/a.csv"
            spec = SourceSpec(
                "S1", url, "a", "a.csv", True, ("text/csv",),
                expected_sha256="0" * 64,
                expected_bytes=len(PAYLOAD) + 1,
            )
            from robo_dados_publicos.sources.inventory import SourceInventory
            drive = MemoryDrive()
            with tempfile.TemporaryDirectory() as td, StateRegistry(Path(td)/"state.sqlite") as st:
                out = SourceCollector(drive, "BRONZE", "Q").collect_inventory(SourceInventory(1, (spec,)), st)
                files = list(st.con.execute("SELECT * FROM files"))
            result = out["results"][0]
            self.assertEqual("STOP_SOURCE_COLLECTION", out["status"])
            self.assertEqual("IMMUTABLE_ARTIFACT_MISMATCH", result["reason"])
            self.assertEqual({"sha256", "bytes"}, set(result["mismatches"]))
            self.assertEqual("Q", drive.items[0]["parent"])
            self.assertEqual([], files)
        finally:
            server.shutdown(); server.server_close()

    def test_state_source_registry_roundtrip(self):
        with tempfile.TemporaryDirectory() as td, StateRegistry(Path(td)/"state.sqlite") as st:
            st.upsert_source_state("S1", "https://example.org/a.csv", etag='"e"', last_sha256="abc", last_status="DOWNLOADED_NEW", remote_file_id="F1")
            got = st.get_source_state("S1")
            self.assertEqual('"e"', got["etag"])
            self.assertEqual("abc", got["last_sha256"])
            self.assertEqual("F1", got["remote_file_id"])
            self.assertEqual(1, len(st.list_source_states()))


if __name__ == "__main__":
    unittest.main()
