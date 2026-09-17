# TASK 250 — diagnóstico bounded do STOP de byte-count da TASK249

## Contexto

O primeiro live da TASK249 (`run 35174078683`) consumiu a autorização one-shot e encerrou fail-closed após três GETs com `STOP_TASK249_SOURCE_BYTE_COUNT_INVALID`. Pela ordem fixa da fila TASK248, as edições 7321 e 7322 foram aceitas e a validação falhou na edição 7323; a edição 7324 não foi solicitada.

Nenhum PDF bruto foi persistido, nenhum write no Drive ocorreu e nenhum efeito downstream foi autorizado.

## Problema

O código TASK249 agrupava em um único STOP três causas estruturalmente diferentes:

- arquivo temporário vazio;
- tamanho acima do limite de 100.000.000 bytes;
- divergência entre o contador de bytes do transporte e o tamanho efetivo gravado no arquivo temporário.

A primeira tentativa, portanto, provou o ponto de falha, mas não adjudicou qual dessas três causas ocorreu.

## Escopo da TASK250

A TASK250 prepara um diagnóstico live independente e estritamente menor:

- uma única identidade: edição 7323;
- uma única URL já pinada pela TASK248;
- no máximo um GET;
- sem redirect, retry ou descoberta alternativa;
- persistência apenas do JSON sanitizado;
- o PDF existe somente dentro de `TemporaryDirectory`;
- nenhum Drive/Bronze/Silver/Gold/OCR/parser/serving/publicação/promoção/schedule/recorrência.

O resultado classifica o byte-count em exatamente uma destas categorias:

- `EMPTY_FILE`;
- `OVER_MAX_BYTES`;
- `TRANSPORT_COUNTER_MISMATCH`;
- `BYTE_COUNT_VALID`.

## Fronteira de autorização

Esta implementação não autoriza o GET corretivo. O runtime exige `TASK_250_LIVE_AUTHORIZATION` vinculada ao SHA exato da implementação mesclada em `main`, com edição 7323, uma tentativa e todos os efeitos downstream `false`.

O `prossiga` que autorizou a TASK249 já foi consumido pelo run `35174078683` e não é reutilizado como autorização automática da TASK250.

## Próximo gate

Após CI e merge da implementação TASK250, uma nova autorização explícita do owner poderá disparar o único GET diagnóstico da edição 7323. O resultado deve ser canonizado antes de qualquer nova tentativa completa da TASK249 ou alteração de limites.
