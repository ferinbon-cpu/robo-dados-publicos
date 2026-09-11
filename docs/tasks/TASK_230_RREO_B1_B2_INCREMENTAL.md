# TASK 230 — RREO 2026 B1/B2 incremental series

## Objetivo

Fechar a fila `RREO_CORROBORATION_GAPS` da TASK 226 sem reingestão cega dos 18 documentos RREO em custódia. A unidade de decisão é o **fato semântico por período**, não o PDF.

## Resultado

Os 18 documentos foram classificados. A materialização substantiva desta task fica limitada a:

- Anexo 14 de jan–fev/2026 (`DOC-047`): novo ponto bimestral compacto;
- Anexo 14 de jan–abr/2026 (`DOC-046`): resumo primário e camada de reconciliação;
- Anexo 8 de jan–fev/2026 (`DOC-064`): novo ponto detalhado de MDE/FUNDEB;
- Anexo 6 de jan–fev/2026 (`DOC-060`): confirmação detalhada dos resultados fiscal/nominal e DCL do bimestre.

`DOC-061` e `DOC-062` permanecem cobertos pela TASK 188. `DOC-063` permanece coberto pela TASK 190. `DOC-048` já tem o total funcional Educação de jan–abr preservado pela TASK 190 e não é duplicado.

## Semântica temporal

Os valores de fevereiro e abril são **posições acumuladas até o bimestre**. Não são valores mensais de fevereiro/abril e não se deve obter fluxo mensal por subtração automática sem contrato específico da métrica.

## Anexo 14

O Anexo 14 é resumo oficial. Ele pode servir a consultas compactas e reconciliação, mas não substitui o anexo detalhado quando a pergunta exige decomposição. A série preserva execução orçamentária, RCL, RPPS, resultados primário/nominal, restos a pagar e acompanhamento constitucional de MDE/FUNDEB/saúde.

Os percentuais de MDE, FUNDEB e saúde em fevereiro/abril são acompanhamento parcial do exercício. **Não autorizam conclusão de cumprimento anual.**

## Restos a pagar

A leitura integral mostrou que o total de RP do Anexo 14 não é igual ao agregado da TASK 188/Anexo 7. A igualdade não é exigida porque os escopos e linhas não são idênticos. Há, porém, correspondência exata no saldo processado do Poder Executivo: R$ 26.670.251,53 em fevereiro e R$ 16.476.433,49 em abril. Isso é registrado como `EXACT_COMPONENT_MATCH_ONLY`.

## Educação

O Anexo 8 B1 acrescenta o ponto jan–fev para MDE/FUNDEB. Mantêm-se separadas três noções:

- gasto funcional Educação do Anexo 2;
- gasto/receita de MDE e FUNDEB do Anexo 8;
- despesa da Secretaria de Educação em outras camadas contábeis.

Elas não são identidades intercambiáveis.

## Guardas

- `SAME_FACT_DIFFERENT_ANNEX_NE_NEW_FACT`
- `CUMULATIVE_BIMESTER_NE_MONTHLY_FLOW`
- `ANEXO14_SUMMARY_NE_DETAILED_ANNEX`
- `RREO_ANEXO8_MDE_NE_ANEXO2_FUNCTION_EDUCATION`
- `RESTS_PAYABLE_SUMMARY_NE_SECOND_COUNT`
- `ANEXO14_RESTS_SCOPE_NE_ANEXO7_SCOPE`
- `PARTIAL_COMPONENT_MATCH_NE_FULL_STATEMENT_EQUALITY`
- `CONSTITUTIONAL_PERCENT_PARTIAL_PERIOD_NE_ANNUAL_COMPLIANCE`
- `RPPS_RESULT_NE_FREE_CASH`
- `NOMINAL_RESULT_NE_BUDGET_SURPLUS`
- `COMMITTED_NE_LIQUIDATED_NE_PAID`
- `NO_CONTEXTUAL_COVERAGE_CHANGE`

## Não efeitos

Sem rede nova, sem escrita no Drive, sem serving/publicação, sem agenda e sem alteração da cobertura contextual 38/38.
