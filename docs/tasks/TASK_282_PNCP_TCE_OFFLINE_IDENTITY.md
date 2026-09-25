# Investigação da ponte entre contratação e execução financeira

TASK282 • Issue #901 • base main `69954f7532da1457c040b745b1a9551cc3551d18`.

A rota mais curta para um primeiro vínculo com o TCE é completar a prova de identidade de um empenho municipal já conhecido. A pesquisa de documentação pública oficial desta task foi explicitamente solicitada pelo owner no Work/Astra; ela é registrada separadamente do replay e da biblioteca T0/offline. O contrato 45/2026 já está ligado ao processo licitatório E00010/2026 e ao empenho TDA `03286-01` pelas TASK219AA e TASK219AB. Falta provar, com documento oficial, a equivalência desse identificador com `3286-2026` na entidade contábil correta do TCE. Retirar zeros e o sufixo `-01` seria uma hipótese, não uma prova.

Existe também o desenho oficial de uma rota potencialmente escalável que dispensa `linked-contract`: AUDESP Edital → Ajuste → Empenho de Contrato. O layout permite descrever as relações necessárias; não demonstra que os registros de Limeira estejam disponíveis publicamente. A conclusão da ponte PNCP–TCE permanece **UNRESOLVED / EVIDENCIA_INSUFICIENTE**.

## 1 Arquitetura atual

JOM fornece atos e âncoras administrativas; PNCP descreve contratação, itens e histórico; TDA municipal documenta contratos e execução; TCE fornece observações contábeis. Bronze preserva a fonte, Silver normaliza e Gold/serving depende de gates separados. Este trabalho acrescenta pesquisa e código offline, sem mudar o produto publicado.

Preservados: território 69/69; answerability 38/38; JOM–PNCP e DETAIL 8/8; ITEMS 40 e HISTORY 49. TASK274–280 registram a sequência 400, diagnóstico de paginação, 404 e 503, incluindo o teste pareado ITEMS645/linked-contract645 com 503. Isso não demonstra inexistência de contrato. TASK281 permanece inerte. Nenhuma requisição operacional PNCP foi realizada; documentação PNCP foi consultada pelo índice de busca e contratos versionados.

Fontes iniciais: os quatro documentos de estado solicitados no Drive e o main acima. A leitura posterior das TASK187, 216 e 219H/AA/AB foi necessária para identificar o contrato contábil vigente e evitar regredir a uma conclusão histórica já superada. Não houve auditoria geral das tarefas encerradas.

## 2 Inventário de chaves

| Sistema | Identificadores disponíveis | Limite observado |
| --- | --- | --- |
| JOM | ID de evento, edição/página, processo administrativo, edital, contrato, CNPJ, controle PNCP literal | Documento e tipo do ato delimitam o namespace |
| PNCP contratação | numeroControlePNCP, CNPJ, anoCompra, sequencialCompra, numeroCompra, processo, unidade | Sequencial PNCP e número da compra na origem são distintos |
| PNCP contrato | numeroControlePNCP, numeroControlePNCPCompra, tipoContrato, numeroContratoEmpenho, anoContrato | Contrato e compra têm controles próprios; tipo 7 é empenho substitutivo |
| PNCP módulo de empenhos | Empenhos associados a um contrato, descritos no manual 2.6, seção 14 | Não há payload desses registros custodiado para os oito alvos |
| TDA municipal | Contrato/ano, processo licitatório tipado, número municipal de empenho, fornecedor; documentos de liquidação e ordem de pagamento no caso 45 | Exportação contratual foi canonizada na TASK219AB; formato de empenho ainda não equivale ao TCE |
| AUDESP Nova Fase IV | municipio, entidade, codigoEdital, idContratacaoPNCP, codigoContrato, numeroEmpenho, anoEmpenho | Campos de layout; implantação e acesso aos registros reais são questões separadas |
| TCE CSV rico | id_despesa_detalhe, ds_orgao, ano_exercicio, nr_empenho, identificador_despesa, tp_despesa, mes_referencia | Não há coluna explícita de contrato, processo ou controle PNCP |

