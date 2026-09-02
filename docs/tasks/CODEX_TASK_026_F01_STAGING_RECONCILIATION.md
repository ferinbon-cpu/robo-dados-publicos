# TASK 026 — F01 STAGING RECONCILIATION

## Objetivo

Reconciliar, em T0/offline, o bundle derivado do primeiro lote supervisionado F01 (PPA/LDO/LOA 2026) depois da TASK 025, sem transformar staging em Silver e sem executar qualquer efeito remoto.

A TASK 025 fixou os três documentos oficiais e implementou o contrato de ingestão manual. A TASK 026 trata somente da consistência interna dos produtos derivados já produzidos sob supervisão.

## Bundle reconciliado

O fechamento possui seis artefatos derivados com hash fixado:

- `PPA_PROGRAM_2001_INDICATORS_V01.csv`;
- `PPA_PROGRAM_2001_ACTIONS_SELECTED_V01.csv`;
- `LDO_2026_STRUCTURAL_MARKERS_V01.csv`;
- `LOA_2026_PRIOR_BRIDGE_EVIDENCE_V01.csv`;
- `STAGING_F01_STRUCTURED_PARSE_V01.json`;
- `QA_F01_STRUCTURED_PARSE_V01.json`.

A reconciliação exige correspondência exata do conjunto e dos SHA-256. Drift, falta ou artefato extra produz STOP.

## Regras semânticas

O staging somente passa se:

1. os hashes e paginação das três fontes continuarem iguais aos fixados na TASK 025;
2. a trajetória do indicador EITI permanecer `52 → 53 → 55 → 57 → 59 → 59`;
3. as ações selecionadas do Programa 2001 permanecerem explicitamente `eiti_specific=false`;
4. qualquer linha marcada para revisão continuar sem promoção;
5. os cinco marcadores estruturais da LDO permanecerem presentes;
6. a LOA continuar com `current_pdf_text_layer=ABSENT` e parser integral bloqueado;
7. as duas evidências antigas de ações da LOA continuarem `DERIVED_PRIOR_EVIDENCE_ONLY`, sem reparse do bruto e sem atribuição EITI;
8. a identidade financeira EITI continuar `EVIDENCIA_INSUFICIENTE`;
9. o QA continuar 10/10 e `PASS_STAGING_ONLY`;
10. a decisão de promoção continuar `DO_NOT_PROMOTE_LOA_FULL_PARSE_INCOMPLETE`.

## O que o PASS significa

`PASS_F01_STAGING_RECONCILED_OFFLINE` significa apenas que o bundle derivado conhecido é internamente consistente com as evidências fixadas.

Não significa:

- Silver validado;
- Gold validado;
- execução financeira específica da EITI comprovada;
- LOA integral parseada;
- autorização de OCR;
- autorização de Drive, serving, dashboard ou publicação.

## Bloqueio restante

O bloqueio estrutural continua sendo a representação da LOA: o PDF canônico de 466 páginas não possui camada textual extraível pelo parser atual. O material histórico derivado pode ser usado como pista e reconciliação, nunca como substituto da fonte.

A próxima etapa deve resolver uma entrada reproduzível para a LOA — preferencialmente uma fonte oficial machine-readable; na ausência dela, OCR determinístico com manifest, hashes, QA e auditoria própria.

## Efeitos

Esta tarefa é T0/offline: rede, Drive, Bronze, Silver, Gold, serving, site, publicação, agenda e recorrência permanecem zerados/desligados.
