# TASK 283 — dossiê TDA → TCE do empenho 03286-01 / 3286-2026

## Objetivo

A TASK283 fecha, ou delimita de forma reproduzível, a única aresta contábil ainda aberta no caso Contrato 45/2026:

`TDA 03286-01 ↔ TCE 3286-2026`.

Ela é uma tarefa T0/offline empilhada sobre a PR #902 / TASK282. Não executa consulta PNCP, TDA, TCE ou Drive, não publica dados e não atribui pagamento.

## Dependência

Enquanto a PR #902 não estiver incorporada ao `main`, a TASK283 permanece empilhada sobre o head aprovado da TASK282:

`e5c04fb7491eb497b7fc8d38e42b6811d7b2b1bd`.

Após o merge externo da #902, esta PR deve ser retargeted para `main` e revalidada no novo head.

## Estado de entrada

As evidências canônicas provam:

`Contrato 45/2026 → E00010/2026 → TDA 03286-01` — **PROVEN**.

O snapshot TCE-SP contém a coorte qualificada:

- município: Limeira;
- entidade: PREFEITURA MUNICIPAL DE LIMEIRA;
- exercício original: 2026;
- empenho: 3286;
- representação TCE: `3286-2026`;
- estágios observados: empenho, liquidação e pagamento.

Isso **não** prova que `03286-01` e `3286-2026` sejam representações do mesmo identificador contábil.

## Auditoria das TASK219X/Y/Z

A leitura das evidências históricas corrige uma interpretação possível da sequência anterior:

- TASK219X localizou a área detalhada, mas não executou consulta do empenho;
- TASK219Y mapeou controles de filtro, mas não executou consulta;
- TASK219Z reproduziu a estrutura, porém parou em `STOP_EXACT_DETAIL_SUBMIT_BINDING_NOT_UNIQUE`;
- portanto nenhuma das três tarefas consultou oficialmente `3286-2026` no formulário Detalhe do Empenho.

A TASK283 não repete esses experimentos na fase offline.

## Contrato de testemunho positivo

A equivalência só pode ser promovida se um artefato oficial trouxer, na mesma relação documental ou em uma regra oficial de namespace suficientemente explícita:

1. TDA: `03286-01`;
2. número contábil: `3286`;
3. exercício original: `2026`;
4. entidade: `PREFEITURA MUNICIPAL DE LIMEIRA`.

O testemunho deve registrar:

- classe de autoridade: Prefeitura de Limeira, TCE-SP ou AUDESP;
- localizador da fonte;
- SHA-256 do artefato;
- os quatro valores exatos acima.

A mera coincidência entre fornecedor, objeto, valor, data, modalidade ou candidato único nunca satisfaz o contrato.

**Correção de integridade de 26/09/2026:** os quatro valores declarados em um dicionário, mesmo acompanhados de URL oficial e SHA-256 bem formado, não demonstram a relação na fonte. A implementação anterior aceitava esse dicionário como prova; agora toda tentativa termina em `WITNESS_SOURCE_ADAPTER_NOT_IMPLEMENTED`. Não existe adaptador positivo aprovado. Uma futura promoção exige patch revisado com bytes pinados, proveniência oficial, extração determinística e prova da relação, incluindo a semântica do sufixo quando a rota for uma convenção. O contrato não dispõe de flag para habilitar prova.

## Heurísticas bloqueadas

A TASK283 rejeita explicitamente:

- cortar `-01`;
- retirar zero à esquerda como prova de equivalência cross-system;
- inferir 2026 pela data de emissão;
- usar o mesmo fornecedor como chave;
- usar o mesmo objeto;
- usar o mesmo valor;
- usar proximidade temporal;
- concluir identidade porque há um único candidato TCE.

Esses sinais podem corroborar uma identidade já demonstrada, nunca criá-la.

## Fontes offline pinadas

O dossiê consome exclusivamente arquivos versionados:

- TASK219AA — ponte municipal forte;
- TASK219AB — contrato TDA machine-readable;
- TASK219H — coorte TCE 3286-2026;
- TASK219X/Y/Z — histórico de gates do formulário TDA;
- TASK282 — identidade contábil qualificada e controle negativo.

Cada arquivo é pinado pela identidade de blob Git. Drift de qualquer fonte termina em STOP.

## Resultado atual

