from __future__ import annotations

import io
import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from robo_dados_publicos.sources import siope_cml_codec as codec


def _zip_bytes(name: str = "metadata.xml", content: bytes = b"<root/>", compression=zipfile.ZIP_STORED) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        archive.writestr(name, content)
    return output.getvalue()


def _czip_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.mkdir("images/")
        for index in range(3):
            archive.writestr(f"images/image{index}.gif", b"GIF89a synthetic")
        archive.writestr("favicon.ico", b"static ico bytes")
        archive.writestr("index.html", b"<html>static</html>")
        archive.writestr("style.css", b"body { color: black; }")
    return output.getvalue()


def _encrypt_payload(payload: bytes) -> bytes:
    """Test-only inverse of the pinned chunk/CV decoder contract."""
    key = codec.derive_metadata_key()
    cv = codec.derive_initial_iv()
    ciphertext = bytearray()
    for chunk_offset in range(0, len(payload), codec.CHUNK_SIZE):
        chunk = payload[chunk_offset : chunk_offset + codec.CHUNK_SIZE]
        complete = len(chunk) - len(chunk) % codec.BLOCK_SIZE
        for offset in range(0, complete, codec.BLOCK_SIZE):
            block = chunk[offset : offset + codec.BLOCK_SIZE]
            encrypted = codec._blowfish_ecb(key, bytes(a ^ b for a, b in zip(block, cv)))
            ciphertext.extend(encrypted)
            cv = encrypted
        remainder = chunk[complete:]
        if remainder:
            stream = codec._blowfish_ecb(key, cv)
            ciphertext.extend(a ^ b for a, b in zip(remainder, stream))
    return codec.expected_container_header() + bytes(ciphertext)


