from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import sys
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("public_surface_gate", SCRIPTS / "github_public_surface_gate.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def _zip(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buffer.getvalue()


class PublicSurfaceAuditTests(unittest.TestCase):
    def test_text_artifact_secret_is_reported_without_value(self) -> None:
        token = "gh" + "p_" + ("Ab9" * 12)
        raw = _zip({"job.log": f"before\n{token}\nafter\n".encode()})
        blockers, reviews, stats = mod.scan_zip_bytes(raw, surface="fixture", resource_id="7")
        self.assertEqual([], reviews)
        self.assertEqual(1, stats["text_entries"])
        self.assertTrue(blockers)
        self.assertNotIn(token, repr(blockers))
        self.assertEqual("GITHUB_TOKEN_PREFIX", blockers[0]["detector"])

    def test_binary_artifact_entry_requires_review(self) -> None:
        raw = _zip({"output.pdf": b"%PDF-1.4\x00binary"})
        blockers, reviews, stats = mod.scan_zip_bytes(raw, surface="fixture", resource_id="8")
        self.assertEqual([], blockers)
        self.assertEqual(1, stats["opaque_entries"])
        self.assertEqual("OPAQUE_ARTIFACT_ENTRY", reviews[0]["detector"])

    def test_plain_text_without_secret_passes(self) -> None:
        raw = _zip({"result.json": b'{"status":"PASS","secret_values_exposed":false}'})
        blockers, reviews, stats = mod.scan_zip_bytes(raw, surface="fixture", resource_id="9")
        self.assertEqual([], blockers)
        self.assertEqual([], reviews)
        self.assertEqual(1, stats["text_entries"])

    def test_redirected_object_store_headers_never_include_repository_token(self) -> None:
        headers = mod.base._request_headers(include_auth=False, accept="application/vnd.github+json")
        self.assertNotIn("Authorization", headers)
        self.assertEqual("robo-dados-publicos-public-readiness-audit", headers["User-Agent"])


if __name__ == "__main__":
    unittest.main()
