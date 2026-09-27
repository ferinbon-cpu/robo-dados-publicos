from __future__ import annotations

import hashlib
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from robo_dados_publicos.sources.siope_2025_metadata_inspector import (
    InspectionError, InspectionLimits, TARGET_ALIASES, dumps, inspect,
)

class MetadataInspectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.fixtures = Path(self._temporary_directory.name)
        self._build_synthetic_fixtures()

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def _zip(
        self,
        name: str,
        entries: list[tuple[str, str] | tuple[str, str, int]],
        compression: int = zipfile.ZIP_DEFLATED,
    ) -> Path:
        path = self.fixtures / name
        with zipfile.ZipFile(path, "w", compression=compression) as archive:
            for entry in entries:
                member_name, contents = entry[:2]
                if len(entry) == 2:
                    archive.writestr(member_name, contents)
                else:
                    info = zipfile.ZipInfo(member_name)
                    info.external_attr = entry[2] << 16
                    archive.writestr(info, contents)
        return path

    def _build_synthetic_fixtures(self) -> None:
        definitions = "\n".join(f"{alias}: definição sintética de {alias}" for alias in TARGET_ALIASES)
        self._zip("safe_aliases.zip", [("schema/fields.txt", definitions)])
        self._zip("without_aliases.zip", [("schema/fields.txt", "CAMPO_TESTE: definição sintética")])
        self._zip("alias_without_definition.zip", [("schema/fields.txt", "NUM_POPU\n")])
        self._zip("ambiguous_definition.zip", [
            ("a.txt", "NUM_POPU: definição sintética A"),
            ("b.txt", "NUM_POPU: definição sintética B"),
        ])
        self._zip("path_traversal.zip", [("../escape.txt", "synthetic")])
        self._zip("absolute_path.zip", [("/escape.txt", "synthetic")])
        self._zip("unexpected_executable.zip", [("payload.exe", "MZ synthetic")])
        self._zip(
            "dangerous_symlink.zip",
            [("link.txt", "../../escape", stat.S_IFLNK | 0o777)],
            compression=zipfile.ZIP_STORED,
        )
        self._zip("too_many_entries.zip", [(f"{index}.txt", "x") for index in range(4)])
        self._zip("oversized_entry.zip", [("big.txt", "x" * 64)])
        self._zip("abnormal_ratio.zip", [("bomb.txt", "0" * 10_000)])
        self._zip("misleading_extension.txt", [("schema.txt", "NUM_POPU: definição sintética")])
        (self.fixtures / "corrupt.zip").write_bytes(b"PK\x03\x04corrupt synthetic fixture")

    def assert_stop(self, fixture: str, code: str, limits: InspectionLimits = InspectionLimits()) -> None:
        with self.assertRaisesRegex(InspectionError, f"STOP_TASK_010A_{code}"):
            inspect(self.fixtures / fixture, limits)

    def test_safe_archive_hashes_lists_and_builds_synthetic_matrix(self) -> None:
        path = self.fixtures / "safe_aliases.zip"
        result = inspect(path)
        self.assertEqual(result["input"]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(result["input"]["detected_type"], "zip")
        self.assertEqual([row["field"] for row in result["semantic_matrix"]], list(TARGET_ALIASES))
        self.assertTrue(all(row["decision"] == "PROVEN" for row in result["semantic_matrix"]))
        self.assertTrue(all(row["synthetic_only"] for row in result["semantic_matrix"]))
        self.assertFalse(result["canonical_state_changed"])
        self.assertEqual(dumps(result), dumps(inspect(path)))

    def test_missing_aliases_are_not_found(self) -> None:
        rows = inspect(self.fixtures / "without_aliases.zip")["semantic_matrix"]
        self.assertTrue(all(row["decision"] == "NOT_FOUND" for row in rows))

    def test_alias_without_definition_is_partial(self) -> None:
        row = inspect(self.fixtures / "alias_without_definition.zip")["semantic_matrix"][0]
        self.assertEqual(row["decision"], "PARTIAL")

    def test_conflicting_definitions_are_ambiguous(self) -> None:
        row = inspect(self.fixtures / "ambiguous_definition.zip")["semantic_matrix"][0]
        self.assertEqual(row["decision"], "AMBIGUOUS")

    def test_rejects_traversal_absolute_active_and_symlink(self) -> None:
        cases = (("path_traversal.zip", "PATH_TRAVERSAL"), ("absolute_path.zip", "ABSOLUTE_PATH"),
                 ("unexpected_executable.zip", "ACTIVE_CONTENT_EXTENSION"), ("dangerous_symlink.zip", "SYMLINK"))
        for fixture, code in cases:
            with self.subTest(fixture=fixture): self.assert_stop(fixture, code)

    def test_enforces_count_and_size_limits(self) -> None:
        self.assert_stop("too_many_entries.zip", "ENTRY_COUNT_LIMIT", InspectionLimits(max_entries=3))
        self.assert_stop("oversized_entry.zip", "ENTRY_SIZE_LIMIT", InspectionLimits(max_entry_size=32))
        self.assert_stop("oversized_entry.zip", "TOTAL_SIZE_LIMIT", InspectionLimits(max_entry_size=128, max_total_size=32))

    def test_rejects_original_archive_before_reading_bytes(self) -> None:
        self.assert_stop("safe_aliases.zip", "ARCHIVE_SIZE_LIMIT", InspectionLimits(max_archive_size=8))

    def test_rejects_abnormal_compression_ratio(self) -> None:
        self.assert_stop("abnormal_ratio.zip", "COMPRESSION_RATIO_LIMIT", InspectionLimits(max_compression_ratio=10))

    def test_uses_signature_not_extension(self) -> None:
        self.assertEqual(inspect(self.fixtures / "misleading_extension.txt")["input"]["detected_type"], "zip")

    def test_rejects_corrupt_and_unknown_content(self) -> None:
        self.assert_stop("corrupt.zip", "CORRUPT_ARCHIVE")
        unknown = self.fixtures / "unknown.bin"
        try:
            unknown.write_bytes(b"not an archive")
            self.assert_stop("unknown.bin", "UNSUPPORTED_SIGNATURE")
        finally:
            unknown.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
