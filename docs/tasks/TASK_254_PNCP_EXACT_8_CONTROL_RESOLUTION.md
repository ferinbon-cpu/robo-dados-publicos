# TASK 254 — resolução exata dos 8 controles JOM→PNCP

## Objetivo

Preparar um carrier `T1_REMOTE_READONLY` fail-closed para uma futura observação one-shot de exatamente oito identificadores PNCP que a TASK253 encontrou escritos literalmente no Jornal Oficial de Limeira.

A implementação desta tarefa é **inerte em `main`**. A PR não realiza GET ao PNCP.

## Fonte canônica

A TASK253 preservou oito anchors da classe:

`EXPLICIT_PNCP_ID_IN_OFFICIAL_JOM_TEXT`

Todos usam o CNPJ de Limeira `45132495000140` e foram extraídos deterministicamente do texto sanitizado dos JOM 7321–7324.

A fixture fonte é:

`docs/evidence/fixtures/task253/TASK_253_EXPLICIT_PNCP_CONTROL_ANCHORS.jsonl`

SHA-256:

`db946b80913ebb892168b5406fd8b5cc274a282ef1f81827d6ba29a2a8f0e7b3`.

## Transformação exata ID → URL

O identificador PNCP já codifica CNPJ, tipo, sequencial e ano.

Exemplo:

`45132495000140-1-000646/2026`

vira unicamente:

`https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/646`

Nenhuma busca por objeto, processo, fornecedor ou similaridade participa dessa transformação.

## Escopo do futuro live

Somente a rota pública DETAIL:

`GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}`

Limites:

- 8 alvos exatos;
- 1 GET por alvo;
- 8 GETs totais;
- 0 preflight;
- 0 paginação;
- 0 busca por publicação;
- 0 ITEMS;
- 0 HISTORY;
- 0 fonte orçamentária;
- 0 contratos vinculados;
- 0 retry;
- 0 redirect seguido;
- 0 descoberta de URL alternativa.

## Validação de identidade

Uma resposta HTTP 200 só é considerada resolução quando o JSON devolve simultaneamente:

- `numeroControlePNCP` exatamente igual ao controle esperado;
- `anoCompra = 2026`;
- `sequencialCompra` exatamente igual ao sequencial derivado do ID;
- `orgaoEntidade.cnpj = 45132495000140`.

HTTP 200 não JSON, schema inesperado ou qualquer drift nesses campos termina em STOP.

`processo`, objeto, valor, fornecedor, datas e semântica não substituem esses identificadores.

## Indisponibilidade

HTTP 404, 503, 504 ou falha de transporte podem ser preservados como:

`UNRESOLVED_SOURCE_OBSERVATION`.

Isso significa apenas que aquele registro não foi resolvido naquela observação bounded.

Não significa:

- ausência global no PNCP;
- inexistência da contratação;
- invalidação do PNCP ID publicado no JOM;
- prova de que não há contrato/empenho;
- prova financeira negativa.

## Persistência

O live futuro poderá persistir em artifact de 1 dia somente resultado sanitizado e metadados de resposta.

Continuam proibidos:

- payload bruto;
- Drive;
- Bronze/Silver/Gold;
- serving;
- publicação;
- promoção;
- TCE;
- schedule;
- recorrência.

## Autorização

O carrier em `main` mantém rede desligada.

Um live futuro exige arquivo novo:

`runtime/task254_owner_authorization.json`

preso ao SHA de implementação TASK254 já mesclado e à operação:

`EXACT_8_TASK253_PNCP_PURCHASE_CONTROL_DETAIL_RESOLUTION`.

A runtime branch só poderá divergir desse SHA por:

- `runtime/task254_owner_authorization.json`;
- `runtime_triggers/task254_pncp_exact_8_control_resolution.run`.

## Próximo gate

`OWNER_AUTHORIZED_EXACT_8_PNCP_DETAIL_GETS_ON_MERGED_TASK254_SHA`

Mesmo que os 8 detalhes PNCP sejam resolvidos futuramente, isso ainda não prova cadeia PNCP→TCE, pagamento, execução financeira ou compliance.
