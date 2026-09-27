import json
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from robo_dados_publicos.journal.processing import (
    JournalPdfProcessor,
    chunk_redacted_text,
    parse_events_from_page,
    redact_personal_identifiers,
    sha256_file,
)

FIXTURE = Path(__file__).parent / 'fixtures' / 'jornal_oficial_fixture_2pages.pdf'


class TestJornalProcessing(unittest.TestCase):
    def test_redaction_removes_personal_identifiers_but_not_cnpj(self):
        text = 'CPF 123.456.789-09 RG 12.345.678-9 email a@b.com fone (19) 99999-0000 CNPJ 61.086.929/0001-70'
        got = redact_personal_identifiers(text)
        self.assertIn('[CPF_REDACTED]', got.text)
        self.assertIn('[RG_REDACTED]', got.text)
        self.assertIn('[EMAIL_REDACTED]', got.text)
        self.assertIn('[PHONE_REDACTED]', got.text)
        self.assertIn('61.086.929/0001-70', got.text)
        self.assertGreaterEqual(got.total, 4)

    def test_extract_pages_from_textual_pdf(self):
        pages = JournalPdfProcessor().extract_pages(FIXTURE)
        self.assertEqual(2, len(pages))
        self.assertIn('CONTRATO', pages[0].text)
        self.assertIn('PORTARIA', pages[1].text)
        status, metrics = JournalPdfProcessor().text_status(pages)
        self.assertEqual('PASS_TEXT_EXTRACTION', status)
        self.assertGreater(metrics['total_extracted_chars'], 120)

    def test_scanned_or_blank_style_pdf_stops_for_ocr(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'blank.pdf'
            w = PdfWriter(); w.add_blank_page(width=595, height=842)
            with open(p, 'wb') as f: w.write(f)
            pages = JournalPdfProcessor().extract_pages(p)
            status, _ = JournalPdfProcessor().text_status(pages)
            self.assertEqual('STOP_OCR_REQUIRED', status)

    def test_event_parser_extracts_contract_fields(self):
        text = '''SECRETARIA MUNICIPAL DE ADMINISTRAÇÃO - Atos Oficiais
CONTRATO Nº: 51/2025
PREGÃO ELETRÔNICO Nº: 19/2025
PROCESSO Nº: 903.586/2025
EDITAL Nº: 20/2025
CONTRATADA: Consórcio Exemplo Ltda
CNPJ nº 61.086.929/0001-70
OBJETO: Contratação de serviços especializados.
VALOR: R$ 532.800,00
DATA DA ASSINATURA: 02/07/2025
CPF 123.456.789-09'''
        events = parse_events_from_page(text, edition=7309, publication_date='2026-08-21', page_number=1, source_url='https://example.org/a.pdf', source_sha256='a'*64)
        self.assertEqual(1, len(events))
        e=events[0]
        self.assertEqual('CONTRATO', e.event_type)
        self.assertEqual('51/2025', e.contract_number)
        self.assertEqual('903.586/2025', e.process_number)
        self.assertEqual('PREGÃO ELETRÔNICO', e.bidding_modality)
        self.assertEqual('19/2025', e.bidding_number)
        self.assertEqual('61086929000170', e.cnpj)
        self.assertEqual('532800.00', e.value_brl)
        self.assertIn('[CPF_REDACTED]', e.excerpt_redacted)

    def test_event_parser_distinguishes_term_addendum(self):
        text='''SECRETARIA MUNICIPAL DE SAÚDE
PRIMEIRO TERMO ADITIVO AO CONTRATO Nº: 101/2024
PROCESSO Nº: 37.339/2024
OBJETO: Prorrogação de prazo de contrato.'''
        events=parse_events_from_page(text, edition=6910, publication_date='2025-01-28', page_number=4, source_url=None, source_sha256='b'*64)
        self.assertEqual('TERMO_ADITIVO_CONTRATO', events[0].event_type)
        self.assertEqual('101/2024', events[0].contract_number)

    def test_chunking_is_deterministic_and_bounded(self):
        text = ('linha com dados públicos e contexto\n' * 150).strip()
        a=chunk_redacted_text(text, max_chars=500, overlap_chars=50)
        b=chunk_redacted_text(text, max_chars=500, overlap_chars=50)
        self.assertEqual(a,b)
        self.assertGreater(len(a), 2)
        self.assertTrue(all(len(x) <= 500 for x in a))

    def test_bronze_staging_is_hash_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'bronze.pdf'
            first=JournalPdfProcessor.stage_bronze(FIXTURE,dest)
            second=JournalPdfProcessor.stage_bronze(FIXTURE,dest)
            self.assertEqual('COPIED_IMMUTABLE',first['status'])
            self.assertEqual('REUSED_IDENTICAL',second['status'])
            self.assertEqual(sha256_file(FIXTURE),sha256_file(dest))
            dest.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'STOP_BRONZE_MUTATION_ATTEMPT'):
                JournalPdfProcessor.stage_bronze(FIXTURE,dest)

    def test_end_to_end_outputs_only_redacted_derived_text(self):
        with tempfile.TemporaryDirectory() as td:
            out=JournalPdfProcessor().process(FIXTURE, edition=7309, publication_date='2026-08-21', source_url='https://example.org/7309.pdf', out_dir=td)
            self.assertEqual('PASS_DOCUMENT_PROCESSING',out['status'])
            self.assertEqual(2,out['silver_pages'])
            self.assertGreaterEqual(out['gold_events'],2)
            silver=(Path(td)/'pages_silver.jsonl').read_text(encoding='utf-8')
            rag=(Path(td)/'chunks_rag.jsonl').read_text(encoding='utf-8')
            gold=(Path(td)/'events_gold.jsonl').read_text(encoding='utf-8')
            self.assertNotIn('123.456.789-09',silver+rag+gold)
            self.assertNotIn('teste.pessoa@example.com',silver+rag+gold)
            self.assertIn('[CPF_REDACTED]',silver+rag+gold)
            self.assertIn('61086929000170',gold)
            manifest=json.loads((Path(td)/'edition_manifest.json').read_text())
            self.assertEqual(sha256_file(FIXTURE),manifest['source_sha256'])
            self.assertEqual('COPIED_IMMUTABLE',manifest['bronze']['status'])

    def test_no_ocr_output_files_when_text_is_insufficient(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'blank.pdf'
            w=PdfWriter(); w.add_blank_page(width=595,height=842)
            with open(p,'wb') as f: w.write(f)
            outdir=Path(td)/'out'
            out=JournalPdfProcessor().process(p, edition=9999, publication_date=None, source_url=None, out_dir=outdir)
            self.assertEqual('STOP_OCR_REQUIRED',out['status'])
            self.assertTrue((outdir/'edition_manifest.json').exists())
            self.assertFalse((outdir/'pages_silver.jsonl').exists())
            self.assertFalse((outdir/'chunks_rag.jsonl').exists())
            self.assertFalse((outdir/'events_gold.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
