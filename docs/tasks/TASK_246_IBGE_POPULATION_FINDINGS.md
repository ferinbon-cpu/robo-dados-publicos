# TASK246 — denominador municipal IBGE, Limeira, 2016–2025

**Decisão: `NOT_COMPARABLE` para comparação direta das observações adquiridas sob um único contrato homogêneo 2016–2025.** Não é uma impossibilidade de produzir futuramente uma série harmonizada. O inventário contém nove referências anuais observadas e uma ausência explícita em 2023; não é uma série de denominadores aprovada para cálculo.

Base: `main 5b5bf747ece811e4c95fd57d9dfc1cc7d745aeaa`, issue #819. Aquisição pública autorizada, bounded/read-only, em 16/09/2026: 34 artefatos oficiais, 38 tentativas, sem retry automático. Quatro falhas HTTP estão registradas. Não houve cálculo per capita, Gold, promoção, publicação de produto ou alteração do Drive. A identidade oficial é **3526902**, Limeira/SP; **352690** é o código SIOPE, não a chave municipal IBGE. O estado formal permanece `0.7.0 ACTIVE`, `0.8.0 CANDIDATE`; a expressão DRY RUN do pedido não promove nem renomeia a release.

## Prova da incompatibilidade

O [esclarecimento da Diretoria do IBGE](https://www.ibge.gov.br/np_download/novoportal/documentos_institucionais/Esclarecimentos_prestados_pela_DPE_estimativas_das_populacoes_municipais_20251022.pdf), PDF p.3, item d, condiciona comparação temporal municipal à **mesma revisão das projeções** e adverte sobre mudanças de limites. Os itens b–c distinguem Censo de estimativas ajustadas e explicam por que a diferença Censo 2022/estimativa 2025 não mede diretamente crescimento. O documento foi assinado em 26/09/2025; 22/10/2025 é a data no nome do arquivo, não sua referência populacional.

Os regimes efetivamente usados são:

| Referências | Regime comprovado | Evidência oficial |
|---|---|---|
| 2016–2017 | Estimativas municipais, projeção 2013 | [Série TCU 2001–2020](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2020/serie_2001_2020_TCU.pdf), p.1, nota 7 |
| 2018–2021 | Estimativas, revisão 2018, bases 2000/2010 | Mesmo documento, nota 8; [nota 2021](https://biblioteca.ibge.gov.br/visualizacao/livros/liv101849.pdf), PDF pp.6–7, impressas 4–5 |
| 2022 | Censo, referência 01/08/2022 | SIDRA 4714; esclarecimento da Diretoria, item j, p.6 |
| 2023 | Sem observação com referência 2023 nos produtos adquiridos | Catálogo de períodos 6579; relação TCU 2023 explicita população 2022 |
| 2024–2025 | Estimativas, revisão 2024, bases 2010/2022 ajustadas | [Nota 2024](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102112.pdf), PDF pp.6–9; [nota 2025](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102198.pdf), PDF pp.6–11 |

A conclusão decorre da regra oficial aplicada às revisões documentadas, não apenas da ocorrência do Censo ou da ausência de prova. A permanência da fórmula AiBi não preserva seus insumos. A nota 2021 explicita que suas estimativas não incorporam os efeitos da pandemia. As notas 2024/2025 descrevem bases censitárias ajustadas às projeções das UFs, mudança da data para julho, harmonização territorial das bases e ajustes por porte. Esses procedimentos sobre pontos censitários de base **não são uma publicação de estimativas municipais anuais retrospectivas 2016–2023**.

## Produtos e observações

O contrato compara quatro candidatos explicitamente: estimativas municipais, Censo, relação TCU 2023 e projeções Brasil/UF. O produto anual selecionado para as oito observações disponíveis é [SIDRA 6579](https://sidra.ibge.gov.br/tabela/6579), variável **9324**, população residente estimada, **Pessoas**, nível **N6**, sem classificações, referência em **1º de julho**. O Censo usa [SIDRA 4714](https://sidra.ibge.gov.br/tabela/4714), variável **93**, população residente, Pessoas, N6, sem classificações, referência **01/08/2022**. Projeções Brasil/UF não fornecem, por si, uma série anual municipal harmonizada.

Os inteiros abaixo vêm das respostas estruturadas da API oficial, conferidos com células numéricas das planilhas ODS oficiais. Não são transcrição de texto livre. O gate reconstitui o inventário desses snapshots. As oito estimativas conferem com as oito edições ODS pinadas; o Censo 2022 confere numericamente com a relação TCU 2023, sem equiparar suas bases territoriais por inferência.

| Referência | Pessoas | Data de referência | Edição ODS de corroboração / regime |
|---|---:|---|---|
| 2016 | 298.701 | 01/07/2016 | `estimativa_TCU_2016_20170614.ods` / projeção 2013 |
| 2017 | 300.911 | 01/07/2017 | `POP2017_20220905.ods` / projeção 2013 |
| 2018 | 303.682 | 01/07/2018 | `POP2018_20220905.ods` / revisão 2018 |
| 2019 | 306.114 | 01/07/2019 | `POP2019_20220905.ods` / revisão 2018 |
| 2020 | 308.482 | 01/07/2020 | `POP2020_20220905.ods` / revisão 2018 |
| 2021 | 310.783 | 01/07/2021 | `POP2021_20240624.ods` / revisão 2018 |
| 2022 | 291.869 | 01/08/2022 | SIDRA 4714 / Censo 2022 |
| 2023 | **ausente** | **não estabelecida** | TCU 2023 não é população referida a 2023 |
| 2024 | 300.728 | 01/07/2024 | `POP2024_20241230.ods` / revisão 2024 |
| 2025 | 301.292 | 01/07/2025 | `POP2025_20260828.ods` / revisão 2024 |

A [relação oficial TCU 2023](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/Relacao_da_Populacao_dos_Municipios_para_publicacao_no_DOU_em_2023/POP_TCU_2023_Municipios_POP2022_Malha2023.ods) tem **291.869** para Limeira, com referência ao **Censo 2022** e **malha 2023**. Fica em registro suplementar com esses três papéis temporais separados. Não se preenche 2023 por repetição, interpolação ou uso de ano de publicação.

## Vintage e território: o que foi e não foi provado

Há edições antigas e posteriores coexistindo no arquivo oficial. Para Limeira, a edição DOU 2019 adquirida e a edição de 05/09/2022 têm **306.114**; a edição DOU 2025 adquirida e a edição de 28/08/2026 têm **301.292**, também iguais ao SIDRA corrente. Isso prova a igualdade desses valores nas edições identificadas, sem autenticar contemporaneamente os bytes da primeira publicação nem afirmar que o conjunto nacional nunca foi revisado.

O SIDRA informa modificação do período: 2016 em 30/08/2017; 2017–2020 em 05/09/2022; 2021 em 24/06/2024; 2022 na tabela 4714 em 07/05/2026; 2024 em 30/12/2024; 2025 em 28/08/2026. Esses metadados não são data de publicação original nem prova de recálculo da linha de Limeira. `publication_date` permanece `null` onde não estabelecida pelos artefatos adquiridos. Cada observação conserva URL, retrieval, edição e hash; a equivalência com primeira publicação não é presumida.

**Há evidência territorial específica de Limeira:** Anexo 1 da nota 2025, PDF p.16, impressa 14, lista **3526902** entre os municípios com atualização territorial de 01/05/2024 a 30/04/2025, com ou sem remanejamento populacional. A natureza e o impacto populacional desse caso não estão discriminados na lista. Não se pode declarar impacto zero nem comparação 2024/2025 já provada. O mesmo código identifica o município, não garante limites constantes. Ausência de marcador judicial na linha ODS também não prova ausência de decisões históricas.

A nota 2025 contém texto de 2024 na seção territorial do corpo, PDF p.12; a evidência conserva essa inconsistência. A ocorrência de Limeira usa a janela explícita do anexo, corroborada pelo esclarecimento da Diretoria p.1. Nenhum texto oficial foi corrigido silenciosamente.

## Artefato exato necessário para superar o bloqueio

O conjunto mínimo é **um extrato municipal oficial harmonizado 2016–2025 e sua nota de revisão**, ou um contrato oficial de adaptação com todos os inputs municipais necessários. Deve estabelecer:

1. harmonização entre revisões **2013 → 2018 → 2024** e o Censo 2022, especialmente nas fronteiras 2017/2018, 2021/2022 e 2022/2024, com conceito, referência, unidade e vintage comuns;
2. uma observação com **referência real em 2023**, dentro desse contrato;
3. base territorial comum para 2016–2025 e solução explícita para a atualização de Limeira registrada em 2024–2025, com efeito populacional ou ausência de remanejamento comprovados.

Essa é uma especificação de conteúdo ainda não localizado, não o título de um documento cuja existência se presume. Uma nova busca genérica, a planilha TCU 2023, a série Brasil/UF ou repetir o Censo não satisfazem esses requisitos. Mesmo após obtê-los, cálculo per capita depende de tarefa e autorização próprias; G1/G2/G3 financeiros da TASK245 permanecem abertos.

## Artefatos e reprodução offline

- `config/ibge_municipal_population_acquisition.v1.json`: aquisição executada e limites; nenhuma aquisição futura automática.
- `config/ibge_municipal_population_2016_2025.v1.json`: produtos, regimes, regras oficiais e conteúdo necessário ao fechamento.
- `config/ibge_population_denominator_rebase.v2.json`: overlay corrente bloqueado; v1 preservada.
- `docs/evidence/TASK_246_IBGE_MUNICIPAL_POPULATION_2016_2025_0.8.0{,.support,.series}.json`: decisão, fontes/locadores e inventário explícito.
- `docs/evidence/task246_sources/`: sete snapshots JSON completos, decodificados sem alteração de conteúdo; hashes dos bytes de transporte e dos decodificados separados.
- Gate e testes TASK246: integridade documental, população/tabela/unidade/código, datas, regimes, missingness, mutações e proibição de promoção. Nenhum consumidor operacional foi habilitado.

```bash
python scripts/github_task_246_ibge_population_gate.py
python -m unittest discover -s tests -p 'test_task_246*' -v
# Com o pacote de fontes entregue separadamente (34 respostas + 38 recibos):
python scripts/github_task_246_ibge_population_gate.py --raw-custody /caminho/TASK246_IBGE_FONTES_OFICIAIS_2026-09-16.zip
```

O segundo modo confere o ZIP, todos os hashes brutos, decodificação gzip dos JSON e extração das onze planilhas ODS. A interpretação dos PDFs é revisão documental explícita pinada, não inferência automática a partir de palavras-chave. O pacote tem SHA-256 `4a1aff5cf5094901e48c8d647fabdf74b239ef24cbfea237489997c6792fee1e`. Não se faz rede em nenhum desses modos.

Os snapshots TASK243–245, readiness e Gold v4 estão preservados por hash. Estado mantido: financeiro 1–6 `PARTIAL`, per capita 7–8 `NON_COMPARABLE`, Gold 2025 `BLOCKED_NOT_CALCULATED`, série SIOPE fechada 2016–2024. Inclusão de população 2025 no inventário não inclui 2025 na série SIOPE.
