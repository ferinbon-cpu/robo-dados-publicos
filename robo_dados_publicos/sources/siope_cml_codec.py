"""Literal, offline decoder for the pinned SIOPE 2025 CML/CZIP framing."""

from __future__ import annotations

import hashlib
import io
import json
import stat
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

CONTRACT_PATH = Path(__file__).parents[2] / "config" / "siope_2025_cml_czip_codec_contract.v1.json"
EXPECTED_CONTRACT_SCHEMA = "SIOPE_2025_CML_CZIP_CODEC_CONTRACT_V1"
CHUNK_SIZE = 1025
HEADER_SIZE = 32
BLOCK_SIZE = 8
XML_SUFFIX = ".xml"
_FORBIDDEN_XML_MARKERS = (b"<!doctype", b"<!entity")


class CodecError(RuntimeError):
    """A deterministic, fail-closed codec or archive validation STOP."""


@dataclass(frozen=True)
class ZipInspectionLimits:
    max_entries: int = 256
    max_entry_size: int = 16 * 1024 * 1024
    max_total_size: int = 64 * 1024 * 1024
    max_depth: int = 8
    max_compression_ratio: float = 100.0

    def __post_init__(self) -> None:
        if min(self.max_entries, self.max_entry_size, self.max_total_size, self.max_depth) <= 0:
            raise ValueError("ZIP inspection limits must be positive")
        if self.max_compression_ratio < 1:
            raise ValueError("compression ratio must be at least 1")


def _stop(code: str, cause: BaseException | None = None) -> None:
    error = CodecError(f"STOP_TASK_010J_{code}")
    if cause is None:
        raise error
    raise error from cause


def _contract() -> dict:
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _stop("CONTRACT_UNREADABLE", exc)
    if contract.get("schema") != EXPECTED_CONTRACT_SCHEMA:
        _stop("CONTRACT_SCHEMA_DRIFT")
    return contract


def _blowfish_ecb(key: bytes, block: bytes, *, decrypt: bool = False) -> bytes:
    context = Cipher(algorithms.Blowfish(key), modes.ECB()).decryptor() if decrypt else Cipher(algorithms.Blowfish(key), modes.ECB()).encryptor()
    return context.update(block) + context.finalize()


