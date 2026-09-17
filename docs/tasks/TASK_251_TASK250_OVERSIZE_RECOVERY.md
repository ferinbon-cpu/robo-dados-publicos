# TASK 251 — canonização do diagnóstico TASK250 e recovery oversized 7323–7324

## Estado de entrada

A TASK249 executou uma única tentativa live bounded sobre a fila 7321–7324. As edições 7321 e 7322 foram estruturalmente validadas; a tentativa parou fail-closed em 7323 com `STOP_TASK249_SOURCE_BYTE_COUNT_INVALID`, antes de qualquer GET da 7324.

A TASK250 isolou a causa com um único GET autorizado da edição 7323. O run `35236892194`, implementação `40ce45d28ed18af0a2ce24d6bd2d651b87a5a2c5` e runtime head `563f5cfe2d381b2a2d3359603836dae1ea0bbf07` concluíram `PASS_TASK250_7323_BYTECOUNT_DIAGNOSTIC`.

O resultado sanitizado provou:

- HTTP 200;
- `application/pdf`;
- `transport_bytes = 126648737`;
- `temporary_stat_bytes = 126648737`;
- limite anterior = `100000000`;
- outcome = `OVER_MAX_BYTES`;
- 1 GET;
- zero Drive write;
- nenhum PDF bruto persistido;
- nenhum retry ou redirect.

Portanto o STOP da TASK249 decorreu do limite de tamanho, e não de arquivo vazio ou divergência entre contador de transporte e arquivo temporário.

## Decisão de desenho

O repositório já possui precedente específico para JOM oversized: a TASK217G usa `262144000` bytes (250 MiB) por documento. A TASK251 reutiliza exatamente esse teto, em vez de criar um novo valor ad hoc.

O recovery corretivo contém apenas as edições ainda não concluídas:

- 7323 — 11/09/2026;
- 7324 — 12/09/2026.

7321 e 7322 são explicitamente excluídas para evitar redownload de documentos já provados.

## Limites do futuro live

O carrier implementado por esta task continua inerte em `main`. Uma execução futura exige nova autorização do owner vinculada ao SHA exato da implementação mesclada.

Quando e somente quando autorizada, a execução poderá:

- fazer no máximo 2 GETs;
- usar apenas as duas URLs exatas herdadas da TASK248;
- aceitar no máximo 262.144.000 bytes por documento;
- aceitar no máximo 524.288.000 bytes agregados;
- validar HTTP, URL final, tipo de conteúdo, assinatura PDF, bytes, SHA-256 e páginas;
- persistir apenas JSON sanitizado de curta retenção.

Continuam proibidos:

- retry automático;
- redirects;
- descoberta de URL alternativa;
- Drive/Bronze/Silver/Gold;
- OCR e parser semântico;
- serving;
- publicação/promoção;
- schedule/recorrência;
- artifact ou commit de PDF bruto.

O limite é fiscalizado durante o streaming. Se um documento ultrapassar o teto, o processo encerra fail-closed antes de avançar para o próximo item.

## Evidência canônica

`docs/evidence/TASK_251_TASK250_OVERSIZE_CANONICAL_0.8.0.json` fixa:

- run TASK250 `35236892194`;
- artifact `10502829335`;
- digest ZIP `013e44c8711f444d884dd157639bd02d5839fc7337b1713c002f7ce45ad2ea8a`;
- hash do resultado sanitizado `70e0de78992bc555cac65a6e5fec0096aa20d98364d06a4c30e1f59c0e560065`;
- contexto imutável da TASK249 para 7321/7322/7323/7324;
- adjudicação `OVER_MAX_BYTES`.

O gate recompõe deterministicamente o hash do payload TASK250 antes de aceitar a evidência.

## Próximo gate

`SEPARATE_OWNER_AUTHORIZATION_REQUIRED_FOR_LIVE_2_DOCUMENT_RECOVERY`

A TASK251 não executa esse live. Depois de merge + CI pós-merge verde, a execução de 7323–7324 continua uma fronteira operacional separada.
