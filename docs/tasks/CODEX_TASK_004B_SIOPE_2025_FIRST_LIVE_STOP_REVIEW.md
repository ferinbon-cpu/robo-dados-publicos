# TASK 004B-R — review offline do primeiro live bounded SIOPE 2025

## Escopo

Esta revisão é exclusivamente T0/OFFLINE. Ela não autoriza novo `workflow_dispatch`, novo GET ao SIOPE/FNDE, Drive, persistência, publicação, Bronze/Silver/Gold, retry, redirect, paginação, recorrência ou schedule.

## Sequência observada

O primeiro dispatch da TASK 004B, run `33201583313`, falhou no preflight por dependência `pypdf` ausente e terminou antes da etapa de autorização e antes da etapa live. Portanto aquele run teve `source_get_count=0`.

Após o hotfix de dependências e o rebind da mesma autorização one-shot, o run `33202186208`, job `98954114713`, executou em `main`, head `5c6a15a1944ad953d7eeba4ae6bfffabc24a1409`, com `run_number=2` e `run_attempt=1`. O preflight passou, o artefato de autorização foi aceito e a execução chegou à fonte.

O primeiro request determinístico do plano — Phase A, ordinal 1, período P1, ano 2025, Limeira/SP — consumiu exatamente um GET e terminou em `STOP_SIOPE_CLIENT_TIMEOUT` após o limite contratual de 60 segundos. O runner parou imediatamente. P2–P6 não foram tentados e a Phase B condicional de schema não foi executada.

Efeitos observados no run #2:

- `source_get_count=1`;
- `drive_read_count=0`;
- `drive_write_count=0`;
- response body não persistido;
- valores de registros não persistidos;
- Bronze/Silver/Gold não criados;
- publication=false;
- retry=false;
- redirect follow=false;
- pagination=false;
- nextLink follow=false.

A autorização one-shot do run #2 é considerada consumida porque houve acesso real à fonte. Qualquer nova tentativa live exige nova autorização explícita do owner em gate separado.

## Correção de telemetria

O log bruto do run #2 registrou o `reason` corretamente como `STOP_SIOPE_2025_T1_TRANSPORT_CLIENT_STOP_SIOPE_CLIENT_TIMEOUT`, mas o campo top-level `status` foi emitido incorretamente como `STOP_LIVE_NOT_AUTHORIZED`. A causa foi o handler genérico do CLI, que aplicava a constante de falha de autorização a qualquer exceção.

A revisão separa agora três classes de STOP:

- falha antes ou durante a validação da autorização: `STOP_LIVE_NOT_AUTHORIZED`;
- falha após todas as guardas de autorização, durante o discovery/transport: `STOP_SIOPE_2025_T1_DISCOVERY`;
- falha inesperada do próprio CLI fora desses dois domínios: `STOP_SIOPE_2025_T1_CLI`.

A correção não altera autorização, request budget, timeout, rota, método, política de retry ou qualquer capacidade de rede.

## Evidência de prefixo parcial

O gerador de evidência do request-plan passa a aceitar qualquer prefixo contíguo válido do plano: `[]`, `[1]`, `[1,2]` até `[1,2,3,4,5,6,7]`. Lacunas, reordenação, ordinais fora do plano e contagem acima do budget continuam fail-closed.

Isso permite representar o run #2 de forma fiel como `executed_ordinals=[1]`, sem inventar execução dos períodos seguintes e sem persistir query values, URL completa com parâmetros ou response values.

A evidência sanitizada está pinada em `docs/evidence/TASK_004_SIOPE_2025_FIRST_LIVE_RUN_2_STOP_0.8.0.json`.

## Investigação do timeout

Há evidência histórica importante, mas limitada: o run `33129373320`, job `98715045661`, executou no mesmo dia um bounded batch histórico com o mesmo `SiopeClient`, timeout de 60 segundos, `max_attempts=1`, sem retry e sem paginação. Foram 5 GETs e 5 registros com sucesso para 2020/P6, 2019/P6, 2018/P6, 2017/P6 e 2016/P1.

Essa comparação sustenta apenas que a família de cliente/transporte e a política bounded de 60 segundos são capazes de funcionar contra a fonte. Ela **não** prova disponibilidade de 2025, não prova que P1 de 2025 deva responder, não prova schema 2025 e não prova encerramento anual ou comparabilidade semântica.

Com apenas um GET de 2025 observado, a causa do timeout permanece:

`UNKNOWN_AFTER_SINGLE_TIMEOUT`

Não há base probatória para classificá-lo como indisponibilidade transitória do FNDE nem como incompatibilidade determinística da rota/query 2025.

## Invariantes após a revisão

- 2016/P1 permanece PROVEN no histórico já pinado;
- 2017–2024/P6 permanecem PROVEN no histórico já pinado;
- 2025 permanece `UNPROVEN_RECENT`;
- 2025/P6 permanece `CANDIDATE_NOT_PROVEN`;
- `Dados_Gerais_Siope` permanece `UNPROVEN_FOR_2025`;
- schema 52 campos de 2025 permanece não observado;
- presença dos 11 Gold input fields em 2025 permanece `NOT_EVALUATED`;
- as 8 métricas Gold de 2025 permanecem `UNKNOWN`;
- annual closure permanece `UNKNOWN`;
- nenhuma promoção automática de 2025 é permitida.

## Próximo gate

Nenhuma nova chamada live faz parte desta revisão. Se, após esta auditoria offline e CI verde, for desejável produzir uma segunda observação, ela deverá ser tratada como nova autorização T1 explícita e bounded. O contrato atual não será silenciosamente relaxado: timeout continua 60 s, sem retry, sem redirect, sem paginação, com fail-closed no primeiro desvio.
