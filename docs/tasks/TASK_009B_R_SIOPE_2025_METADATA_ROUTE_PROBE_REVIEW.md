# TASK 009B-R — review do primeiro redirect do pacote de metadados SIOPE 2025

## Escopo

Revisão exclusivamente T0/offline do run live bounded #2 da TASK 009B. Nenhuma nova requisição de rede é executada nesta revisão.

## Run observado

- workflow: `.github/workflows/siope-2025-metadata-package-route-probe.yml`
- run id: `33217097796`
- run number: `2`
- attempt: `1`
- head: `ab546a502ec1114ac5e88b05594bee6cbb3e613e`
- authorization id: `SIOPE2025-METADATA-PROBE-20260828-01`

## Resultado sanitizado

O contrato permitia um único GET com `Range: bytes=0-4095`, máximo de 4096 bytes lidos, uma tentativa, 60 segundos, sem retry e sem seguir redirects.

O SharePoint respondeu `HTTP 302`, com `Content-Length: 185`. O robô leu zero bytes de corpo e não seguiu o redirect. O header `Location` observado foi relativo:

`/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip`

O resultado correto foi `STOP_METADATA_PACKAGE_ROUTE_REDIRECT_REQUIRES_NEW_AUTHORIZATION`.

## Resolução offline do próximo alvo

O `Location` começa com `/`, portanto é uma referência relativa de caminho absoluto. A resolução padrão contra a URL inicial HTTPS preserva esquema e autoridade. Assim, sem qualquer novo acesso de rede, o próximo alvo determinístico é:

`https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip`

Essa resolução prova somente a identidade sintática do próximo alvo. Ela não prova que o alvo retorna ZIP, não prova tamanho, hash, conteúdo, aliases, semântica, fechamento anual ou comparabilidade.

## Consumo da autorização

A autorização one-shot foi consumida porque um GET de origem foi efetivamente emitido. Não é permitido rerun, retry ou novo request usando a autorização anterior. Qualquer observação do alvo resolvido exige nova autorização explícita do owner e novo artefato authorization-only.

## Efeitos e invariantes

- GET fiscal/OData: 0;
- consulta operacional de recibo/status de Limeira: 0;
- Drive read/write: 0/0;
- corpo/ZIP persistido: não;
- Bronze/Silver/Gold: não;
- publicação: não;
- série anual fechada: 2016–2024;
- fechamento anual 2025: `UNKNOWN`;
- comparabilidade semântica 2025: `UNKNOWN`;
- Gold 2025: `UNKNOWN`;
- 2026: não promovido.

## Próxima etapa permitida

Preparar em T0 um contrato separado para exatamente um probe bounded do alvo resolvido acima, novamente sem retry e sem seguir novos redirects. O probe deverá observar apenas status HTTP, content type, tamanho/Content-Range, ZIP magic e hash da amostra bounded. A execução permanecerá bloqueada até autorização humana explícita separada.
