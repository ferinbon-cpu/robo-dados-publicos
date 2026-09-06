import csv
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.task194_censo_turma_live_gate import (
    Task194Stop,
    derive_sanitized_aggregate,
    exact_auth_comment,
)


def _synthetic_bundle(root: Path, *, wrong_school_count: bool = False):
    codes = [f"35{i:06d}" for i in range(1, 70)]
    ai40 = codes[:40]
    ei29 = codes[40:]

    escola_rows = []
    active_codes = codes[:-1] if wrong_school_count else codes
    for code in active_codes:
        escola_rows.append({
            "CO_ENTIDADE": code,
            "CO_MUNICIPIO": "3526902",
            "TP_DEPENDENCIA": "3",
            "TP_SITUACAO_FUNCIONAMENTO": "1",
        })
    escola_rows.append({
        "CO_ENTIDADE": "99999999",
        "CO_MUNICIPIO": "3550308",
        "TP_DEPENDENCIA": "3",
        "TP_SITUACAO_FUNCIONAMENTO": "1",
    })

    turma_rows = []
    for code in ai40:
        turma_rows.append({"CO_ENTIDADE": code, "QT_TUR_BAS": "10"})
    for idx, code in enumerate(ei29):
        turma_rows.append({"CO_ENTIDADE": code, "QT_TUR_BAS": "14" if idx == len(ei29) - 1 else "10"})

    def csv_bytes(rows, fields):
        sio = io.StringIO()
        writer = csv.DictWriter(sio, fieldnames=fields, delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return sio.getvalue().encode("latin-1")

    escola_bytes = csv_bytes(
        escola_rows,
        ["CO_ENTIDADE", "CO_MUNICIPIO", "TP_DEPENDENCIA", "TP_SITUACAO_FUNCIONAMENTO"],
    )
    turma_bytes = csv_bytes(turma_rows, ["CO_ENTIDADE", "QT_TUR_BAS"])
    turma_md5 = hashlib.md5(turma_bytes).hexdigest().upper()
    manifest = f"{turma_md5}  Tabela_Turma_2025_V2.csv\n".encode("latin-1")

    package = root / "synthetic.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("dados/Tabela_Escola_2025_V2.csv", escola_bytes)
        zf.writestr("dados/Tabela_Turma_2025_V2.csv", turma_bytes)
        zf.writestr("md5_microdados_ed_basica_2025.txt", manifest)

    seed = root / "ai40.csv"
    with seed.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["codigo_inep"])
        writer.writeheader()
        for code in ai40:
            writer.writerow({"codigo_inep": code})
    return package, seed, turma_md5


class TestTask194CensoTurmaLiveGate(unittest.TestCase):
    def test_exact_authorization_comment_is_pinned(self):
        sha = "a" * 40
        self.assertEqual(
            exact_auth_comment(sha),
            (
                "TASK194_CENSO_TURMA_2025_LIVE_AUTHORIZED "
                f"main={sha} issue=598 max_http_attempts=3 raw_persist=0"
            ),
        )

    def test_synthetic_bundle_closes_exact_network_class_count(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package, seed, md5 = _synthetic_bundle(root)
            result = derive_sanitized_aggregate(
                package,
                expected_turma_md5=md5,
                ai40_seed_path=seed,
            )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["scope"]["active_school_count"], 69)
        self.assertEqual(result["class_count"]["ai40_school_count"], 40)
        self.assertEqual(result["class_count"]["ei29_school_count"], 29)
        self.assertEqual(result["class_count"]["ai40_class_count"], 400)
        self.assertEqual(result["class_count"]["ei29_class_count"], 294)
        self.assertEqual(result["class_count"]["network_value"], 694)
        self.assertEqual(result["class_count"]["turma_rows_for_active_schools"], 69)
        self.assertTrue(result["source"]["turma_md5_verified"])
        self.assertTrue(result["guards"]["class_count_is_sum_qt_tur_bas_not_row_count"])
        self.assertFalse(result["guards"]["raw_bytes_persisted"])

    def test_md5_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package, seed, _ = _synthetic_bundle(root)
            with self.assertRaisesRegex(Task194Stop, "TASK194_TURMA_MD5_MISMATCH"):
                derive_sanitized_aggregate(
                    package,
                    expected_turma_md5="0" * 32,
                    ai40_seed_path=seed,
                )

    def test_wrong_active_school_count_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package, seed, md5 = _synthetic_bundle(root, wrong_school_count=True)
            with self.assertRaisesRegex(Task194Stop, "TASK194_ACTIVE_SCHOOL_COUNT"):
                derive_sanitized_aggregate(
                    package,
                    expected_turma_md5=md5,
                    ai40_seed_path=seed,
                )

    def test_ei29_reconciliation_fails_if_subtotal_drifts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package, seed, md5 = _synthetic_bundle(root)
            # Rebuild the ZIP changing one EI-only school from 10 to 11 classes.
            with zipfile.ZipFile(package, "r") as source:
                escola = source.read("dados/Tabela_Escola_2025_V2.csv")
                turma = source.read("dados/Tabela_Turma_2025_V2.csv").decode("latin-1")
            turma = turma.replace("35000041;10\n", "35000041;11\n")
            turma_bytes = turma.encode("latin-1")
            drift_md5 = hashlib.md5(turma_bytes).hexdigest().upper()
            with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("dados/Tabela_Escola_2025_V2.csv", escola)
                zf.writestr("dados/Tabela_Turma_2025_V2.csv", turma_bytes)
                zf.writestr(
                    "md5_microdados_ed_basica_2025.txt",
                    f"{drift_md5}  Tabela_Turma_2025_V2.csv\n".encode("latin-1"),
                )
            with self.assertRaisesRegex(Task194Stop, "TASK194_EI29_CLASS_RECONCILIATION"):
                derive_sanitized_aggregate(
                    package,
                    expected_turma_md5=drift_md5,
                    ai40_seed_path=seed,
                )


if __name__ == "__main__":
    unittest.main()
