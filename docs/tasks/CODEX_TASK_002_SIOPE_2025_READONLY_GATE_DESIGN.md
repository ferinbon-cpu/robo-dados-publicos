# CODEX TASK 002 — desenho do gate read-only SIOPE 2025

## Decisão desta entrega

Esta entrega é exclusivamente `T0_OFFLINE`: desenha, mas não implementa nem autoriza, um futuro gate `T1_REMOTE_READONLY`. Durante a TASK 002 não houve GET ao FNDE/SIOPE/Olinda, acesso ao Drive, uso de credenciais, persistência, criação de Bronze/Silver/Gold ou publicação.

O contrato machine-readable está em `config/siope_2025_readonly_discovery_design.v1.json` e é validado por `scripts/github_siope_2025_readonly_discovery_design_gate.py`. O mapa histórico permanece como autoridade sobre o estado atual de prova: 2025 continua `UNPROVEN_RECENT`, com período, schema, fechamento anual e elegibilidade para a série fechada desconhecidos.

O comportamento futuro é exercitado sem rede pelo validador puro `robo_dados_publicos/sources/siope_2025_readonly_discovery_offline.py` e por dez fixtures sintéticas e sanitizadas em `tests/fixtures/siope_2025_readonly_discovery`. Elas cobrem ausência de períodos, períodos sem P6, P6 com schema exato, campo ausente, campo extra, duplicidade, identidade divergente, nextLink, drift de transporte e estouro do orçamento declarado. Não contêm valores financeiros nem alegam ser evidência live.

## Perguntas que o futuro gate deverá responder

1. Limeira/SP aparece no recurso candidato para algum dos períodos 1–6 de 2025?
2. Quais períodos são observados, sem interpretar presença como fechamento anual?
3. Se P6 for observado para a identidade exata, o recurso retorna exatamente os 52 campos selecionados do contrato atual?
4. Estão presentes os 11 campos de entrada necessários às 8 métricas aritméticas atuais, sem alias ou drift?
5. Que evidência ainda falta para provar semântica, fechamento anual e comparabilidade?

Nenhuma resposta poderá ser antecipada por continuidade com 2024.

## Desenho bounded do futuro runtime T1

### Fase A — disponibilidade de períodos

O futuro gate, após autorização humana separada, poderá fazer no máximo seis GETs: um para cada P1–P6, sempre filtrado por Limeira (`COD_MUNI=352690`) e selecionando somente os cinco campos de identidade. Cada período poderá ser consultado uma única vez. Zero registros significa apenas `PERIOD_NOT_OBSERVED`; um registro exato significa `PERIOD_OBSERVED_IDENTITY_ONLY`; duplicidade, identidade divergente, redirect, nextLink, drift HTTP/content-type ou estouro de limite exigem STOP.

A fase A não prova schema completo, semântica das métricas ou fechamento anual.

### Fase B — schema condicional

Somente se P6 for observado com identidade exata, o futuro gate poderá fazer um sétimo e último GET, selecionando exatamente os 52 campos já provados para 2024. P6 continua `CANDIDATE_ONLY`: sua presença não prova que 2025 esteja fechado. Campo ausente, extra, renomeado, duplicado ou semanticamente incerto termina em STOP/UNKNOWN; aliases não estão autorizados.

O corpo e os valores poderão ser inspecionados apenas transitoriamente. O desenho não permite persistir body/records, calcular Gold, criar camadas ou publicar. A evidência sanitizada futura deve conter somente contagens, booleanos, schema/campos observados, hashes e estado do gate — nunca valores financeiros ou URLs com query values.

## Resultados permitidos

O futuro gate pode produzir somente `STOP`, `2025_NOT_OBSERVED`, `2025_PERIODS_OBSERVED_SCHEMA_UNKNOWN` ou `2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN`. Mesmo o último resultado não promove 2025, não altera a série 2016–2024 e não autoriza Gold.

Uma promoção futura exige, em PR/gate separado, evidência live pinada e revisada, decisão explícita de fechamento anual e revisão da comparabilidade semântica das 8 métricas. Batch, retry, paginação, recorrência, schedule, Drive, persistência, publicação e conclusões de compliance permanecem bloqueados.

## Próximo gate — não autorizado

O próximo passo proposto é `SEPARATE_HUMAN_AUTHORIZED_T1_SIOPE_2025_READONLY_DISCOVERY_IMPLEMENTATION`. Ele deverá implementar os limites deste desenho e receber autorização própria antes de qualquer efeito de rede. Esta TASK 002 não pode ser usada como autorização operacional.
