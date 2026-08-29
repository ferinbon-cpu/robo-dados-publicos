# TASK 010R — reconciliação da TASK 010 com 009D/009E e handoff humano

## Classificação

Esta é uma revisão **T0/documental**. Não executa rede, não autoriza novo GET, não cria workflow live, não acessa SharePoint e não altera estados semânticos.

Issue de rastreio: `#230`.

## Motivo da reconciliação

A TASK 010 foi aberta para explorar o pacote oficial **`Metadados de 2025 — Municipal`**. A auditoria posterior do histórico completo mostrou que a mesma rota já havia sido tratada pelas TASKs 009A–009D antes da 010:

- TASK 009A preparou o probe bounded do share link oficial;
- TASK 009B observou `HTTP 302` com redirect relativo no share link;
- TASK 009C observou `HTTP 401` no caminho SharePoint resolvido;
- TASK 009D consolidou a rota como dead-end sem prova de acesso público anônimo e proibiu `REPEAT_NEGATIVE_ROUTE_WITHOUT_NEW_OFFICIAL_EVIDENCE`;
- TASK 009E-L-R, depois de 11 fontes oficiais, manteve S1/S2 `NOT_PROVEN` e registrou `future_remote_discovery_authorized=false`.

Por isso, a tentativa registrada na TASK 010B **não constitui nova classe de evidência**, não supera o dead-end da 009D e não autoriza nenhum retry automatizado. Seu resultado deve ser lido apenas como um STOP adicional sem efeito semântico.

## O que permanece válido da TASK 010

A TASK 010A permanece útil como capacidade de segurança offline. Ela adicionou um inspector que:

- calcula SHA-256;
- detecta ZIP por assinatura/magic bytes;
- aplica limite do archive antes de `read_bytes()`;
- limita entradas, tamanho expandido, profundidade e compression ratio;
- rejeita traversal, caminhos absolutos, symlinks e conteúdo ativo;
- não extrai para disco e não executa conteúdo;
- usa fixtures sintéticas geradas em runtime;
- mantém gate T0 com allowlist explícita de imports do inspector e do CLI;
- produz matriz sintética para `NUM_POPU` e os dez aliases financeiros.

Nenhum resultado sintético da 010A constitui evidência SIOPE.

## Interpretação correta da TASK 010B

A evidência `docs/evidence/TASK_010B_SIOPE_2025_METADATA_ACQUISITION_STOP_0.8.0.json` registra que uma autorização one-shot foi consumida sem obtenção do artefato.

Classificação reconciliada:

`NON_NOVEL_REDUNDANT_STOP_NO_SEMANTIC_EFFECT`

Isso significa:

- nenhum byte oficial foi adquirido;
- nenhum conteúdo do pacote foi observado;
- nenhuma nova propriedade da rota SharePoint foi provada além do histórico 009B/009C;
- a política de no-retry da 009D/009E continua prevalecendo;
- não existe autorização implícita para nova tentativa remota.

## Próximo caminho permitido

Sem nova evidência oficial que abra uma rota técnica diferente, o caminho prático é um **handoff humano controlado**, sem nova tentativa automatizada.

Procedimento:

1. o proprietário acessa manualmente a página oficial do FNDE:
   `https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads`;
2. em `Municipal`, clica em `Metadados de 2025`;
3. se o navegador entregar um arquivo **sem exigir login, credenciais ou autenticação institucional**, preserva o arquivo exatamente como recebido;
4. não abrir, executar, extrair, editar ou renomear o arquivo;
5. enviar o arquivo para o ambiente de análise;
6. a partir daí, toda inspeção volta a ser T0/offline com o inspector 010A.

Se houver login, autenticação, cookie institucional ou credencial exigida: **STOP**. Não contornar.

## Proveniência inicial do handoff

Um arquivo recebido dessa forma deve começar como:

`USER_MEDIATED_OFFICIAL_DOWNLOAD_CANDIDATE`

Nunca como `PROVEN_OFFICIAL_BYTES` automaticamente.

Antes de interpretar conteúdo, registrar:

- página oficial de origem;
- rótulo clicado: `Municipal → Metadados de 2025`;
- data/hora aproximada do download;
- nome original informado pelo navegador;
- tamanho em bytes;
- SHA-256 calculado offline;
- tipo real por magic bytes;
- se houve ou não autenticação;
- declaração de que o arquivo não foi modificado entre download e handoff.

A ausência de checksum oficial deve permanecer explícita. A proveniência pode ser fortalecida por sinais internos consistentes de exercício/artefato, mas nunca por nome de arquivo isolado.

## Inspeção offline futura, se houver handoff

O inspector 010A deve então:

1. validar o archive fail-closed;
2. inventariar entradas sanitizadas;
3. procurar identificação interna de exercício 2025 e regime municipal;
4. procurar `NUM_POPU` e os dez aliases financeiros;
5. procurar definição, fonte populacional, regra temporal/vintage e bridges conceituais;
6. produzir matriz item a item;
7. não promover estado canônico automaticamente.

Qualquer promoção de S1, S2, comparabilidade, fechamento ou Gold exige review/gate separado.

## Estado canônico preservado

- `0.7.0 = ACTIVE`;
- `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série anual fechada = `2016–2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Proibições preservadas

- sem retry automatizado do share link 2025;
- sem retry do caminho SharePoint resolvido;
- sem URL inventada;
- sem login automatizado ou reutilização de cookies/credenciais;
- sem execução de instalador ou conteúdo do pacote;
- sem consulta financeira de Limeira;
- sem Gold 2025;
- sem promoção de fechamento/comparabilidade;
- sem 2026;
- sem schedule/recurrence.

## Decisão

`KEEP_009D_009E_NO_RETRY_POLICY_AND_ALLOW_ONLY_OFFLINE_HUMAN_HANDOFF_CANDIDATE`
