# TASK 010M — probe único do `$metadata`/EDMX OData SIOPE 2025

## Resultado

`STOP_DNS_RESOLUTION_NO_EDMX_NO_RETRY`

A TASK 010M recebeu autorização explícita do proprietário para um único GET ao endpoint oficial `$metadata` do serviço OData SIOPE, sem município, ano, período ou valores financeiros. A autorização não incluía retry, paginação, autenticação, cookies, OAuth, login ou follow de redirect.

## Alvo autorizado

`https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/$metadata`

## Execução

Uma tentativa inicial pelo conector documental foi rejeitada localmente pela regra interna de segurança de URL antes de qualquer requisição de rede. Essa rejeição não consumiu o orçamento HTTP.

Em seguida foi realizada uma única tentativa outbound com GET intencional, `retry=0` e `max-redirs=0`. A resolução DNS de `www.fnde.gov.br` falhou antes do envio de uma requisição HTTP:

- `curl exit code = 6`;
- HTTP code reportado pelo cliente = `000`;
- bytes de resposta = `0`;
- EDMX recebido = `false`;
- autenticação = `false`;
- retry = `0`.

Por política fail-closed, a autorização one-shot é considerada conservadoramente consumida pelo intento de rede. Nenhuma segunda tentativa foi feita.

## Consequência semântica

Como nenhum EDMX foi recebido, não houve inspeção de propriedades, annotations, descriptions, functions, entity types ou qualquer outra estrutura OData. Logo:

- nenhuma descrição dos aliases foi observada;
- nenhuma bridge alias → conceito/estrutura interna foi provada;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN` permanece inalterado.

Não é legítimo inferir qualquer resultado sobre o conteúdo do `$metadata` a partir da falha de DNS.

## Estados preservados

- `0.7.0 = ACTIVE`;
- `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série fechada = `2016-2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Efeitos

Não houve consulta municipal, observação de valor financeiro, Drive, persistência, Gold, publicação, fechamento anual, expansão da série ou promoção de 2026.

## Próximo gate

Qualquer nova tentativa remota contra `$metadata` exige nova autorização explícita. A classe de evidência desejada continua sendo o EDMX/metadata oficial do serviço OData; sem resposta, B2 permanece bloqueado.
