# Jornal Oficial de Limeira — pipeline documental M4E.3

## Objetivo
Converter uma edição oficial em dados derivados pesquisáveis sem confundir evidência original, extração textual, evento estruturado e interpretação.

## Fluxo

```text
PDF oficial declarado pelo índice
        ↓
SHA-256 + Bronze imutável
        ↓
extração textual nativa por página
        ↓
texto insuficiente? → STOP_OCR_REQUIRED
        ↓
minimização de identificadores pessoais
        ↓
Silver: páginas redigidas
        ├→ Gold: eventos/atos estruturados
        └→ RAG: chunks redigidos + proveniência
```

## Saídas

`edition_manifest.json`
: proveniência, hash, status do Bronze, métricas de texto e contagens.

`pages_silver.jsonl`
: texto normalizado por página, com CPF/RG/e-mail/telefone minimizados e pista de órgão.

`events_gold.jsonl`
: atos detectados por regras determinísticas e campos estruturados quando presentes.

`chunks_rag.jsonl`
: chunks redigidos, por página, com hash, edição, data e URL da evidência.

## Eventos iniciais
- CONTRATO
- TERMO_ADITIVO_CONTRATO
- APOSTILAMENTO
- ATA_REGISTRO_PRECOS
- CONVENIO
- DECRETO
- PORTARIA
- LEI
- RESOLUCAO
- EDITAL
- AVISO_LICITACAO

## Princípio de precisão
O parser é conservador. Se um padrão ainda não foi coberto por fixture/regressão, o software pode deixar de estruturar o ato, mas não deve inventar um ato ou um campo.

## Exemplo

```bash
python3 main.py journal-process \
  --pdf runtime/edicao.pdf \
  --edition 7309 \
  --publication-date 2026-08-21 \
  --source-url 'https://.../edicao.pdf' \
  --out-dir runtime/jornal_7309
```

## OCR
A 0.5.3 não executa OCR. Edições sem texto extraível retornam `STOP_OCR_REQUIRED`. Isso evita reconstruir números por OCR quando a camada textual nativa já deveria ser a primeira escolha e evita tratamento silencioso de documentos potencialmente degradados.