class CodecContractTests(unittest.TestCase):
    def test_deterministic_key_iv_and_header(self):
        self.assertEqual(codec.derive_metadata_key().hex(), "1ef164301c8949207c0066d3270407cae797b7c6" + "ff" * 12)
        self.assertEqual(codec.derive_initial_iv().hex(), "69fbe9f873a4758b")
        self.assertEqual(codec.expected_container_header().hex(), "442d68fb56d3e72adb7e95e0f7b003795a1d3ae15f98ca334c7a557c58277593")

    def test_short_wrong_header_and_empty_ciphertext_stop(self):
        cases = (
            (b"short", "CONTAINER_TOO_SHORT"),
            (b"x" * 33, "INVALID_HEADER"),
            (codec.expected_container_header(), "EMPTY_CIPHERTEXT"),
        )
        for data, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(codec.CodecError, code):
                codec.decode_container_bytes(data)

    def test_synthetic_cml_and_czip_containers(self):
        for extension in (".cml", ".czip"):
            with self.subTest(extension=extension):
                payload = _zip_bytes("inside.xml", b"<metadata synthetic='true'/>") if extension == ".cml" else _czip_bytes()
                decoded = codec.decode_container_bytes(_encrypt_payload(payload))
                self.assertEqual(decoded, payload)
                self.assertTrue(codec.inspect_decoded_zip(decoded, extension)["crc_valid"])

    def test_cml_is_xml_only(self):
        self.assertTrue(codec.inspect_decoded_zip(_zip_bytes(), "cml")["valid_zip"])
        with self.assertRaisesRegex(codec.CodecError, "TYPE_NOT_ALLOWED"):
            codec.inspect_decoded_zip(_zip_bytes("index.html", b"<html/>"), "cml")

    def test_czip_static_shape_passes_without_interpreting_bytes(self):
        result = codec.inspect_decoded_zip(_czip_bytes(), "czip")
        self.assertEqual(result["container_type"], "CZIP")
        self.assertEqual(len(result["entries"]), 6)

    def test_czip_rejects_active_and_unexpected_types(self):
        for name in ("active.js", "active.exe", "unexpected.xml"):
            with self.subTest(name=name), self.assertRaisesRegex(codec.CodecError, "TYPE_NOT_ALLOWED"):
                codec.inspect_decoded_zip(_zip_bytes(name, b"static"), "czip")

    def test_literal_chunk_boundaries_and_remainders(self):
        lengths = (8, 1024, 1025, 1026, 1031, 2048, 2050, 3077)
        for length in lengths:
            with self.subTest(length=length):
                payload = bytes((index * 29 + 7) % 256 for index in range(length))
                self.assertEqual(codec.decode_container_bytes(_encrypt_payload(payload)), payload)

    def test_ciphertext_corruption_no_longer_yields_valid_zip(self):
        container = bytearray(_encrypt_payload(_zip_bytes()))
        container[32] ^= 1
        decoded = codec.decode_container_bytes(bytes(container))
        with self.assertRaises(codec.CodecError):
            codec.inspect_decoded_zip(decoded, "cml")

    def test_invalid_zip_stops(self):
        with self.assertRaisesRegex(codec.CodecError, "DECODED_NOT_ZIP"):
            codec.inspect_decoded_zip(b"not a zip", "cml")

    def test_crc_invalid_stops(self):
        data = bytearray(_zip_bytes(content=b"abcdefgh"))
        content_offset = data.index(b"abcdefgh")
        data[content_offset] ^= 1
        with self.assertRaisesRegex(codec.CodecError, "CRC_INVALID"):
            codec.inspect_decoded_zip(bytes(data), "cml")

    def test_unsafe_paths_and_symlink_stop(self):
        for name, code in (("../escape.xml", "PATH_TRAVERSAL"), ("/absolute.xml", "ABSOLUTE_PATH"), ("C:\\absolute.xml", "ABSOLUTE_PATH")):
            with self.subTest(name=name), self.assertRaisesRegex(codec.CodecError, code):
                codec.inspect_decoded_zip(_zip_bytes(name), "cml")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            info = zipfile.ZipInfo("link.xml")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "target.xml")
        with self.assertRaisesRegex(codec.CodecError, "SYMLINK"):
            codec.inspect_decoded_zip(output.getvalue(), "cml")

    def test_special_file_stops(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            info = zipfile.ZipInfo("device.xml")
            info.create_system = 3
            info.external_attr = (stat.S_IFCHR | 0o600) << 16
            archive.writestr(info, b"ignored")
        with self.assertRaisesRegex(codec.CodecError, "SPECIAL_FILE"):
            codec.inspect_decoded_zip(output.getvalue(), "cml")

    def test_depth_limit(self):
        deep = _zip_bytes("a/b/c.xml")
        with self.assertRaisesRegex(codec.CodecError, "DEPTH_LIMIT"):
            codec.inspect_decoded_zip(deep, "cml", codec.ZipInspectionLimits(max_depth=2))

    def test_entry_size_total_count_and_ratio_limits(self):
        two_entries = io.BytesIO()
        with zipfile.ZipFile(two_entries, "w") as archive:
            archive.writestr("a.xml", "a")
            archive.writestr("b.xml", "b")
        with self.assertRaisesRegex(codec.CodecError, "ENTRY_COUNT"):
            codec.inspect_decoded_zip(two_entries.getvalue(), "cml", codec.ZipInspectionLimits(max_entries=1))
        with self.assertRaisesRegex(codec.CodecError, "ENTRY_SIZE"):
            codec.inspect_decoded_zip(_zip_bytes(content=b"12"), "cml", codec.ZipInspectionLimits(max_entry_size=1))
        with self.assertRaisesRegex(codec.CodecError, "TOTAL_SIZE"):
            codec.inspect_decoded_zip(two_entries.getvalue(), "cml", codec.ZipInspectionLimits(max_total_size=1))
        bomb = _zip_bytes(content=b"0" * 10_000, compression=zipfile.ZIP_DEFLATED)
        with self.assertRaisesRegex(codec.CodecError, "COMPRESSION_RATIO"):
            codec.inspect_decoded_zip(bomb, "cml", codec.ZipInspectionLimits(max_compression_ratio=2))

    def test_dtd_and_entity_are_rejected_without_parsing(self):
        for declaration in (b"<!DOCTYPE root>", b"<!ENTITY x 'y'>"):
            with self.subTest(declaration=declaration), self.assertRaisesRegex(codec.CodecError, "DTD_OR_ENTITY"):
                codec.inspect_decoded_zip(_zip_bytes(content=declaration + b"<root/>"), "cml")

    def test_outer_package_decodes_both_extensions_without_writes(self):
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w") as archive:
            archive.writestr("Metadados.cml", _encrypt_payload(_zip_bytes("Metadados.xml")))
            archive.writestr("nested/Dados.czip", _encrypt_payload(_czip_bytes()))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.zip"
            path.write_bytes(outer.getvalue())
            result = codec.decode_outer_metadata_package(path)
            self.assertEqual(result["container_count"], 2)
            self.assertEqual(result["remote_effects"], 0)
            self.assertFalse(result["canonical_state_changed"])
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_inner_preflight_rejects_before_read_or_testzip(self):
        invalid = _zip_bytes("active.js", b"alert(1)")
        with mock.patch.object(zipfile.ZipFile, "read", side_effect=AssertionError("read before preflight")), mock.patch.object(
            zipfile.ZipFile, "testzip", side_effect=AssertionError("testzip before preflight")
        ):
            with self.assertRaisesRegex(codec.CodecError, "TYPE_NOT_ALLOWED"):
                codec.inspect_decoded_zip(invalid, "czip")

    def test_outer_limits_and_preflight_before_read(self):
        def outer_bytes(names: list[str], compression=zipfile.ZIP_STORED, payload: bytes | None = None) -> bytes:
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w", compression=compression) as archive:
                for name in names:
                    archive.writestr(name, payload if payload is not None else b"x")
            return output.getvalue()

        cases = (
            (["a.cml", "b.cml"], codec.ZipInspectionLimits(max_entries=1), "ENTRY_COUNT"),
            (["a.cml", "b.cml"], codec.ZipInspectionLimits(max_total_size=1), "TOTAL_SIZE"),
            (["a/b/c.cml"], codec.ZipInspectionLimits(max_depth=2), "DEPTH_LIMIT"),
            (["a.cml"], codec.ZipInspectionLimits(max_compression_ratio=2), "COMPRESSION_RATIO"),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outer.zip"
            for names, limits, error in cases:
                payload = b"0" * 10_000 if error == "COMPRESSION_RATIO" else None
                compression = zipfile.ZIP_DEFLATED if payload else zipfile.ZIP_STORED
                path.write_bytes(outer_bytes(names, compression, payload))
                with self.subTest(error=error), mock.patch.object(
                    zipfile.ZipFile, "read", side_effect=AssertionError("read before outer preflight")
                ), self.assertRaisesRegex(codec.CodecError, error):
                    codec.decode_outer_metadata_package(path, limits)
            path.write_bytes(outer_bytes(["a.cml"]))
            with self.assertRaisesRegex(codec.CodecError, "OUTER_ARCHIVE_SIZE_LIMIT"):
                codec.decode_outer_metadata_package(path, codec.ZipInspectionLimits(max_archive_size=1))

    def test_contract_drift_fails_closed(self):
        contract = json.loads(codec.CONTRACT_PATH.read_text(encoding="utf-8"))
        contract["schema"] = "DRIFT"
        with mock.patch.object(codec, "CONTRACT_PATH") as path:
            path.read_text.return_value = json.dumps(contract)
            with self.assertRaisesRegex(codec.CodecError, "SCHEMA_DRIFT"):
                codec.derive_metadata_key()
