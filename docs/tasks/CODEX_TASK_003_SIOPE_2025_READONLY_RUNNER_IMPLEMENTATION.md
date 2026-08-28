# CODEX TASK 003 — implementação do runner read-only SIOPE 2025 sem GET live

## Escopo

Esta entrega materializa o runner bounded desenhado na TASK 002, mas permanece integralmente `T0_OFFLINE`. Nenhum GET live ao SIOPE/FNDE/Olinda é autorizado ou executado por esta tarefa. O componente live permanece ausente (`live_transport=null`) e qualquer chamada de `run_bounded()` sem o `FakeSiope2025Transport` concreto termina em `STOP_LIVE_NOT_AUTHORIZED` antes de qualquer transporte.

Efeitos remotos autorizados e observados pela arquitetura desta tarefa: `source_get_count=0`, `drive_read_count=0`, `drive_write_count=0`, `publication=false`, sem secrets, sem persistência de body/records e sem criação Bronze/Silver/Gold.

## Arquitetura implementada

A implementação separa responsabilidades:

1. `siope_2025_request_plan.py` — materializa e valida o plano determinístico de requests e o ledger de orçamento/ordem;
2. `siope_2025_fake_transport.py` — transporte estritamente in-memory para fixtures T0;
3. `siope_2025_readonly_discovery_offline.py` — valida transporte/identidade/schema das observações sintéticas;
4. `siope_2025_bounded_runner.py` — máquina de execução/outcomes e guardas semânticos;
5. `siope_2025_evidence.py` — produz somente evidência estrutural sanitizada;
6. `run_siope_2025_bounded_offline.py` — CLI segura: sem argumentos apenas valida/materializa o plano; `--live` retorna STOP; fixtures positivas allowlisted usam apenas o fake transport;
7. `github_siope_2025_bounded_runner_gate.py` — gate T0 integrado ao CI offline.

Não existe adapter HTTP live nesta TASK 003.

## Plano bounded

O plano contém exatamente sete posições possíveis. P1–P6 são probes de identidade com cinco campos; o sétimo request é condicional e só pode ocorrer para P6 após `PHASE_A_PERIOD_6_OBSERVED_EXACT_IDENTITY`.

Cada `PlannedRequest` fixa: ordinal, fase, método `GET`, host `www.fnde.gov.br`, path Olinda exato pinado pela TASK 002, ano 2025, período, UF SP, município 352690, campos selecionados, timeout 60 s, limite 262144 bytes, uma tentativa, `retry=false`, `redirect=false`, `pagination=false`, `nextLink=false` e precondição da fase B.

O `RequestExecutionLedger` rejeita request fora de ordem, repetição do mesmo par fase/período e qualquer oitavo request. A segunda ocorrência de P6 só é válida porque pertence à fase `CONDITIONAL_SCHEMA` e depende da identidade exata observada na fase A.

## Evidência sanitizada

A evidência preparada contém somente metadados estruturais: ordinais/fases, status HTTP, content-type, tamanho de resposta, cardinalidade, flags de redirect/retry/nextLink, nomes de campos observados, contagem e SHA-256 dos nomes, status de presença dos 11 campos necessários às oito métricas, períodos observados, outcome e contadores zero de efeitos remotos.

São explicitamente marcados como não persistidos: body, valores de registros, valores de query, tokens, cookies e headers sensíveis. As oito métricas permanecem individualmente em `UNKNOWN`; `any_metric_proven=false`; fechamento anual permanece `UNKNOWN`; `promote_2025_to_proven=false`.

## Guardas semânticos

A TASK 003 falha se houver tentativa de:

- alterar o alvo para 2026, outra UF ou outro município;
- marcar fechamento anual como conhecido/fechado;
- promover 2025 para `PROVEN`;
- promover qualquer uma das oito métricas;
- habilitar batch futuro, rede, Drive, persistência ou publicação;
- alterar método, host, path, timeout, tamanho máximo, tentativas, retry, redirect, paginação ou nextLink;
- exceder o orçamento máximo de sete requests.

2025 permanece `UNPROVEN_RECENT`; `Dados_Gerais_Siope` permanece `UNPROVEN_FOR_2025`; P6 permanece `CANDIDATE_NOT_PROVEN`; comparabilidade semântica e fechamento anual permanecem `UNKNOWN`. 2026 continua fora do gate.

## Outcomes permitidos

O runner fake pode produzir somente os outcomes herdados do contrato da TASK 002: `2025_NOT_OBSERVED`, `2025_PERIODS_OBSERVED_SCHEMA_UNKNOWN` ou `2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN`. Qualquer drift estrutural ou semântico termina em STOP.

## Testes e validações

A suíte da TASK 003 cobre: P1–P6 uma vez cada; fase B condicional; budget 7 e oitavo request STOP; repetição indevida STOP; método/host/path/ano/período/timeout/bytes/tentativas/retry/redirect/paginação/nextLink fail-closed; HTTP/content-type/identidade/schema fail-closed; ausência de campo Gold; tentativa de promoção de métrica; tentativa de inferir fechamento anual; inclusão de 2026; CLI plan-only; live STOP; ausência de dependências de rede/Drive nos módulos centrais; e contadores de efeitos zero.

A autoridade final de PASS é o GitHub Actions no head final do PR. Até que os checks sejam observados, resultados de CI devem ser tratados como `UNOBSERVED`; este documento não inventa run IDs ou contagens.

## Próximo gate

Após merge e auditoria desta TASK 003, a TASK 004 poderá materializar separadamente o workflow/manual runner `T1_REMOTE_READONLY` e solicitar autorização humana explícita para o primeiro discovery live bounded. Mesmo nessa etapa: máximo absoluto de sete GETs, zero Drive/persistência/publicação, evidência sanitizada e nenhuma promoção automática de 2025.
