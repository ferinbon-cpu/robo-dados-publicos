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
                payload = _zip_bytes("inside.xml", b"<metadata synthetic='true'/>")
                decoded = codec.decode_container_bytes(_encrypt_payload(payload))
                self.assertEqual(decoded, payload)
                self.assertTrue(codec.inspect_decoded_zip(decoded)["crc_valid"])

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
            codec.inspect_decoded_zip(decoded)

    def test_invalid_zip_stops(self):
        with self.assertRaisesRegex(codec.CodecError, "DECODED_NOT_ZIP"):
            codec.inspect_decoded_zip(b"not a zip")

    def test_crc_invalid_stops(self):
        data = bytearray(_zip_bytes(content=b"abcdefgh"))
        content_offset = data.index(b"abcdefgh")
        data[content_offset] ^= 1
        with self.assertRaisesRegex(codec.CodecError, "CRC_INVALID"):
            codec.inspect_decoded_zip(bytes(data))

    def test_unsafe_paths_and_symlink_stop(self):
        for name, code in (("../escape.xml", "PATH_TRAVERSAL"), ("/absolute.xml", "ABSOLUTE_PATH"), ("C:\\absolute.xml", "ABSOLUTE_PATH")):
            with self.subTest(name=name), self.assertRaisesRegex(codec.CodecError, code):
                codec.inspect_decoded_zip(_zip_bytes(name))
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            info = zipfile.ZipInfo("link.xml")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "target.xml")
        with self.assertRaisesRegex(codec.CodecError, "SYMLINK"):
            codec.inspect_decoded_zip(output.getvalue())

    def test_entry_size_total_count_and_ratio_limits(self):
        two_entries = io.BytesIO()
        with zipfile.ZipFile(two_entries, "w") as archive:
            archive.writestr("a.xml", "a")
            archive.writestr("b.xml", "b")
        with self.assertRaisesRegex(codec.CodecError, "ENTRY_COUNT"):
            codec.inspect_decoded_zip(two_entries.getvalue(), codec.ZipInspectionLimits(max_entries=1))
        with self.assertRaisesRegex(codec.CodecError, "ENTRY_SIZE"):
            codec.inspect_decoded_zip(_zip_bytes(content=b"12"), codec.ZipInspectionLimits(max_entry_size=1))
        with self.assertRaisesRegex(codec.CodecError, "TOTAL_SIZE"):
            codec.inspect_decoded_zip(two_entries.getvalue(), codec.ZipInspectionLimits(max_total_size=1))
        bomb = _zip_bytes(content=b"0" * 10_000, compression=zipfile.ZIP_DEFLATED)
        with self.assertRaisesRegex(codec.CodecError, "COMPRESSION_RATIO"):
            codec.inspect_decoded_zip(bomb, codec.ZipInspectionLimits(max_compression_ratio=2))

    def test_dtd_and_entity_are_rejected_without_parsing(self):
        for declaration in (b"<!DOCTYPE root>", b"<!ENTITY x 'y'>"):
            with self.subTest(declaration=declaration), self.assertRaisesRegex(codec.CodecError, "DTD_OR_ENTITY"):
                codec.inspect_decoded_zip(_zip_bytes(content=declaration + b"<root/>"))

    def test_outer_package_decodes_both_extensions_without_writes(self):
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w") as archive:
            archive.writestr("Metadados.cml", _encrypt_payload(_zip_bytes("Metadados.xml")))
            archive.writestr("nested/Dados.czip", _encrypt_payload(_zip_bytes("Dados.xml")))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.zip"
            path.write_bytes(outer.getvalue())
            result = codec.decode_outer_metadata_package(path)
            self.assertEqual(result["container_count"], 2)
            self.assertEqual(result["remote_effects"], 0)
            self.assertFalse(result["canonical_state_changed"])
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_contract_drift_fails_closed(self):
        contract = json.loads(codec.CONTRACT_PATH.read_text(encoding="utf-8"))
        contract["schema"] = "DRIFT"
        with mock.patch.object(codec, "CONTRACT_PATH") as path:
            path.read_text.return_value = json.dumps(contract)
            with self.assertRaisesRegex(codec.CodecError, "SCHEMA_DRIFT"):
                codec.derive_metadata_key()