`UNRESOLVED_MISSING_OFFICIAL_NAMESPACE_WITNESS`.

Isso significa:

- cadeia municipal: provada;
- coorte TCE: observada;
- equivalência TDA → TCE: não provada;
- atribuição de pagamento TCE ao contrato: bloqueada;
- aquisição live autorizada por esta task: não.

## Acervo e pesquisa pública

As buscas no Drive não localizaram os binários. Em 26/09/2026, os três originais foram recuperados do acervo do proprietário e seus SHA-256 conferidos integralmente com a TASK219AA. O registro novo é `docs/evidence/TASK_283_RECOVERED_SOURCE_INSPECTION_0.8.0.json`; os snapshots históricos e os arquivos de origem não foram alterados. Binários, identificadores privados do acervo, fornecedor e valores não foram adicionados ao repositório.

O XLSX Empenhado preserva `Plan1!A20=03286-01`, `B20=E00010/2026` e o contexto `C2=Limeira - Prefeitura`. O Detalhe preserva o filtro `C2=2026`, `C3=03286-01` e o resultado `A6=03286-01`. Os dois arquivos têm uma planilha visível, sem linhas/colunas ocultas, fórmulas, nomes definidos ou relações externas. Nenhuma célula contém o número contábil isolado `3286` ou `3286-2026`. Os metadados OOXML não têm timestamps de criação/modificação: não usar defaults de bibliotecas como datas da fonte. O PDF do contrato não define o sufixo.

Replay local dos dois originais, sem rede ou escrita:

```bash
python -m robo_dados_publicos.research.task283_archive_inspection \
  --empenhado /caminho/ao/export-empenhado.xlsx \
  --detail /caminho/ao/export-detalhe.xlsx
```

O replay confere os hashes antes de interpretar OOXML e emite somente inventário e células permitidas. Os testes usam bytes sintéticos identificados como tais; jamais tratam a fixture como testemunho oficial.

A documentação pública do Portal da Transparência do TCE-SP descreve `nr_empenho` como "Número do empenho" e exemplifica o padrão `44-2015`, mas não fornece uma regra para interpretar o sufixo municipal `-01`. Portanto essa documentação não fecha a aresta.

O schema oficial AUDESP `empenho-JSONSchemaeExemplo_1.zip`, recuperado no estudo anterior, exige `numeroEmpenho` no padrão `^[1-9][0-9]{0,34}$`. Isso define a gramática de destino, não uma transformação do TDA. O modelo oficial 2026 v02, aba `Empenho de Contrato`, B4:H9, liga município, entidade, `codigoContrato`, `numeroEmpenho` e `anoEmpenho`; G8:G9 preveem validação indicativa no balancete da entidade, conta 5.2.2.9.2.01.01. Falta a remessa concreta e o mapeamento oficial do identificador municipal. O exemplo genérico do schema não é um registro de Limeira.

## Execução

```bash
python -m robo_dados_publicos.research.task283_tda_tce_namespace_dossier
python -m unittest discover -s tests -p 'test_task_283*' -v
```

A saída corrente deve permanecer `UNRESOLVED_MISSING_OFFICIAL_NAMESPACE_WITNESS` enquanto nenhum testemunho positivo for materializado.

## Próximo gate se continuar UNRESOLVED

Uma aquisição live posterior deve ser uma operação separada, bounded e materializada antes da execução. Prioridades:

1. TASK284 / issue #907: a sessão autorizada terminou em `STOP_AREA_IDENTITY_NOT_PROVEN_BEFORE_TOP_ACTION`, com uma navegação e nenhuma consulta. A autorização foi consumida; consultar a evidência própria, sem repetir a sessão;
2. obter Nota de Empenho original ou extrato de integração do sistema municipal que vincule `03286-01`, número contábil 3286, exercício original 2026 e Prefeitura de Limeira; a mera resposta a um filtro numérico não basta;
3. alternativamente, obter documentação oficial da convenção aplicável à versão municipal, explicando zeros e `-01`;
4. rota AUDESP: remessa `Empenho de Contrato` desse par número/ano, remessa `Ajuste` que ligue `codigoContrato` ao Contrato 45/2026, identificação oficial dos códigos município/entidade e crosswalk de origem preservando `03286-01`. Não presumir que `45/2026` seja o `codigoContrato`.

A task não deve voltar ao PNCP nem repetir descoberta de fornecedor/contrato.
