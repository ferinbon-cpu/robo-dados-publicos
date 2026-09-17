# TASK 253 — canonização do redigest JOM e controles PNCP explícitos

## Objetivo

Canonizar offline o run ao vivo da TASK252 para as edições 7321–7324 e transformar em evidência durável apenas o subconjunto necessário para identidade administrativa:

- 20 anchors fortes já derivados pela TASK252;
- 8 eventos sanitizados que contêm literalmente `PNCP ID`;
- 8 controles PNCP normalizados e vinculados à proveniência do evento.

A TASK253 é `T0_OFFLINE`. Ela não consulta JOM, PNCP, TCE ou Drive.

## Fonte pinada

- implementação TASK252: `33847adbe1efcd6711898c7ce12c6bac5296b7de`;
- runtime head: `4d9023c38e0d9745a36b24a8cd0ff68394c7dfc6`;
- run: `35279271730`;
- job: `105397199842`;
- artifact: `10521364762`;
- ZIP SHA-256: `9b383a295a0f2cab864b5fec994241e483416626af6469c48e8a50addd9f3ca4`;
- bundle SHA-256: `bde6cc8c913a955ec5ce6d26a08451587680f9e4d1691dfae02099748d55a84d`.

O resultado TASK252 é `PASS_COMPLETE_4_DOCUMENT_GENERAL_EVENT_REDIGEST`: 4 downloads, 230.331.629 bytes, 677 eventos, 677 semânticas, 20 anchors e zero escrita remota/publicação/promoção.

## Regra PNCP explícita

Somente texto sanitizado de evento `EDITAL` pode alimentar o parser.

A gramática tolera ruído de espaçamento do PDF, mas exige deterministicamente:

- rótulo literal `PNCP ID`;
- CNPJ `45132495000140`;
- tipo `1`;
- sequência numérica de até seis dígitos, normalizada com zero-padding;
- ano `2026`.

Exemplo:

`PNCP ID : 45132495000140 -1-00646 / 2026`

vira:

`45132495000140-1-000646/2026`.

CNPJ isolado, objeto, data, valor ou similaridade semântica não criam identidade.

## Resultado materializado

A TASK253 preserva oito controles PNCP explícitos:

- `45132495000140-1-000646/2026`
- `45132495000140-1-000639/2026`
- `45132495000140-1-000645/2026`
- `45132495000140-1-000648/2026`
- `45132495000140-1-000655/2026`
- `45132495000140-1-000653/2026`
- `45132495000140-1-000654/2026`
- `45132495000140-1-000069/2026`

Cada linha preserva `event_id`, edição, página, data, `source_id`, URL, SHA-256 do PDF e SHA-256 do trecho sanitizado.

Os 20 anchors tradicionais contêm 18 identidades únicas: 11 de processo e 7 de contrato. Comparados ao índice canônico das 99 edições anteriores, quatro já existiam e 14 são novas. A união projetada passa de 303 para 317 identidades fortes (203 processos e 114 contratos).

## Limite epistêmico

`EXPLICIT_PNCP_ID_IN_OFFICIAL_JOM_TEXT` significa que o próprio Jornal Oficial publicou um identificador PNCP completo associado ao aviso. Isso é um candidato direto de identidade entre sistemas, muito mais forte que similaridade textual.

Ainda permanecem **não provados** nesta tarefa:

- que o registro remoto PNCP resolva atualmente;
- os campos retornados pelo PNCP;
- qualquer cadeia PNCP → contrato/empenho → TCE;
- identidade financeira ou compliance.

## Efeitos proibidos

Continuam em zero:

- rede JOM/PNCP/TCE;
- Drive;
- Bronze/Silver/Gold;
- serving;
- publicação;
- promoção;
- schedule;
- recorrência.

## Próximo gate

`BOUNDED_EXACT_8_PNCP_CONTROL_REMOTE_RESOLUTION_REQUIRES_SEPARATE_AUTHORIZATION`

Esse gate futuro deverá consultar somente os oito controles acima, sem busca, similaridade, rediscovery ou expansão silenciosa de escopo.
