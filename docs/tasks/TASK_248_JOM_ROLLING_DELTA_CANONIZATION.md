# TASK 248 — canonização do delta live do JOM

Issue: #823

## Objetivo

Transformar o resultado live read-only e sanitizado da TASK247 em um novo baseline canônico de identidades do Jornal Oficial de Limeira, sem reescrever a TASK217C e sem autorizar download de PDFs, persistência no Drive/serving, publicação, promoção, agenda ou recorrência.

## Origem da prova

A TASK247 foi incorporada ao `main` no SHA `3c3b59606ecafbd48fe634ef850543ac03c72bdc`. A execução live autorizada ocorreu no run GitHub Actions `35151868669`, head runtime `cbaa17bb14a90bf171c10f090e9f596896120368`, com conclusão `success`.

O artefato sanitizado `task-247-jom-rolling-sanitized-discovery` tem ID `10469402153`, SHA-256 do ZIP `bea443dcec80cd271e6902c3f16cdf0ee65dea0468a90a5d35d14b013ccdbb7f` e resultado lógico SHA-256 `28701eb442dee5bc74e34fe9c7c5a21cec27ffcbae680fe0988ef4a64c978b6d`.

## Resultado live canonizado

O baseline histórico TASK217C permanece intacto: 99 identidades oficiais até 08/09/2026, incluindo as edições 7316–7320 em setembro.

A janela TASK247, de 09/09/2026 a 16/09/2026, consultou uma página de índice, consumiu dois GETs estimados e descobriu quatro novas identidades:

- 7321 — 09/09/2026;
- 7322 — 10/09/2026;
- 7323 — 11/09/2026;
- 7324 — 12/09/2026.

O inventário canônico de identidades passa, portanto, a 103 edições conhecidas. A data de publicação mais recente efetivamente observada é 12/09/2026.

## Limite epistemológico

`103 identidades conhecidas` não significa `103 PDFs digeridos`. A TASK247 não baixou documentos e a TASK248 também não baixa. O conteúdo das edições 7321–7324 permanece não materializado.

Da mesma forma, a observação da janela até 16/09/2026 não autoriza afirmar ausência final de publicações em 13–16/09. Publicação tardia ou backfill continuam possíveis e devem ser detectados pela próxima descoberta incremental.

## Efeitos remotos

A canonização TASK248 é repo-only:

- fonte remota: 0 novas consultas;
- download de PDF: 0;
- Drive: 0 escrita;
- serving: 0 escrita;
- publicação: 0;
- promoção: 0;
- schedule: desabilitado;
- recorrência: desabilitada.

## Próximo marco

O novo baseline pode alimentar uma próxima janela de descoberta rolling. Qualquer recorrência automática, download/redigest dos PDFs, extração de eventos ou atualização de serving exige contrato e autorização próprios. A linha JOM pode continuar avançando independentemente dos bloqueios G1/G2/G3 do SIOPE.
