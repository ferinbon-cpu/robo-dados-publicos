# M7 SIOPE Limeira — escopo aritmético do primeiro Gold 0.8.0

## Status

Este documento registra o contrato interpretativo do primeiro payload Gold derivado de `Dados_Gerais_Siope` para Limeira/SP, exercício 2024, período 6.

O artefato é **somente um resumo aritmético derivado** (`DERIVED_ARITHMETIC_ONLY_FROM_SIOPE_DADOS_GERAIS`). Ele não constitui auditoria fiscal, não prova cumprimento de MDE ou Fundeb, não substitui demonstrativos legais e não autoriza imputação de valores ausentes.

## Fórmulas determinísticas

As oito métricas usam exclusivamente campos já presentes no registro Silver de 52 campos, sem novo acesso ao SIOPE:

1. `receita_realizada_sobre_previsao_atualizada_pct` = `VAL_RECE_REAL / VAL_RECE_PREV_ATUA * 100`.
2. `despesa_paga_sobre_dotacao_atualizada_pct` = `VAL_DESP_PAGA / VAL_DESP_DOTA_ATUA * 100`.
3. `despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct` = `VL_DESP_PAGA_EDU / VL_DESP_DOTA_ATUA_EDU * 100`.
4. `participacao_educacao_na_despesa_empenhada_pct` = `VL_DESP_EMPE_EDU / VAL_DESP_EMPE * 100`.
5. `participacao_educacao_na_despesa_liquidada_pct` = `VL_DESP_LIQU_EDU / VAL_DESP_LIQU * 100`.
6. `participacao_educacao_na_despesa_paga_pct` = `VL_DESP_PAGA_EDU / VAL_DESP_PAGA * 100`.
7. `despesa_total_paga_por_habitante` = `VAL_DESP_PAGA / NUM_POPU`.
8. `despesa_educacao_paga_por_habitante` = `VL_DESP_PAGA_EDU / NUM_POPU`.

Percentuais são arredondados deterministicamente para quatro casas decimais e valores per capita para duas casas, com `ROUND_HALF_UP`.

## Integridade pinada

- contrato Gold: `SIOPE_DADOS_GERAIS_LIMEIRA_ARITHMETIC_SUMMARY_GOLD_V1`;
- payload: 1612 bytes;
- SHA-256: `d6a35db7c42129569c73f19de789d871d0d285929d8eb3fe2a04d5ef03fdd6e0`;
- Silver de origem: `072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da`;
- registro de origem: `20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6`.

A persistência remota preparada para a etapa seguinte é limitada a uma única criação `create-only` no `03_GOLD`, com colisão de nome bloqueando a execução antes de qualquer write. Overwrite, replace, delete, processamento, recorrência e schedule permanecem proibidos.
