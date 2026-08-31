# TASK 022 — revisão offline do pinning do checkpoint real do Jornal Oficial

## Resultado: STOP fail-closed

A TASK 021 ficou corretamente em `STOP_REAL_CHECKPOINT_NOT_PINNED`: a closure da
TASK 018 prova que 12 itens foram descobertos e processados, mas não contém as
cinco propriedades de identidade de cada item. `count=12` não permite detectar
desaparecimento, drift ou duplicidade e, portanto, não é um checkpoint para o
planner da TASK 020.

Esta revisão T0 auditou as evidências versionadas das TASKs 018–021 e tentou ler
somente o artifact histórico sanitizado `task-018-sanitized-operational-evidence`
(artifact `9758450652`, run `33392616951`). O ambiente não possuía autenticação
GitHub e a leitura não se completou. Não houve fallback para o site do Jornal,
Drive ou PDFs. A closure fornece run, batch, head, status, contagens e zero itens
restantes, mas não `edition`, `publication_date`, `document_url`, `source_id` e
`logical_key` por item. Logo, nenhuma das 12 identidades foi reconstruída ou
pinada.

## Proibições e normalização

Não foi presumida uma sequência de edições, calculada data, nem fabricada URL.
A fixture sintética da TASK 021 permanece exclusivamente de teste. O validador
T0 criado nesta task demonstra a regra que um candidato futuro deverá cumprir:
12 itens diretamente observados no artifact histórico, ordem crescente de
edição, `source_id=LIMEIRA_JO_{edition:05d}`,
`logical_key=limeira/jornal_oficial/edicao/{edition}`, data ISO, HTTPS no host
`ecrie.com.br`, proveniência explícita e SHA-256 do payload JSON canônico
(`sort_keys=true`, separadores compactos, UTF-8). Como não existe payload real,
não existe hash de snapshot a registrar.

## Validações e limites

Os testes cobrem candidato válido, 11/13 itens, todas as duplicidades, identidade
derivada divergente, data/URL/host inválidos, proveniência ausente ou sintética,
sequência presumida, origem TASK 018 divergente, integridade, live proof,
schedule e recurrence. O gate também reconcilia `COMPLETE`, 12 processados,
zero restantes e zero falhas com a closure, preserva TASKs 020/021 e os limites
de release.

O resultado é `STOP_REAL_CHECKPOINT_EVIDENCE_INSUFFICIENT` e não autoriza prova
live, workflow, future batch, download, downstream, publicação, checkpoint
advance, schedule ou recurrence. TASK 018 continua consumida e não rerodável.

## Menor ação futura

Disponibilizar o artifact sanitizado já produzido para uma auditoria histórica
read-only autenticada. Se ele contiver diretamente as 12 identidades, uma task
separada poderá piná-las com proveniência e integridade. Se não contiver, o STOP
permanece; não se deve consultar site ou Drive para preencher a lacuna.
