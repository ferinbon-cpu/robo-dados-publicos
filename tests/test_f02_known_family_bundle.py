from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from robo_dados_publicos.manual_ingest.f02_known_family_bundle import (
    F02KnownFamilyBundleStop,
    load_json,
    run_known_family_bundle,
    validate_adapter_contract,
    validate_batch_manifest,
    validate_controller_alignment,
    validate_gate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "config/f02_known_family_bundle_adapter.v1.json"

RREO_APR = """
MUNICIPIO DE LIMEIRA
Relatorio Resumido da Execucao Orcamentaria
Demonstrativo das Receitas e Despesas com Manutencao e Desenvolvimento do Ensino - MDE
Periodo de Referencia: JANEIRO a ABRIL 2026 / BIMESTRE: MARCO-ABRIL
RREO - ANEXO 8 (LDB, art.72)
3 - TOTAL DA RECEITA RESULTANTE DE IMPOSTOS 1.395.706.204,43 477.974.870,08
4 - TOTAL DESTINADO AO FUNDEB-20% 152.655.663,02 56.621.833,68
25% DE ((1.1) 196.270.888,07 62.871.883,83
6 - TOTAL DAS RECEITAS DO FUNDEB RECEBIDAS 204.310.244,38 70.620.568,12
9 - TOTAL DOS RECURSOS DO FUNDEB DISPONIVEIS PARA UTILIZACAO (6 + 8) 71.668.089,20
11- TOTAL DAS DESPESAS CUSTEADAS C/RECURSOS DO FUNDEB
RECEBIDAS NO EXERCICIO 129.124.321,63 62.841.461,94 43.847.432,77
12- Total das Despesas do FUNDEB com Profissionais da
Educacao Basica 128.900.343,54 62.617.483,85 43.623.454,68
15- Minimo de 70% do FUNDEB na Remuneracao dos Profissionais da Educacao Basica 49.434.397,68 62.617.483,85 62.617.483,85 88,67
29- APLICACAO EM MDE SOBRE A RECEITA RESULTANTE DE IMPOSTOS 119.493.717,52 115.982.840,60 24,27
"""

FUNDEB_APR = """
Prefeitura Municipal de Limeira
APLICACAO COM RECURSOS DO FUNDEB
22/05/2026 POSICAO EM 30/04/2026 Pagina 1
RECEITA DO FUNDEB RETENCOES AO FUNDEB
Principal (I) 198.489.969,37 69.842.340,65 152.259.900,22 56.621.833,48
TOTAL (I+II+III+IV+V+VI+VII+VIII+IX+X) 204.319.468,70 70.662.083,95 69.842.340,65 56.621.833,48
APLICACAO MINIMA - PROFISSIONAIS DA EDUCACAO BASICA
TOTAL  (min. 90%)** 129.124.321,63 182,73 62.841.461,94 88,93 43.847.432,77 62,05
PROFISSIONAIS DA EDUCACAO BASICA* - exceto
Complementacao da Uniao VAAR (min. 70%) 128.900.343,54 182,42 62.617.483,85 88,62 43.623.454,68 61,74
"""

MDE_APR = """
Prefeitura Municipal de Limeira
APLICACAO DOS RECURSOS PROPRIOS EM ENSINO - POR DATA
22/05/2026 POSICAO EM 30/04/2026 Pagina 1
RECEITA DE IMPOSTOS APLICACAO MINIMA CONSTITUCIONAL
Total 1.393.727.390,62 477.974.870,08
Retencoes ao FUNDEB 152.259.900,22 56.621.833,48
DESPESAS PROPRIAS EM EDUCACAO
DESPESAS TOTAIS
TOTAL 192.993.733,99 40,38 111.043.318,30 23,23 99.563.903,63 20,83
DESPESAS LIQUIDAS
Ensino Fundamental 78.323.066,84 16,39 32.754.512,39 6,85 24.995.305,53 5,23
TOTAL 192.796.668,89 40,34 110.846.253,20 23,19 86.592.437,82 18,12
"""

FUNDEB_MAY = """
Prefeitura Municipal de Limeira
APLICACAO COM RECURSOS DO FUNDEB
22/06/2026 POSICAO EM 31/05/2026 Pagina 1
RECEITA DO FUNDEB RETENCOES AO FUNDEB
Principal (I) 193.564.450,07 81.329.560,61 151.546.735,85 69.018.540,87
TOTAL (I+II+III+IV+V+VI+VII+VIII+IX+X) 202.418.930,44 85.705.568,77 81.329.560,61 69.018.540,87
PROFISSIONAIS DA EDUCACAO BASICA
DESPESAS LIQUIDAS
TOTAL ** 135.614.525,38 158,23 83.352.004,79 97,25 64.033.238,78 74,71
PROFISSIONAIS DA EDUCACAO BASICA* - exceto Complementacao da Uniao VAAR 135.390.547,29 157,97 83.128.026,70 96,99 63.809.260,69 74,45
"""

MDE_MAY = """
Prefeitura Municipal de Limeira
APLICACAO DOS RECURSOS PROPRIOS EM ENSINO - POR DATA
23/06/2026 POSICAO EM 31/05/2026 Pagina 1
RECEITA DE IMPOSTOS APLICACAO MINIMA CONSTITUCIONAL
Total 1.389.542.306,44 586.706.702,84
Retencoes ao FUNDEB 151.546.735,85 69.018.540,87
DESPESAS PROPRIAS EM EDUCACAO
DESPESAS TOTAIS
TOTAL * 207.464.562,74 35,36 138.465.313,16 23,60 126.809.299,88 21,61
DESPESAS LIQUIDAS
TOTAL 207.244.381,02 35,32 138.245.131,44 23,56 121.603.816,07 20,73
"""


def effects_false():
    return {key: False for key in (
        "bronze_write", "silver_write", "gold_write", "serving", "publication",
        "site", "overwrite", "delete", "move", "schedule", "recurrence",
    )}


def source(source_id, family, payload, path):
    return {
        "source_id": source_id,
        "family": family,
        "role": "TEST_KNOWN_FAMILY",
        "drive_file_id": "drive-" + source_id,
        "expected_sha256": hashlib.sha256(payload).hexdigest(),
        "expected_bytes": len(payload),
        "expected_pages": 1,
        "snapshot_path": path,
    }


class F02KnownFamilyBundleTests(unittest.TestCase):
    def setUp(self):
        self.adapter = load_json(ADAPTER)

    def _write_bundle(self, tmp, kind, period_end, texts):
        rel_dir = Path(tmp.name).relative_to(ROOT)
        sources = []
        text_by_payload = {}
        families = ["FUNDEB_LOCAL", "MDE_25_LOCAL"] if kind == "LOCAL_ONLY" else [
            "RREO_MDE", "FUNDEB_LOCAL", "MDE_25_LOCAL"
        ]
        for i, (family, text) in enumerate(zip(families, texts), start=1):
            payload = f"payload-{kind}-{period_end}-{i}".encode()
            filename = f"{family.lower()}_{i}.pdf"
            file_path = Path(tmp.name) / filename
            file_path.write_bytes(payload)
            sources.append(source(f"S{i}", family, payload, str(rel_dir / filename)))
            text_by_payload[payload] = text
        manifest = {
            "schema": "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1",
            "mode": "MANUAL_SUPERVISED_INGEST",
            "batch_id": f"TEST_{kind}_{period_end}",
            "batch_kind": kind,
            "reference_period": {"start": "2026-01-01", "end": period_end},
            "sources": sources,
            "remote_effects_authorized": effects_false(),
        }
        return manifest, text_by_payload

    def _run(self, manifest, text_by_payload):
        def inspect(payload):
            return {
                "pages": 1,
                "text_pages": 1,
                "text_chars": len(text_by_payload[payload]),
                "has_text_layer": True,
                "text": text_by_payload[payload],
            }
        with patch("robo_dados_publicos.manual_ingest.mde_fundeb.inspect_f02_pdf", side_effect=inspect):
            return run_known_family_bundle(self.adapter, manifest, root=ROOT)

    def test_adapter_preserves_individual_supervised_maturity(self):
        validated = validate_adapter_contract(self.adapter)
        self.assertEqual(
            validated["controller_alignment"]["bundle_execution_maturity"],
            "EXECUTION_READY_BOUNDED_MANUAL_SUPERVISED",
        )
        self.assertEqual(
            validated["controller_alignment"]["individual_family_maturity_remains"],
            "ROUTING_ONLY_SUPERVISED_EXECUTION",
        )

    def test_same_code_runs_rreo_aligned_and_local_only_manifests(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td1, tempfile.TemporaryDirectory(dir=ROOT) as td2:
            m1, t1 = self._write_bundle(type("T", (), {"name": td1})(), "RREO_ALIGNED", "2026-04-30", [RREO_APR, FUNDEB_APR, MDE_APR])
            m2, t2 = self._write_bundle(type("T", (), {"name": td2})(), "LOCAL_ONLY", "2026-05-31", [FUNDEB_MAY, MDE_MAY])
            r1, x1 = self._run(m1, t1)
            r2, x2 = self._run(m2, t2)
        self.assertEqual(r1["batch_kind"], "RREO_ALIGNED")
        self.assertTrue(r1["authority"]["official_mde_claim_authorized"])
        self.assertFalse(r1["authority"]["annual_compliance_claim_authorized"])
        self.assertEqual(r2["batch_kind"], "LOCAL_ONLY")
        self.assertFalse(r2["authority"]["official_mde_claim_authorized"])
        self.assertEqual(r2["normalized"][0]["metrics"]["fundeb_professionals_liquidated_percent_local"], "96.99")
        self.assertEqual(x1["remote_effects"], 0)
        self.assertEqual(x2["remote_effects"], 0)
        self.assertNotEqual(r1["content_sha256"], r2["content_sha256"])

    def test_manifest_can_change_period_without_code_change(self):
        rreo_jun = RREO_APR.replace("ABRIL 2026 / BIMESTRE: MARCO-ABRIL", "JUNHO 2026 / BIMESTRE: MAIO-JUNHO")
        fundeb_jun = FUNDEB_APR.replace("30/04/2026", "30/06/2026")
        mde_jun = MDE_APR.replace("30/04/2026", "30/06/2026")
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            manifest, texts = self._write_bundle(type("T", (), {"name": td})(), "RREO_ALIGNED", "2026-06-30", [rreo_jun, fundeb_jun, mde_jun])
            result, _ = self._run(manifest, texts)
        self.assertEqual(result["reference_period"]["end"], "2026-06-30")
        self.assertEqual(result["status"], "PASS_F02_KNOWN_FAMILY_BATCH_OFFLINE_NOT_PERSISTED")

    def test_path_traversal_remote_effect_and_missing_family_stop(self):
        base = {
            "schema": "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1",
            "mode": "MANUAL_SUPERVISED_INGEST",
            "batch_id": "BAD",
            "batch_kind": "LOCAL_ONLY",
            "reference_period": {"start": "2026-01-01", "end": "2026-05-31"},
            "sources": [
                source("F", "FUNDEB_LOCAL", b"x", "../escape.pdf"),
                source("M", "MDE_25_LOCAL", b"y", "m.pdf"),
            ],
            "remote_effects_authorized": effects_false(),
        }
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "SNAPSHOT_PATH_UNSAFE"):
            validate_batch_manifest(base, self.adapter)
        base["sources"][0]["snapshot_path"] = "f.pdf"
        base["remote_effects_authorized"]["gold_write"] = True
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "REMOTE_EFFECT_ENABLED"):
            validate_batch_manifest(base, self.adapter)
        base["remote_effects_authorized"]["gold_write"] = False
        base["sources"] = base["sources"][:1]
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "SOURCE_COUNT"):
            validate_batch_manifest(base, self.adapter)

    def test_hash_and_manifest_period_drift_stop(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            tmp = type("T", (), {"name": td})()
            manifest, texts = self._write_bundle(tmp, "LOCAL_ONLY", "2026-05-31", [FUNDEB_MAY, MDE_MAY])
            manifest["sources"][0]["expected_sha256"] = "0" * 64
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "IMMUTABLE_MISMATCH"):
                self._run(manifest, texts)

        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            tmp = type("T", (), {"name": td})()
            manifest, texts = self._write_bundle(tmp, "LOCAL_ONLY", "2026-04-30", [FUNDEB_MAY, MDE_MAY])
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "MANIFEST_PERIOD_DRIFT"):
                self._run(manifest, texts)


    def test_unknown_and_duplicate_family_manifest_stop(self):
        base = {
            "schema": "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1",
            "mode": "MANUAL_SUPERVISED_INGEST",
            "batch_id": "BAD_FAMILY",
            "batch_kind": "LOCAL_ONLY",
            "reference_period": {"start": "2026-01-01", "end": "2026-05-31"},
            "sources": [
                source("F", "FUNDEB_LOCAL", b"x", "f.pdf"),
                source("M", "MDE_25_LOCAL", b"y", "m.pdf"),
            ],
            "remote_effects_authorized": effects_false(),
        }
        unknown = copy.deepcopy(base)
        unknown["sources"][1]["family"] = "ALIEN_FAMILY"
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "BAD_FAMILY"):
            validate_batch_manifest(unknown, self.adapter)

        duplicate = copy.deepcopy(base)
        duplicate["sources"][1]["family"] = "FUNDEB_LOCAL"
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "DUPLICATE_FAMILY"):
            validate_batch_manifest(duplicate, self.adapter)

    def test_absolute_snapshot_and_missing_remote_effect_key_stop(self):
        base = {
            "schema": "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1",
            "mode": "MANUAL_SUPERVISED_INGEST",
            "batch_id": "BAD_PATH",
            "batch_kind": "LOCAL_ONLY",
            "reference_period": {"start": "2026-01-01", "end": "2026-05-31"},
            "sources": [
                source("F", "FUNDEB_LOCAL", b"x", "/tmp/escape.pdf"),
                source("M", "MDE_25_LOCAL", b"y", "m.pdf"),
            ],
            "remote_effects_authorized": effects_false(),
        }
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "SNAPSHOT_PATH_UNSAFE"):
            validate_batch_manifest(base, self.adapter)

        base["sources"][0]["snapshot_path"] = "f.pdf"
        base["remote_effects_authorized"].pop("gold_write")
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "REMOTE_EFFECT_SET"):
            validate_batch_manifest(base, self.adapter)

    def test_snapshot_symlink_is_rejected_at_read_boundary(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            tmp = type("T", (), {"name": td})()
            manifest, texts = self._write_bundle(
                tmp, "LOCAL_ONLY", "2026-05-31", [FUNDEB_MAY, MDE_MAY]
            )
            rel_dir = Path(td).relative_to(ROOT)
            target = Path(td) / "target.pdf"
            target.write_bytes(b"payload")
            link = Path(td) / "link.pdf"
            link.symlink_to(target.name)
            manifest["sources"][0]["snapshot_path"] = str(rel_dir / "link.pdf")
            manifest["sources"][0]["expected_sha256"] = hashlib.sha256(b"payload").hexdigest()
            manifest["sources"][0]["expected_bytes"] = len(b"payload")
            texts[b"payload"] = FUNDEB_MAY
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "SNAPSHOT_PATH_SYMLINK"):
                self._run(manifest, texts)

    def test_parser_schema_drift_is_normalized_to_bundle_stop(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            tmp = type("T", (), {"name": td})()
            manifest, texts = self._write_bundle(
                tmp, "LOCAL_ONLY", "2026-05-31", [FUNDEB_MAY, MDE_MAY]
            )
            with patch(
                "robo_dados_publicos.manual_ingest.f02_known_family_bundle."
                "normalize_f02_local_monitoring_document",
                return_value={"family": "FUNDEB_LOCAL", "authority": "X", "period_start": "2026-01-01", "period_end": "2026-05-31"},
            ):
                with self.assertRaisesRegex(F02KnownFamilyBundleStop, "NORMALIZED_SCHEMA"):
                    self._run(manifest, texts)

    def test_mixed_normalized_periods_stop(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            tmp = type("T", (), {"name": td})()
            manifest, texts = self._write_bundle(
                tmp, "LOCAL_ONLY", "2026-05-31", [FUNDEB_MAY, MDE_APR]
            )
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "MANIFEST_PERIOD_DRIFT"):
                self._run(manifest, texts)

    def test_controller_and_maturity_drift_stop(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel = Path(td).relative_to(ROOT)
            controller = load_json(ROOT / "config/drive_ingestion_controller.v3.json")
            controller["family_default_routes"]["RREO"] = "REVIEW"
            controller_path = Path(td) / "controller.json"
            controller_path.write_text(json.dumps(controller), encoding="utf-8")
            adapter = copy.deepcopy(self.adapter)
            adapter["controller_alignment"]["controller_contract_path"] = str(rel / "controller.json")
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "CONTROLLER_ROUTE_DRIFT"):
                validate_controller_alignment(adapter, root=ROOT)

        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel = Path(td).relative_to(ROOT)
            maturity = load_json(ROOT / "config/source_family_maturity_registry.v1.json")
            maturity["families"]["RREO"]["level"] = "EXECUTION_READY_BOUNDED"
            maturity_path = Path(td) / "maturity.json"
            maturity_path.write_text(json.dumps(maturity), encoding="utf-8")
            adapter = copy.deepcopy(self.adapter)
            adapter["controller_alignment"]["maturity_registry_path"] = str(rel / "maturity.json")
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "INDIVIDUAL_MATURITY_DRIFT"):
                validate_controller_alignment(adapter, root=ROOT)

    def test_adapter_and_gate_cannot_enable_remote_effects(self):
        adapter = copy.deepcopy(self.adapter)
        adapter["automatic_effects"]["gold_write"] = True
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "AUTOMATIC_EFFECT_ENABLED"):
            validate_adapter_contract(adapter)

        gate = load_json(ROOT / "config/f02_known_family_bundle_gate.v1.json")
        gate["blocked_remote_effects"]["gold_write"] = False
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "GATE_REMOTE_EFFECT_OPEN"):
            validate_gate_contract(gate)

    def test_adapter_config_paths_reject_absolute_and_symlink(self):
        absolute = copy.deepcopy(self.adapter)
        absolute["controller_alignment"]["controller_contract_path"] = "/tmp/controller.json"
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "CONTROLLER_PATH_UNSAFE"):
            validate_controller_alignment(absolute, root=ROOT)

        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel = Path(td).relative_to(ROOT)
            link = Path(td) / "controller-link.json"
            link.symlink_to(ROOT / "config/drive_ingestion_controller.v3.json")
            adapter = copy.deepcopy(self.adapter)
            adapter["controller_alignment"]["controller_contract_path"] = str(rel / link.name)
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "CONTROLLER_PATH_SYMLINK"):
                validate_controller_alignment(adapter, root=ROOT)


    def test_unknown_batch_kind_missing_source_field_and_bad_sha_stop(self):
        base = {
            "schema": "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1",
            "mode": "MANUAL_SUPERVISED_INGEST",
            "batch_id": "BAD_SHAPE",
            "batch_kind": "LOCAL_ONLY",
            "reference_period": {"start": "2026-01-01", "end": "2026-05-31"},
            "sources": [
                source("F", "FUNDEB_LOCAL", b"x", "f.pdf"),
                source("M", "MDE_25_LOCAL", b"y", "m.pdf"),
            ],
            "remote_effects_authorized": effects_false(),
        }

        bad_kind = copy.deepcopy(base)
        bad_kind["batch_kind"] = "UNKNOWN_KIND"
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "BATCH_KIND"):
            validate_batch_manifest(bad_kind, self.adapter)

        missing = copy.deepcopy(base)
        missing["sources"][0].pop("expected_sha256")
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "MISSING_FIELDS"):
            validate_batch_manifest(missing, self.adapter)

        bad_sha = copy.deepcopy(base)
        bad_sha["sources"][0]["expected_sha256"] = "not-a-sha"
        with self.assertRaisesRegex(F02KnownFamilyBundleStop, "BAD_SHA256"):
            validate_batch_manifest(bad_sha, self.adapter)


    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"),
        "descriptor-relative no-follow test requires POSIX",
    )
    def test_toctou_swap_to_symlink_before_final_open_stops(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            tmp = type("T", (), {"name": td})()
            manifest, texts = self._write_bundle(
                tmp, "LOCAL_ONLY", "2026-05-31", [FUNDEB_MAY, MDE_MAY]
            )
            rel = Path(manifest["sources"][0]["snapshot_path"])
            victim = ROOT / rel
            outside = Path(td) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            real_open = os.open
            swapped = {"done": False}

            def racing_open(path, flags, mode=0o777, *, dir_fd=None):
                if (
                    not swapped["done"]
                    and str(path) == rel.parts[-1]
                    and dir_fd is not None
                    and not (flags & getattr(os, "O_DIRECTORY", 0))
                ):
                    victim.unlink()
                    victim.symlink_to(outside)
                    swapped["done"] = True
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with patch(
                "robo_dados_publicos.manual_ingest.f02_known_family_bundle.os.open",
                side_effect=racing_open,
            ):
                with self.assertRaisesRegex(F02KnownFamilyBundleStop, "SNAPSHOT_PATH_SYMLINK"):
                    self._run(manifest, texts)
            self.assertTrue(swapped["done"])

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "mkfifo"), "FIFO test requires POSIX")
    def test_fifo_and_directory_snapshot_are_not_regular_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel_dir = Path(td).relative_to(ROOT)
            fifo = Path(td) / "snapshot.fifo"
            os.mkfifo(fifo)
            base = {
                "schema": "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1",
                "mode": "MANUAL_SUPERVISED_INGEST",
                "batch_id": "SPECIAL_FILE",
                "batch_kind": "LOCAL_ONLY",
                "reference_period": {"start": "2026-01-01", "end": "2026-05-31"},
                "sources": [
                    source("F", "FUNDEB_LOCAL", b"x", str(rel_dir / fifo.name)),
                    source("M", "MDE_25_LOCAL", b"y", str(rel_dir / "missing.pdf")),
                ],
                "remote_effects_authorized": effects_false(),
            }
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "NOT_REGULAR"):
                run_known_family_bundle(self.adapter, base, root=ROOT)

        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            rel_dir = Path(td).relative_to(ROOT)
            directory = Path(td) / "snapshot-dir"
            directory.mkdir()
            base = {
                "schema": "F02_KNOWN_FAMILY_BATCH_MANIFEST_V1",
                "mode": "MANUAL_SUPERVISED_INGEST",
                "batch_id": "DIRECTORY_FILE",
                "batch_kind": "LOCAL_ONLY",
                "reference_period": {"start": "2026-01-01", "end": "2026-05-31"},
                "sources": [
                    source("F", "FUNDEB_LOCAL", b"x", str(rel_dir / directory.name)),
                    source("M", "MDE_25_LOCAL", b"y", str(rel_dir / "missing.pdf")),
                ],
                "remote_effects_authorized": effects_false(),
            }
            with self.assertRaisesRegex(F02KnownFamilyBundleStop, "NOT_REGULAR"):
                run_known_family_bundle(self.adapter, base, root=ROOT)


if __name__ == "__main__":
    unittest.main()
