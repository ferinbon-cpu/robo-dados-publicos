# TASK 004A — preparação do primeiro discovery live SIOPE 2025 T1

## Estado desta etapa

A TASK 004A materializa a capacidade futura `T1_REMOTE_READONLY`, mas sua própria execução e validação permanecem `T0_OFFLINE`. Esta etapa **não autoriza nem realiza GET live**.

Base de engenharia: `232bd69c456c4e0035fecf73473d9e7356f52c1d`.

## Arquitetura preparada

- `config/siope_2025_t1_first_live_preparation.v1.json`: contrato machine-readable da preparação e dos limites do primeiro run;
- `config/siope_2025_t1_first_live_authorization.template.v1.json`: template propositalmente não autorizado;
- `robo_dados_publicos/sources/siope_2025_t1_authorization.py`: validação fail-closed do futuro artefato de autorização humana;
- `robo_dados_publicos/sources/siope_2025_t1_transport.py`: adapter HTTP read-only, sem efeito de rede no import e reutilizando o `SiopeClient` com limites mais estreitos;
- `robo_dados_publicos/sources/siope_2025_t1_discovery.py`: runtime bounded para P1–P6 e schema condicional P6;
- `scripts/run_siope_2025_t1_first_live.py`: entrypoint `prepare`/`live`, com import do transporte live somente depois do gate de autorização;
- `.github/workflows/siope-2025-t1-first-live-discovery.yml`: workflow exclusivamente manual;
- `scripts/github_siope_2025_t1_preparation_gate.py`: gate T0 da preparação;
- `tests/test_siope_2025_t1_preparation.py`: regressões offline e mock do caminho futuro.

## Trava de autorização

O workflow manual não é autorização. Para alcançar o transporte, o runtime exige um arquivo fixo `config/siope_2025_t1_first_live_authorization.v1.json`, que **não existe nesta TASK 004A**.

Quando a TASK 004B for explicitamente autorizada pelo proprietário, o artefato deverá:

1. declarar `authorized=true` e `approval_kind=OWNER_EXPLICIT_SINGLE_BOUNDED_RUN`;
2. usar ID de autorização válido e aprovação de `ferinbon-cpu`;
3. pinar o `authorized_base_sha` da implementação 004A já mergeada;
4. ser o único path alterado depois desse base SHA;
5. estar em um único commit filho direto do base autorizado;
6. possuir validade temporal explícita;
7. preservar máximo de 7 GETs, zero Drive, zero persistência e zero publicação;
8. preservar fechamento anual e as 8 métricas como `UNKNOWN`.

Sem isso, `STOP_LIVE_NOT_AUTHORIZED` ocorre antes da construção do transporte live e `source_get_count=0`.

## Contrato bounded

- alvo: Limeira/SP, `COD_MUNI=352690`, ano 2025;
- P1–P6: até 6 GETs de identidade;
- fase B: 1 GET adicional somente após P6 com identidade exata;
- máximo absoluto: 7 GETs;
- método `GET`;
- host `www.fnde.gov.br`;
- path Olinda exato pinado pela TASK 002/003;
- timeout 60 s;
- resposta máxima 262144 bytes;
- uma tentativa;
- sem retry, redirect, paginação ou `nextLink`;
- segundo request indevido para mesmo par fase/período => STOP;
- HTTP/content-type/cardinalidade/identidade/schema drift => STOP.

## Semântica preservada

Após a TASK 004A:

- 2025 continua `UNPROVEN_RECENT`;
- P6 continua `CANDIDATE_NOT_PROVEN`;
- `Dados_Gerais_Siope` continua `UNPROVEN_FOR_2025`;
- fechamento anual continua `UNKNOWN`;
- as 8 métricas continuam `UNKNOWN`;
- nenhum Gold 2025 é calculado;
- nenhum claim MDE/Fundeb/compliance/causalidade é autorizado;
- 2026 permanece fora do gate.

## Efeitos remotos da TASK 004A

- `source_get_count=0`;
- `drive_read_count=0`;
- `drive_write_count=0`;
- `publication=false`;
- nenhum body/record financeiro persistido;
- nenhum Bronze/Silver/Gold criado.

## Validação

Os comandos mínimos do `AGENTS.md`, o gate específico e a suíte unitária devem passar no CI do PR final. Enquanto o GitHub Actions do head final não concluir, seu resultado deve ser tratado como `UNOBSERVED`.

## Próximo gate

A TASK 004B será exclusivamente a autorização humana e o primeiro run live bounded. Um comando genérico como `prossiga`, a mera existência da issue ou o clique em `workflow_dispatch` não substituem a autorização explícita para o GET real.