def derive_metadata_key() -> bytes:
    """Derive the exact SHA-1 plus FF-padded 256-bit key pinned by the contract."""
    codec = _contract()["codec"]
    text = codec["constant_text"] + codec["metadata_passphrase"]
    encoded = text.encode("utf-16le")[: len(text)]
    if encoded.hex() != codec["hash_input_hex"]:
        _stop("CONTRACT_HASH_INPUT_DRIFT")
    digest = hashlib.sha1(encoded).digest()
    key = digest + b"\xff" * (codec["key_bits"] // 8 - len(digest))
    if digest.hex() != codec["sha1_hex"] or key.hex() != codec["key_hex"]:
        _stop("CONTRACT_KEY_DRIFT")
    return key


def derive_initial_iv() -> bytes:
    """Apply the pinned DCP1COMPAT implicit-IV rule."""
    codec = _contract()["codec"]
    key = derive_metadata_key()
    seed = bytes.fromhex(codec["implicit_iv_seed_hex"])
    iv = _blowfish_ecb(key, seed)
    if iv.hex() != codec["initial_iv_hex"]:
        _stop("CONTRACT_IV_DRIFT")
    return iv


def expected_container_header() -> bytes:
    """Reproduce and verify the pinned 32-byte encrypted-key header."""
    contract = _contract()
    key = derive_metadata_key()
    cv = derive_initial_iv()
    output = bytearray()
    for offset in range(0, len(key), BLOCK_SIZE):
        block = bytes(a ^ b for a, b in zip(key[offset : offset + BLOCK_SIZE], cv))
        cv = _blowfish_ecb(key, block)
        output.extend(cv)
    expected = bytes.fromhex(contract["container_framing"]["header_hex"])
    if bytes(output) != expected:
        _stop("CONTRACT_HEADER_DRIFT")
    return expected


def validate_container_header(data: bytes) -> None:
    """Fail closed unless *data* has the exact pinned container header and payload."""
    if len(data) < HEADER_SIZE:
        _stop("CONTAINER_TOO_SHORT")
    if data[:HEADER_SIZE] != expected_container_header():
        _stop("INVALID_HEADER")
    if len(data) == HEADER_SIZE:
        _stop("EMPTY_CIPHERTEXT")


def decode_container_bytes(data: bytes) -> bytes:
    """Decode chunks literally, carrying only the last complete ciphertext block."""
    validate_container_header(data)
    ciphertext = memoryview(data)[HEADER_SIZE:]
    key = derive_metadata_key()
    cv = derive_initial_iv()
    plaintext = bytearray()
    for chunk_offset in range(0, len(ciphertext), CHUNK_SIZE):
        chunk = ciphertext[chunk_offset : chunk_offset + CHUNK_SIZE]
        complete = len(chunk) - len(chunk) % BLOCK_SIZE
        for offset in range(0, complete, BLOCK_SIZE):
            encrypted_block = bytes(chunk[offset : offset + BLOCK_SIZE])
            decrypted = _blowfish_ecb(key, encrypted_block, decrypt=True)
            plaintext.extend(a ^ b for a, b in zip(decrypted, cv))
            cv = encrypted_block
        remainder = bytes(chunk[complete:])
        if remainder:
            stream = _blowfish_ecb(key, cv)
            plaintext.extend(a ^ b for a, b in zip(remainder, stream))
    return bytes(plaintext)


def _safe_zip_path(raw_name: str, limits: ZipInspectionLimits) -> PurePosixPath:
    path = PurePosixPath(raw_name.replace("\\", "/"))
    windows_path = PureWindowsPath(raw_name)
    if not raw_name or "\x00" in raw_name:
        _stop("ZIP_INVALID_PATH")
    if path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        _stop("ZIP_ABSOLUTE_PATH")
    if any(part in {"", ".", ".."} for part in path.parts):
        _stop("ZIP_PATH_TRAVERSAL")
    if len(path.parts) > limits.max_depth:
        _stop("ZIP_DEPTH_LIMIT")
    return path


def inspect_decoded_zip(data: bytes, limits: ZipInspectionLimits = ZipInspectionLimits()) -> dict:
    """Validate a decoded ZIP, CRCs and inert XML bytes without extracting anything."""
    if not data.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        _stop("DECODED_NOT_ZIP")
    entries: list[dict] = []
    total_size = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) > limits.max_entries:
                _stop("ZIP_ENTRY_COUNT_LIMIT")
            bad_crc = archive.testzip()
            if bad_crc is not None:
                _stop("ZIP_CRC_INVALID")
            for info in infos:
                path = _safe_zip_path(info.filename, limits)
                if stat.S_ISLNK(info.external_attr >> 16):
                    _stop("ZIP_SYMLINK")
                if info.is_dir():
                    continue
                if path.suffix.lower() != XML_SUFFIX:
                    _stop("ZIP_NON_XML_ENTRY")
                if info.file_size > limits.max_entry_size:
                    _stop("ZIP_ENTRY_SIZE_LIMIT")
                total_size += info.file_size
                if total_size > limits.max_total_size:
                    _stop("ZIP_TOTAL_SIZE_LIMIT")
                if info.file_size / max(info.compress_size, 1) > limits.max_compression_ratio:
                    _stop("ZIP_COMPRESSION_RATIO_LIMIT")
                content = archive.read(info)
                lowered = content.lower()
                if any(marker in lowered for marker in _FORBIDDEN_XML_MARKERS):
                    _stop("XML_DTD_OR_ENTITY_FORBIDDEN")
                entries.append({
                    "path": path.as_posix(),
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "sha256": hashlib.sha256(content).hexdigest(),
                })
    except CodecError:
        raise
    except (OSError, RuntimeError, NotImplementedError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        _stop("ZIP_INVALID_OR_CORRUPT", exc)
    entries.sort(key=lambda item: item["path"])
    return {"valid_zip": True, "crc_valid": True, "limits": asdict(limits), "entries": entries}


def decode_outer_metadata_package(path: Path) -> dict:
    """Read one explicit local outer ZIP and inspect all CML/CZIP entries offline."""
    try:
        package = path.read_bytes()
    except OSError as exc:
        _stop("OUTER_PACKAGE_UNREADABLE", exc)
    results: list[dict] = []
    try:
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            for info in archive.infolist():
                safe_path = _safe_zip_path(info.filename, ZipInspectionLimits())
                if info.is_dir():
                    continue
                if stat.S_ISLNK(info.external_attr >> 16):
                    _stop("OUTER_ZIP_SYMLINK")
                if safe_path.suffix.lower() not in {".cml", ".czip"}:
                    _stop("OUTER_ZIP_UNEXPECTED_ENTRY")
                container = archive.read(info)
                decoded = decode_container_bytes(container)
                inspection = inspect_decoded_zip(decoded)
                results.append({"container": safe_path.as_posix(), "decoded": inspection})
    except CodecError:
        raise
    except (OSError, RuntimeError, NotImplementedError, zipfile.BadZipFile) as exc:
        _stop("OUTER_PACKAGE_INVALID", exc)
    results.sort(key=lambda item: item["container"])
    return {
        "schema": "SIOPE_2025_CML_CZIP_OFFLINE_INSPECTION_V1",
        "status": "OFFLINE_INSPECTION_NO_SEMANTIC_PROMOTION",
        "input": {"name": path.name, "size": len(package), "sha256": hashlib.sha256(package).hexdigest()},
        "container_count": len(results),
        "containers": results,
        "canonical_state_changed": False,
        "remote_effects": 0,
    }
