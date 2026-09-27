# TASK 025 — MANUAL_SUPERVISED_INGEST F01 PPA/LDO/LOA

## Objetivo

Formalizar, em T0/offline, o primeiro contrato de ingestão supervisionada de documentos que foram obtidos manualmente e colocados pelo proprietário sob custódia do Drive do `ROBO_DADOS_PUBLICOS`.

O F01 contém a família de planejamento e orçamento municipal de Limeira/SP:

- PPA 2026–2029 — Lei Municipal 7.213/2025;
- LDO 2026 — Lei Municipal 7.141/2025;
- LOA 2026 — Lei Municipal 7.223/2025 e anexos.

## Separação de responsabilidades

O Drive preserva os arquivos oficiais e derivados de trabalho. O GitHub preserva o conhecimento operacional: contratos, parser, testes, gates e regras fail-closed.

`SOURCE` oficial tem precedência sobre `DERIVED`, `REFERENCE`, `ARCHIVE` e `PRODUCT`. MD, OCR, relatório, V10, dashboard ou site nunca substituem o PDF oficial.

## Evidência externa já concluída

Antes deste PR, o proprietário realizou uma migração supervisionada para `10_INBOX/PENDENTES/F01_PPA_LDO_LOA_2026` e verificou por readback os três arquivos canônicos. Este PR não repete nem autoriza efeitos remotos; apenas fixa os hashes/tamanhos/paginação já auditados em um contrato offline.

| Família | Lei | bytes | páginas | SHA-256 |
|---|---|---:|---:|---|
| PPA | 7.213/2025 | 4.856.211 | 105 | `3e5deb53448c2e5eea56217a4e5d7f20f7fc3859eff7fcb93a7de7eb17011c1a` |
| LDO | 7.141/2025 | 11.534.048 | 37 | `6f28017bb61fe6dbd7db44e2306bd1a48f813d8d40411d87c130fba78fca2406` |
| LOA | 7.223/2025 | 24.203.962 | 466 | `bc4c8bf4b2b1e8f59e880318c37ec7f7fbd4357a85a8b46c97750444dbf01d4b` |

## Implementação offline

`robo_dados_publicos/manual_ingest/planning_budget.py` adiciona primitivas puras para:

1. carregar e validar o contrato do lote;
2. conferir SHA-256, bytes e paginação de um PDF fornecido ao processo;
3. detectar presença/ausência de camada textual sem executar OCR;
4. extrair de forma delimitada o Programa 2001 e o indicador EITI do PPA;
5. parar se a trajetória conhecida `52 → 53 → 55 → 57 → 59 → 59` sofrer drift;
6. exigir marcadores estruturais mínimos na LDO;
7. impedir que mera continuidade do Programa 2001 seja promovida a identidade financeira EITI.

## Limite específico da LOA

O PDF canônico da LOA tem 466 páginas e não possui camada textual extraível pelo `pypdf`. O corpus histórico contém OCR, e a V10 contém evidências derivadas de ações do Programa 2001, mas nenhum desses derivados substitui a fonte.

Por isso este PR **não implementa um parser integral da LOA e não executa OCR**. A condição correta é fail-closed:

`CURRENT_CANONICAL_PDF_HAS_NO_EXTRACTABLE_TEXT_LAYER`

A próxima etapa deve escolher uma entrada reproduzível: OCR determinístico auditado ou fonte oficial machine-readable. Até lá, a saída integral da LOA não pode ser Silver.

## Regra de identidade financeira EITI

Código de programa igual entre PPA e LOA permite afirmar continuidade programática. Não permite atribuir todo o Programa 2001 à Educação Integral em Tempo Integral.

A prova financeira específica exige a cadeia:

`indicador/meta → programa → ação/subação explícita → unidade → fonte/destinação → natureza → dotação → empenhado → liquidado → pago`

Se qualquer elo necessário estiver ausente, retornar `EVIDENCIA_INSUFICIENTE`.

## Efeitos deste PR

- source network: 0;
- Drive reads/writes: 0;
- Bronze/Silver/Gold: 0;
- serving/site/publicação: 0;
- schedule/recurrence: false.

Os efeitos de custódia mencionados são evidência histórica externa já concluída, não efeitos deste PR.

## Próxima decisão

Após aprovação deste boundary offline:

1. executar o parser contra cópias locais controladas dos arquivos canônicos;
2. reconciliar a saída com o probe F01 e com a V10;
3. resolver a ausência de camada textual da LOA sem adivinhar dados;
4. somente depois avaliar uma promoção separada para Silver;
5. Gold/serving/site continuam fora do escopo.