No contrato vigente da TASK187, `id_despesa_detalhe` identifica a observação e `identificador_despesa` identifica o fornecedor. O segundo não deve ser usado como chave do lançamento. `ds_modalidade_lic` informa modalidade, não número da licitação. A documentação da API antiga descreve `id_fornecedor`, mas o CSV atual tem um contrato próprio com 23 colunas.

## 3 Matriz de compatibilidade campo a campo

F = identidade forte dentro do namespace documentado; C = identidade composta potencialmente forte, dependente do escopo e da relação oficial; R = corroborador contextual; P = pista fraca; I = inutilizável para a identidade pretendida. Uma chave forte de fornecedor não é uma chave forte de contratação.

| Chave de origem | Destino possível | Classe | Condição ou impedimento |
| --- | --- | --- | --- |
| JOM controle PNCP literal | PNCP numeroControlePNCP da compra | F | Controle completo e classe 1; já provado 8/8 |
| CNPJ + ano + sequencial PNCP | Controle da compra | C | Incluir classe 1 e namespace; ano + sequencial isolados são I entre órgãos |
| Controle da compra | numeroControlePNCPCompra do contrato | F | Relação explícita no registro oficial; não usar controle classe 2 como classe 1 |
| Controle da compra | AUDESP idContratacaoPNCP / codigoEdital | C | Veículo PNCP, layout aplicável e registro real; considerar adesão/gerenciadora |
| JOM processo administrativo | PNCP processo | I | No mapeamento literal atual, nenhum dos oito pares é igual; não converter 900.714/2026 em E00147 por palpite |
| Edital / número de pregão | PNCP numeroCompra / TDA processo tipado | C | Edital 202/2026 e pregão 147/2026 são séries diferentes; exigir documento que os relacione |
| Contrato + ano + entidade | TDA contrato / AUDESP ajuste | C | Instrumento tipado, entidade emissora e ano; contrato 45 não é empenho 45 |
| numeroContratoEmpenho | Número contábil de empenho | C | Somente tipo 7. Nos demais tipos, consultar a relação ajuste–empenho |
| AUDESP codigoContrato | codigoContrato do Empenho de Contrato | F | No escopo validado: relação explícita entre dois registros oficiais, com versão e retificação resolvidas |
| Entidade + ano original + empenho | TCE nr_empenho e ds_orgao | C | Crosswalk oficial da entidade e do formato; ano contábil não substitui ano original |
| TDA 03286-01 | TCE 3286-2026 | P | Sufixo e normalização não demonstrados; igualdade do fornecedor não supre a lacuna |
| TCE id_despesa_detalhe | Observação no mesmo snapshot | F | Identifica registro, não contrato nem documento fiscal; entre snapshots preservar proveniência |
| CNPJ do órgão | Entidade AUDESP / ds_orgao | C | Exigir cadastro oficial que relacione os namespaces; nome municipal não identifica a unidade |
| CNPJ do fornecedor | Fornecedor no outro sistema | R | Forte para a pessoa jurídica, não para contrato; preservar letras e zeros. CPF truncado é I para identidade pessoal |
| Objeto | Descrição do contrato ou histórico | P | Similaridade textual nunca promove identidade |
| Valor isolado | Outro valor | I | Estimado, contratado, empenhado e pago têm semânticas diferentes |
| Datas | Publicação, vigência, emissão, mês | R | Compatibilidade temporal, não vínculo. dt_emissao_despesa não prova data do pagamento |
| Fornecedor + objeto + valor + proximidade | Contratação candidata | P | Acumular sinais fracos não cria uma chave forte |
| Chaves tipadas + entidade + relação explícita | Cadeia documental e contábil | C | Exigir testemunho por aresta; rejeitar conflitos e preservar cardinalidade |

## 4 Evidências oficiais e aplicabilidade

