from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.ppa_2018_ocr import (
    ExactSourceClient,
    Task112Stop,
    bounded_excerpt,
    normalize_ocr,
    parse_tsv,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/task112_real_ppa_2018_2021_ocr.v1.json"


class TestTask112RealPpaOcrPreflight(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_contract_is_exact_and_bounded(self):
        validate_contract(self.data)
        self.assertEqual(2, self.data["source"]["max_http_requests_total"])
        self.assertFalse(self.data["source"]["retry"])
        self.assertFalse(self.data["source"]["discovery_search"])
        self.assertEqual(250, self.data["document"]["max_pdf_pages"])
        self.assertTrue(all(v == 0 for v in self.data["hard_boundaries"].values()))

    def test_url_or_host_drift_fails_closed(self):
        for field, value in (
            ("url", "https://www.limeira.sp.gov.br/other.pdf"),
            ("allowed_host", "example.com"),
        ):
            data = copy.deepcopy(self.data)
            data["source"][field] = value
            with self.assertRaises(Task112Stop):
                validate_contract(data)

    def test_retry_discovery_or_future_enablement_fails_closed(self):
        for section, field in (
            ("source", "retry"),
            ("source", "discovery_search"),
            (None, "future_execution_authorized"),
        ):
            data = copy.deepcopy(self.data)
            if section:
                data[section][field] = True
            else:
                data[field] = True
            with self.assertRaises(Task112Stop):
                validate_contract(data)

    def test_exact_source_client_rejects_non_allowlisted_host_before_network(self):
        client = ExactSourceClient(
            initial_url="https://example.com/file.pdf",
            allowed_host="www.limeira.sp.gov.br",
            max_requests=2,
        )
        with self.assertRaisesRegex(Task112Stop, "TASK112_HOST"):
            client.get()
        self.assertEqual([], client.request_log)

    def test_normalization_matches_accentless_signal(self):
        self.assertEqual(
            "ESCOLAS COM PROGRAMAS EM TEMPO INTEGRAL",
            normalize_ocr("Escolas com programas em tempo integral"),
        )
        self.assertEqual("LEI 5 947", normalize_ocr("Lei 5.947"))

    def test_tsv_parser_keeps_confidence_and_text(self):
        tsv = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t95.5\tEscolas\n"
            "5\t1\t1\t1\t1\t2\t0\t0\t10\t10\t92.0\tintegral\n"
        )
        text, conf = parse_tsv(tsv)
        self.assertEqual("Escolas integral", text)
        self.assertEqual([95.5, 92.0], conf)

    def test_excerpt_is_bounded(self):
        excerpt = bounded_excerpt("x " * 1000 + "escolas com programas em tempo integral " + "y " * 1000, "escolas com programas em tempo integral")
        self.assertLessEqual(len(excerpt), 500)
        self.assertIn("ESCOLAS COM PROGRAMAS EM TEMPO INTEGRAL", excerpt)


if __name__ == "__main__":
    unittest.main()
