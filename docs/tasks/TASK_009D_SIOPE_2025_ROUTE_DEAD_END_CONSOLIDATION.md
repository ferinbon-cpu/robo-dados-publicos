# TASK 009D — consolidação T0 dos becos sem saída de rota para metadados SIOPE 2025

## Escopo

Esta tarefa é exclusivamente `T0_OFFLINE`. Ela não executa rede, não adiciona workflow live, não lê/escreve Drive, não persiste fonte remota, não publica produto e não autoriza nova execução remota.

O objetivo é transformar em estado auditável duas trilhas de aquisição já investigadas, para impedir repetição de probes sem nova evidência oficial.

## Trilha A — Plataforma Antonieta de Barros

O histórico já versionado do repositório prova que o produto público `Dados Gerais - SIOPE` possui metadata pública de artefato. O endpoint observado pelo runtime foi:

`GET https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/products/data-products/20/artifact-metadata`

O run `32840507830` verificou o endpoint com HTTP 200 JSON e observou somente a estrutura `lastUpdated`, `name`, `path`, `size`; o `path` observado apontava para `exports/SIOPE/`, sem URL HTTP final provada.

A investigação subsequente chegou ao run DOM `32855472741`, que observou o controle `Entrar com gov.br` antes de qualquer rota final de artefato. O contrato consolidado em `config/source_expansion.siope_artifact_access_boundary.json` fixa:

- `artifact_metadata_status = PUBLIC_VERIFIED`;
- `anonymous_export_status = AUTHENTICATION_BOUNDARY_OBSERVED`;
- `acquisition_route_status = UNPROVEN_BEYOND_AUTHENTICATION_BOUNDARY`;
- login automatizado, captura de credenciais/cookies/sessão e bypass permanecem proibidos.

Conclusão: a trilha Antonieta não prova entrega pública anônima do arquivo e não pode ser reutilizada para sintetizar URL de download a partir de `exports/SIOPE/`.

## Trilha B — pacote municipal `Metadados_Mun_2025`

A TASK 008 já consolidou que o índice oficial do FNDE publica um pacote municipal 2025, mas seu conteúdo/layout não foi inspecionado. Assim, a existência do pacote não prova o bridge dos 11 aliases, a definição/vintage de `NUM_POPU` ou continuidade semântica 2025↔2017–2024.

Na TASK 009B, a share URL oficial observada recebeu exatamente um GET bounded e respondeu HTTP 302. O `Location` relativo observado foi:

`/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip`

A resolução URI offline produziu o alvo exato:

`https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip`

Na TASK 009C, exatamente um GET bounded ao alvo resolvido retornou HTTP 401. A autorização one-shot foi consumida. Nenhum corpo ou arquivo foi persistido e nenhuma autenticação foi autorizada.

Conclusão: o caminho SharePoint resolvido não está provado como rota pública anônima de entrega do pacote. Rerun/reuse/autenticação permanecem bloqueados.

## Estado semântico que não muda

- 2025: `PROVEN_STRUCTURAL_RECENT`;
- fechamento anual: `UNKNOWN`;
- comparabilidade semântica: `UNKNOWN`;
- Gold 2025: `UNKNOWN`;
- série anual fechada: 2016–2024;
- 2026: `UNPROVEN_CURRENT_YEAR`.

A coincidência de nomes dos campos não é prova suficiente de identidade semântica.

## Evidência nova mínima admissível

Uma próxima tarefa somente pode ser desenhada se antes for pinada pelo menos uma destas classes de evidência:

1. URL/href oficial FNDE explicitamente publicado para entrega pública não autenticada do mesmo `Metadados_Mun_2025`;
2. conteúdo/layout oficial 2025 já residente no repositório, com proveniência verificável;
3. documentação oficial primária 2025 que defina diretamente os 11 aliases requeridos, incluindo fonte e regra de vintage de `NUM_POPU`.

Mesmo com uma dessas classes, qualquer novo GET exige gate separado, revisão e autorização humana quando aplicável. Esta TASK não concede essa autorização.

## Inferências e ações explicitamente proibidas

- compor URL final a partir de storage path;
- inventar `_layouts/15/download.aspx`;
- acrescentar `?download=1` por inferência;
- automatizar login gov.br;
- capturar/reutilizar credenciais, cookies, OAuth ou sessão;
- repetir rota já negativa sem nova evidência oficial;
- promover fechamento, Gold, série fechada ou 2026;
- inferir equivalência semântica apenas por igualdade/similaridade de nomes.

## Decisão

`KEEP_BLOCKED_UNTIL_NEW_OFFICIAL_EVIDENCE_CLASS_IS_PINNED`

O próximo trabalho permitido é pesquisa documental/repo-resident. Nenhuma rota remota adicional é autorizada por esta consolidação.
