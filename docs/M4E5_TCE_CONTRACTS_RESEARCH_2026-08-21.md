# M4E.5 — Pesquisa técnica para resolvers TCE-SP e Contratos de Limeira

Data: 21/08/2026

## TCESP

A página pública atual do município de Limeira expõe `Receita Detalhada`, `Despesa Detalhada` e `Restos a Pagar`. O link atual de `Despesa Detalhada` em 2026 aponta para um ZIP municipal anual. A implementação 0.5.5 não codifica esse caminho como regra fixa: abre primeiro a página do município/ano e segue o href cujo texto visível é `Despesa Detalhada`.

A página oficial `APIs` do TCESP documenta a API JSON/XML de despesas somente para 2014–2019, com `evento`, `nr_empenho`, `id_fornecedor`, `nm_fornecedor`, `dt_emissao_despesa` e `vl_despesa`. Por isso a candidata divide o resolver por regime temporal e não extrapola o contrato histórico para 2020+.

## Cadastro municipal de contratos

A superfície pública da Prefeitura apresenta filtros por Ano de Pesquisa, Número do Contrato, Tipo de Documento, Objeto e Fornecedor. A renderização pública observada não fornece contrato técnico estável dos nomes internos dos campos. A 0.5.5 portanto descobre o formulário HTML ao vivo, identifica campos por atributos/contexto e só submete quando ano + contrato/fornecedor são inequívocos.

## Regra metodológica

Um fornecedor encontrado no TCESP ou um contrato encontrado no cadastro municipal é apenas `MATCH_CANDIDATE`. A identidade contrato → empenho/liquidação/pagamento depende de chaves adicionais e gates V16/V17.
