# TASK 009E — desenho T0 da descoberta documental oficial para semântica dos aliases SIOPE 2025

## Situação de partida

Esta tarefa começa após `main` `9c20f078b68891334aac7abe8b3074c54a374149` e é exclusivamente `T0_OFFLINE`. Nenhuma fonte externa é consultada por este desenho.

A evidência residente no repositório já permite separar com precisão o que está e o que não está provado:

- o Dicionário de Dados SIOPE 2019 fornece definições oficiais históricas para 10 dos 11 conceitos usados pelas oito métricas Gold atuais;
- esse dicionário não prova que os aliases OData observados em 2025 sejam identidade semântica desses campos históricos;
- `NUM_POPU` permanece sem definição oficial primária e sem regra de origem/vintage pinada;
- o runtime atual prova apenas a presença estrutural dos 52 campos em `Dados_Gerais_Siope`;
- o pacote oficial municipal de metadados 2025 é publicado pelo FNDE, mas seu conteúdo não foi inspecionado;
- a rota SharePoint resolvida do pacote já recebeu um único GET autorizado e retornou HTTP 401;
- a trilha Antonieta possui metadata pública, mas o export anônimo chega a uma fronteira `gov.br` antes de qualquer rota final provada.

A TASK 009D congelou esses dois últimos caminhos negativos para impedir repetição sem nova evidência oficial.

## Pergunta S1 — `NUM_POPU`

Uma definição suficiente precisa estabelecer, em fonte oficial primária:

1. o significado do campo;
2. a origem da população usada pelo SIOPE;
3. a regra temporal, ano de referência, data-base ou vintage;
4. a aplicabilidade dessa regra ao recurso/regime corrente ou especificamente a 2025.

Não basta descobrir que o valor parece uma população municipal, coincidir numericamente com alguma série externa ou ser usado por implementações de terceiros.

## Pergunta S2 — bridge dos dez aliases financeiros

O objetivo é localizar fonte oficial aplicável ao regime corrente que conecte, campo a campo, os aliases OData atuais aos conceitos oficiais já definidos historicamente:

- `VAL_RECE_PREV_ATUA`;
- `VAL_RECE_REAL`;
- `VAL_DESP_DOTA_ATUA`;
- `VAL_DESP_EMPE`;
- `VAL_DESP_LIQU`;
- `VAL_DESP_PAGA`;
- `VL_DESP_DOTA_ATUA_EDU`;
- `VL_DESP_EMPE_EDU`;
- `VL_DESP_LIQU_EDU`;
- `VL_DESP_PAGA_EDU`.

A semelhança lexical com os nomes históricos do Dicionário 2019 é pista, não prova.

## Futuro T1 — limites preparados, não autorizados

O desenho admite uma futura sessão documental humana/assistida somente após autorização explícita do proprietário. O orçamento máximo preparado é de 12 URLs oficiais distintas, uma tentativa por URL, método GET e sem retry.

A descoberta deve permanecer restrita a autoridade FNDE e hosts oficiais `gov.br`/`fnde.gov.br`. Ela não pode consultar dados financeiros de Limeira, não pode parametrizar município/ano/período em recurso de dados e não pode reutilizar a rota SharePoint que já retornou 401.

Também continuam proibidos login `gov.br`, cookies, OAuth, credenciais, sessão pessoal, sintetização de URL, download de pacote binário, coleta de registros financeiros, Drive, publicação e qualquer promoção semântica na própria sessão de descoberta.

## Classes de evidência admissíveis

Podem ser aproveitados, após abertura da fonte oficial:

- dicionário oficial corrente ou específico de 2025;
- metadata/layout oficial corrente ou de 2025;
- manual técnico oficial que defina os campos;
- documentação do portal oficial que defina explicitamente um alias;
- documento oficial de release/schema que faça a ponte explícita entre alias corrente e campo histórico.

Um resultado de busca, snippet, implementação de terceiro, coincidência de nome, schema estrutural de 52 campos ou mera existência do pacote não é suficiente sozinho.

## Separação entre descoberta e promoção

Mesmo se S1 ou S2 produzirem evidência forte, a futura sessão documental não pode promover automaticamente 2025 para comparável nem calcular Gold. O resultado deve primeiro ser pinado em evidência sanitizada e submetido a uma revisão T0 independente.

Somente uma revisão posterior poderá avaliar, campo a campo:

- `NUM_POPU` e sua continuidade temporal;
- os 10 aliases financeiros;
- os numeradores/denominadores das oito métricas;
- eventual drift entre 2017–2024 e 2025.

Fechamento anual continua sendo gate independente: prova semântica não prova finalidade da declaração.

## Estado preservado

- 2025: `PROVEN_STRUCTURAL_RECENT`;
- fechamento anual: `UNKNOWN`;
- comparabilidade semântica: `UNKNOWN`;
- Gold 2025: `UNKNOWN`;
- série fechada: 2016–2024;
- 2026: `UNPROVEN_CURRENT_YEAR`.

## Decisão

`DESIGN_READY_REMOTE_DISCOVERY_NOT_AUTHORIZED`

O próximo passo, e somente ele, é uma autorização humana separada para a descoberta documental bounded. Esta TASK 009E não a concede e não adiciona workflow live executável.
