# SOFTWARE V01 0.5.5 — CANDIDATE

**Marco:** M4E.5 — primeiros resolvers reais de reconciliação
**Status:** candidata local; não promove a 0.4.0 ativa antes dos gates live.

## Avanço substantivo

A 0.5.5 transforma parte da fila persistente de 0.5.4 em execução real. Dois `target_source` passam a ter resolver próprio:

1. `TCE_SP_DESPESAS`
2. `LIMEIRA_CONTRATOS`

## TCE-SP

Regra temporal explícita:

- 2014–2019: somente a API JSON oficialmente documentada, consultada mês a mês;
- 2020+: o software abre primeiro a página pública `municipio/limeira/<ano>`, localiza exatamente o link visível `Despesa Detalhada` e segue a rota declarada pelo próprio portal;
- o software não adivinha URL de ZIP para anos recentes;
- arquivo ZIP sem CSV ou CSV com schema não reconhecido produz STOP;
- CNPJ é a chave preferencial de fornecedor; nome normalizado é apenas fallback;
- empenho/liquidação/pagamento encontrados para o fornecedor continuam sendo candidatos, não prova de vínculo com o contrato do Jornal Oficial.

## Cadastro municipal de contratos

O portal público expõe busca por ano, número do contrato, tipo de documento, objeto e fornecedor. Como o contrato técnico dos nomes de campos HTML ainda não foi validado ao vivo, o resolver é adaptativo e fail-closed:

- baixa a tela real;
- inspeciona formulários e campos;
- só submete se localizar inequivocamente ano + contrato/fornecedor;
- preserva campos hidden e o botão de pesquisa quando identificável;
- limita-se a uma submissão;
- resultado sem tabela interpretável gera STOP;
- candidatos exigem sinal forte (número de contrato ou CNPJ), não apenas semelhança de texto.

## Executor da fila

Novo comando: `reconciliation-execute`.

- seleciona apenas tarefas `READY_SEARCH`;
- permite filtro por target e limite;
- `--dry-run` não faz rede nem muda status;
- registra `RUNNING` e o resultado final no SQLite;
- registra evento `RECONCILIATION_RESOLVED`;
- erros operacionais viram `RETRY_ERROR`;
- targets ainda não implementados não são executados automaticamente.

## QA local

- compileall: PASS;
- 59/59 testes unitários: PASS;
- 109/109 regressões históricas: PASS;
- TCE 2020+ com descoberta de recurso e ZIP: PASS em servidor-fixture;
- TCE 2019 via contrato API histórico: PASS em servidor-fixture;
- schema desconhecido → STOP: PASS;
- formulário municipal adaptativo + submissão controlada: PASS em servidor-fixture;
- formulário não comprovado → nenhuma submissão: PASS;
- executor persistente e dry-run: PASS;
- consistência de versão pyproject/__version__: PASS;
- secret scan: PASS.

## Gates ainda pendentes

- executar os resolvers contra as fontes reais em runtime externo com rede;
- confirmar o schema real do ZIP `Despesa Detalhada` atual do TCESP;
- confirmar os nomes reais dos campos/form submission do cadastro municipal de contratos;
- validar índice/PDF real do Jornal Oficial;
- executar probe live do TDA;
- gate GitHub Actions/agendamento.

A release ativa permanece 0.4.0.
