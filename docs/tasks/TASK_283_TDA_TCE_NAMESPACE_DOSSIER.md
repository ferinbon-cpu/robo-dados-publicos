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

Em 26/09/2026, a busca no Drive pelos nomes exatos dos três artefatos operacionais preservados na TASK219AA não localizou os binários. Isso não invalida os hashes ou fatos bounded já canonizados.

A documentação pública do Portal da Transparência do TCE-SP descreve `nr_empenho` como "Número do empenho" e exemplifica o padrão `44-2015`, mas não fornece uma regra para interpretar o sufixo municipal `-01`. Portanto essa documentação não fecha a aresta.

## Execução

```bash
python -m robo_dados_publicos.research.task283_tda_tce_namespace_dossier
python -m unittest discover -s tests -p 'test_task_283*' -v
```

A saída corrente deve permanecer `UNRESOLVED_MISSING_OFFICIAL_NAMESPACE_WITNESS` enquanto nenhum testemunho positivo for materializado.

## Próximo gate se continuar UNRESOLVED

Uma aquisição live posterior deve ser uma operação separada, bounded e materializada antes da execução. Prioridades:

1. recuperar um dos artefatos oficiais TDA já hashados;
2. localizar nota de empenho/exportação oficial que mostre a representação contábil completa;
3. localizar documentação oficial da Prefeitura/TDA que explique o significado de `NNNNN-SS`;
4. alternativamente, localizar registro AUDESP que relacione ajuste/contrato ao empenho com entidade e exercício.

A task não deve voltar ao PNCP nem repetir descoberta de fornecedor/contrato.