[Catálogo oficial da Nova Fase IV](https://www.tce.sp.gov.br/audesp/documentacao/reformulacao-fase-iv-jsonschemas-e-documentacao-xlsx): foram examinados os ZIPs Edital, Licitação, Ajuste e Empenho e o workbook `Novo Modelo da Fase IV_2026_v02_externo.xlsx`. O manifesto JSON da TASK282 registra URLs, instantes de aquisição, tamanhos e SHA-256 dos 12 documentos obtidos, sem incluir credenciais ou IDs privados de Drive.

No workbook, os localizadores relevantes são Edital C8:I9 e C13:I13; Ajuste C12:I14 e C18:I19; Empenho de Contrato C4:H9; Tipo de Contrato A9:B9. O tipo 7 usa número/ano do empenho no próprio ajuste; os outros instrumentos usam o módulo de empenhos associado. A unicidade é qualificada por município e entidade. A checagem contábil aparece como erro indicativo: não é garantia de integridade absoluta dos dados transmitidos.

Há drift documental real: o ZIP de Ajuste possui tab literal que falha em JSON estrito; o schema de Empenho é anterior às revisões do workbook; `idContratacaoPNCP` consta no workbook e não no schema Edital examinado. Não foi ativado um validador de produção baseado em arquivos presumidamente equivalentes.

[Comunicado AUDESP 15/2026](https://www.tce.sp.gov.br/legislacao/comunicado/nova-fase-iv-licitacoes-e-contratos-orgaos-municipais): distingue o Edital em vigor dos demais módulos em testes naquele momento. O comunicado não prova implantação posterior nem disponibilidade pública. [Comunicado 08/2026](https://tce.sp.gov.br/legislacao/comunicado/nova-fase-iv-audesp-adesao-ou-participacao-licitacao-gerenciada-por-outra) esclarece que adesão muda a entidade gerenciadora e o modo de referenciar edital/ata. Recepção autenticada e consulta por protocolo não constituem, por si, uma API pública de pesquisa.

[Layout do AUDESP legado](https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/layout-ajustes-licitacoes.pdf), página 2: há contrato/ano e nota de empenho ou documento similar. O [catálogo de dados](https://transparencia.tce.sp.gov.br/conjunto-de-dados) observado oferece ajustes até 2025; não foi identificado arquivo de ajustes 2026. Não se extrapola o layout antigo para a implantação nova.

[Manual PNCP 2.6, contratos vinculados](https://pncp.gov.br/manual/pt-br/latest/contrato_empenho/consultar_contratos_ou_empenhos_de_uma_contratacao.html) e [seção 14.5, empenhos de contrato](https://pncp.gov.br/manual/pt-br/latest/empenho/consultar_empenhos.html): as duas relações são distintas. O manual foi consultado via conteúdo indexado, sem GET direto ao PNCP; não há hash de bytes adquiridos para essas páginas. O DTO público [SHJordan/api-pncp-php](https://github.com/SHJordan/api-pncp-php/blob/HEAD/docs/Model/RecuperarContratoDTO.md), blob `8a2712d0d6589d41825e9257358cbe4d3ffa0473`, corrobora nomes e nesting, mas não é autoridade semântica nem prova da versão atual.

As páginas oficiais [Licitações de Limeira](https://www.limeira.sp.gov.br/licitacoes) e [Contratos de Limeira](https://www.limeira.sp.gov.br/consultas/contratos/contratos_1) foram examinadas como pontos de navegação. A evidência mais específica já está nas TASK219AA/AB: PDF do contrato, exportações TDA e chave E00010/2026. A busca por nomes exatos dos arquivos no Drive não localizou os binários; isso não invalida a canonização existente nem prova inexistência no acervo.

## 5 Rotas candidatas

| Rota | Parte já sustentada | Proposição ainda necessária |
| --- | --- | --- |
| Municipal TDA | JOM contrato 45 → contrato oficial → E00010/2026 → 03286-01; TASK219AA/AB | 03286-01 e 3286-2026 designam o mesmo empenho na mesma entidade |
| Nova Fase IV | Relações edital → ajuste → empenho descritas oficialmente | Registros reais, implantação aplicável, acesso e crosswalk da entidade |
| AUDESP legado | Layout Ajustes contém contrato e empenho/documento similar | Arquivo temporalmente adequado, instrumento tipado e registros do caso |
| PNCP módulo 14 | Manual descreve empenhos de contrato | Controle do contrato obtido por outra fonte e payload oficial; nenhuma chamada nesta missão |
| Histórico TCE tipado | Alguns históricos citam contratos literalmente | Relação inequívoca, número completo e entidade; mera menção continua candidata |

A rota municipal é prioritária para um piloto maduro. A Nova Fase IV é a melhor arquitetura candidata para escala. O módulo PNCP 14 pode dispensar `linked-contract` se o controle do contrato vier de fonte independente; não resolve a falta desse controle sozinho. Nenhuma rota autoriza paginação, exploração ou retries.

## 6 Falsos positivos demonstrados

O replay do CSV custodiado confirmou 39.779 observações, 6.956 chaves completas de empenho e **682 números/anos compartilhados por mais de um órgão**. O replay e a biblioteca não fazem rede; a aquisição anterior de 12 documentos públicos oficiais é uma etapa de pesquisa separada e explicitamente registrada no manifesto de proveniência. O empenho 1/2026 aparece em Prefeitura, Câmara e Instituto de Previdência. A fixture mínima usa duas dessas entidades e três observações do caso 3286; não publica dados pessoais do exemplo da Câmara.

Os oito pares processo JOM/processo PNCP divergem literalmente. Exemplo: processo administrativo 900.714/2026, edital 202/2026, `numeroCompra=00147`, `processo=E00147` e sequencial PNCP 645 são cinco identificadores com papéis diferentes. Uma regra que remove pontuação não resolve esses papéis.

O mesmo empenho pode ter várias liquidações e pagamentos. A coorte prova pertencimento à chave contábil, mas não qual nota fiscal foi quitada por qual pagamento. Cancelamentos genéricos não são automaticamente abatidos do pago. Adesões, atas com vários fornecedores, retificações e subcontratação exigem relações específicas.

## 7 Lacunas delimitadas

**Caso maduro 45/2026:** a ponte municipal está preservada. O CSV TCE contém os IDs 667130190, 678095929 e 678117536, com empenhado, liquidado e pago em uma coorte da Prefeitura. Falta uma prova oficial de equivalência entre os formatos TDA e TCE, incluindo significado do sufixo `-01`, exercício original e entidade. O valor municipal de R$ 35 mil pago não substitui os R$ 17,5 mil do snapshot TCE até julho. A diferença de cobertura não constitui, sozinha, divergência contábil.

**Oito alvos da TASK264:** sete foram publicados em setembro, após a cobertura TCE observada de janeiro a julho. O controle 69 foi publicado em fevereiro; sua presença nesse intervalo não comprova execução. Todos os encerramentos registrados nos oito DETAIL ficam depois do checkpoint de setembro. A ausência de ocorrências literais dos oito controles/processos nos históricos desse CSV é apenas resultado dessa busca, não prova de inexistência de contratação, empenho ou pagamento.

**Escopo institucional:** CNPJ PNCP, município/entidade AUDESP e nome do órgão no CSV exigem crosswalk oficial, especialmente para administração indireta e adesão. A lista de municípios/entidades indicada no layout é um caminho documental; um código de exemplo do schema não é código de Limeira.

**Granularidade de execução:** falta chave oficial de documento/ordem para ligar uma liquidação individual a um pagamento TCE. Já existem documentos municipais de duas parcelas na TASK219AA, mas isso não fornece automaticamente uma chave estrangeira do registro TCE.

## 8 Hipóteses descartadas

Não se usa fornecedor, valor, descrição, data próxima ou candidato único como identidade de compra. Não se iguala contrato a empenho porque o campo se chama `numeroContratoEmpenho`. Não se interpreta o sequencial PNCP como número de edital. Não se corta `-01` do TDA nem se completa ano ausente por inferência. Não se infere ausência a partir de 404/503, histórico PNCP sem resultado, período TCE antigo ou retorno vazio de exportação municipal.

SICONFI e SIOPE servem à análise fiscal e educacional agregada, mas não acrescentaram uma chave de empenho a esta investigação. Nenhuma consulta operacional a essas fontes foi necessária. SDKs públicos ajudam a entender estrutura; não provam a relação de um registro municipal. O formulário NCWEB anteriormente sem correspondência não invalida a prova TDA posterior.

## 9 Algoritmo de identidade que falha fechado

1. Verificar bytes, hash, origem, versão, data de referência e localizador de cada evidência. Manter os snapshots imutáveis.
2. Criar identificadores tipados: compra PNCP, contrato PNCP, processo administrativo, processo licitatório, contrato municipal, empenho municipal, empenho TCE e observação TCE. Preservar entidade, ano e valores originais.
3. Aceitar uma aresta somente quando um registro oficial liga explicitamente suas duas pontas, ou quando um contrato de dados oficial demonstra equivalência dos namespaces. A origem e o localizador devem sustentar a relação, não apenas os valores isolados.
4. Qualificar o empenho TCE por município, entidade, ano original e número. Rejeitar ID duplicado, fornecedor conflitante no mesmo escopo, estágio desconhecido e sintaxe não suportada. A implementação atual executa esta etapa, sem atribuir pagamentos a compras.
5. Resolver cardinalidade: uma compra pode gerar vários contratos e empenhos. Um empenho compartilhado exige regra documental de alocação antes de atribuir valores por contrato ou item. Não escolher o candidato mais parecido.
6. Manter UNRESOLVED com o nome da aresta ausente. Distinguir relação contratual provada, coorte contábil observada, execução atribuível e pareamento de documentos. São conclusões diferentes.
7. Confirmar fornecedor como verificação posterior; contradição bloqueia, coincidência não cria aresta. Tratar retificações, vigência e anulações explicitamente.

O resolvedor entregue não calcula total contratual, não soma estágios e não deduz data de pagamento de `dt_emissao_despesa`. A ausência de novas arestas não reduz a answerability já canonizada em outras tarefas.

## 10 Fixtures testes e reprodução

Foi incluída uma fixture minimizada com cinco âncoras reais por ordinal e apenas os campos contábeis necessários para reproduzir namespace, estágio e colisão. CNPJ/CPF, valor, descrição da despesa e histórico textual não são persistidos na fixture. Marcadores sintéticos de fornecedor exercitam apenas a regra de consistência. No replay completo, o identificador bruto do fornecedor é usado transitoriamente para detectar contradição dentro da coorte, mas não é emitido no resultado. O replay usa o arquivo já custodiado da TASK187 e não busca uma versão atual na rede.

Os testes cobrem colisão, ausência de entidade, município/ano divergentes, número sem ano, sintaxe TDA não suportada, ID duplicado, conflito de fornecedor, estágio desconhecido, anulação sem estágio, ordenação determinística, bytes alterados, classe PNCP trocada, invariantes de não atribuição, minimização da fixture, ausência de clientes de rede no replay e separação explícita entre pesquisa documental autorizada e runtime T0.

A revisão DeepSeek inicial do head 650521ff identificou um falso positivo de sintaxe causado pela própria redação/sanitização do contexto e também pontos válidos de governança/minimização. A revisão foi respondida no código: o identificador bruto do fornecedor deixou de ser persistido, a fixture foi minimizada, a aquisição documental passou a ser explicitamente separada do replay T0 e foram adicionados testes de ausência de cliente de rede e de proveniência. O head corrigido deve passar novamente pela CI e pela revisão DeepSeek antes de qualquer merge.

```bash
python -m robo_dados_publicos.research.task282_pncp_tce_bridge_audit \
  --ledger-csv /caminho/local/despesas-limeira-2026.csv \
  --check docs/evidence/TASK_282_PNCP_TCE_OFFLINE_AUDIT_0.8.0.json
python -m unittest discover -s tests -p 'test_task_282*' -v
```

SHA-256 CSV: `87b640aa9d854832bdd66b452d8532043e9f27bc12ec638ee77dcb5d8001f152`.
SHA-256 ZIP: `e696c40b1af0e68efca01e8f819cd26c62a3f62881692e0da33d867604d4d11b`.
SHA-256 workbook AUDESP: `3dbd2061d14c0f3eb70adbf87b23d9725014c5e583d69175b7d0598141ee4e5d`.

Fixtures futuras indispensáveis: um testemunho oficial positivo TDA–TCE; dois ajustes distintos com números coincidentes em entidades diferentes; tipo 7 e tipo 1; adesão de outro órgão; retificação conflitante; restos a pagar com exercício original anterior; um empenho com várias notas/pagamentos; chave de pagamento ausente. Exemplos fictícios de schemas não serão tratados como prova de produção.

## 11 Próximas tarefas propostas

**TASK283 proposta — dossiê offline do caso 45/2026.** Entradas exatas: evidências TASK219AA/AB, exportações oficiais ali hashadas e CSV TASK187. Inventariar os campos originais e metadados de `03286-01`, recuperar a documentação do sufixo e a entidade emissora quando já estiverem no acervo. Saída: grafo com as arestas municipais preservadas e um único testemunho de equivalência TDA–TCE, ou rejeição específica desse testemunho. Zero requests PNCP. Não repetir descoberta de fornecedor ou busca de contrato já provados.

**TASK284 proposta — adaptador de testemunho oficial.** Só após materializar a prova: parser determinístico da nota de empenho/exportação ou dos registros AUDESP reais, com crosswalk institucional, versões e localizadores. Critério de aceite: converter ambas as representações para a mesma chave qualificada sem eliminar informação não explicada; uma mutação de entidade, exercício ou sufixo deve impedir a ligação. Escopo inicial de um empenho.

**TASK285 proposta — relação entre documentos de execução.** Com a compra ligada ao empenho, provar liquidação/ordem de pagamento por chave documental oficial, controlar multiplicidade e diferenças de cobertura. Não atribuir percentuais de execução ou pagamentos por item sem regra própria. Os números destas três TASKs são propostas, ainda não issues criadas.

## 12 Próximo grande salto recomendado

Priorizar o caso maduro 45/2026, cujo contrato, processo licitatório, empenho municipal e pagamentos já têm evidência. O objetivo é fechar a equivalência **TDA `03286-01` ↔ TCE `3286-2026`**, e não esperar recuperação do PNCP para descobrir uma relação que a Prefeitura já documenta.

O menor artefato suficiente seria uma nota de empenho oficial ou exportação/cadastro de integração que exponha a identificação municipal, o número contábil 3286, o exercício 2026 e a entidade emissora de forma explícita; alternativamente, um ajuste AUDESP do contrato 45 com seu registro de empenho e crosswalk da entidade. O documento deve permitir resolver o significado de `-01`, ou fornecer uma ligação independente que torne desnecessário normalizá-lo.

O tratamento pode ser inteiramente offline quando esses bytes forem localizados no acervo. A busca realizada não os localizou por aqueles nomes no Drive; por isso a implementação entregue não simula a prova positiva. Para escala posterior, a rota AUDESP reduz a dependência de coincidências entre números de processo.

## 13 Gate live futuro

Nenhum gate live é indispensável para revisar e reproduzir esta entrega. Não foi criado nem consumido gate, e o orçamento PNCP continua em zero. A TASK281 mantém sua finalidade de saúde e sua autorização própria.

Ainda não há um endpoint de download documental unitário identificado para a nota de empenho que falta. Portanto não se propõe um GET executável com URL adivinhada nem uma visita à página inicial como se provasse a identidade. Se o acervo não contiver o testemunho, a próxima task deverá primeiro materializar sua URL oficial ou obter o arquivo do operador, vincular o hash e limitar a aquisição a esse documento. Consultas em lote e exploração de endpoints não fazem parte desta proposta.

## Limites da implementação

O código executável entregue é uma biblioteca offline e um comando de replay, sem workflow novo, sem fetch e sem persistência automática. Isso não apaga a fase anterior de pesquisa: 12 leituras HTTP de documentação pública oficial e leituras de contexto no Drive ocorreram sob a solicitação explícita do owner e estão declaradas separadamente no manifesto. O arquivo de evidência é um resultado de pesquisa submetido à revisão, não promoção de release ou identidade de compra. TASK219AA/AB, TASK281 e snapshots históricos permanecem preservados. CI e a revisão externa exigida por AGENTS.md continuam sendo condições do PR; não há self-merge.
