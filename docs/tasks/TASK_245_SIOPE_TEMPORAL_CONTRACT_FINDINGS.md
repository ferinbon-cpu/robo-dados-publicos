# TASK 245 — contrato público temporal dos dez inputs financeiros

**Conclusão: PARTIAL.** Aquisição documental oficial realizada em 15/09/2026, sobre `main` `e4ecf87afba21717844db5b28415f13d52e1e48c`. O resultado mantém os dez inputs e as seis métricas financeiras em PARTIAL. Os oito artefatos adquiridos não provam uma quebra desses inputs nem fornecem uma cadeia semântica completa.

## O que a aquisição delimitou

1. O [dicionário FNDE de 2019](https://www.fnde.gov.br/phocadownload/sistemas/siope/Manuais/DICIONARIO%20DE%20DADOS%20SIOPE%202019.pdf), página 2, define os dez campos consolidados e declara expressamente a fronteira anual: 2016/P1 e, desde 2017, P6. O [catálogo analítico](https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/arquivos-dados-analiticos) associa esse dicionário aos arquivos consolidados 2008–2016, 2017, 2018 e 2019, atualizados até 01/03/2020. Essa associação identifica o vocabulário dos arquivos; a correspondência com os aliases OData continua pendente.
2. A [documentação pública Olinda v1](https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/documentacao) foi adquirida e sua especificação embutida extraída. Os dez aliases estão presentes: seis são `texto`, quatro são `decimal`. Todos têm título e descrição vazios. A versão `v1` não informa vigência semântica por exercício, unidade monetária ou histórico de mudanças desses campos.
3. O [tutorial oficial de 2024](https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/media/Tutorial_Bsico_Siope_2024_v2.pdf), páginas 21–22 conferidas visualmente, separa receita total, despesa total e Educação/Função 12. A tela de receitas distingue deduções Fundeb, outras deduções e receitas intraorçamentárias. A regra de inclusão desses componentes nos agregados históricos da API não é declarada nessa tela.
4. O [catálogo de versões](https://www.fnde.gov.br/siope/download.do) distingue exercício e versão publicada: por exemplo, 2016/16.0.0.31 foi publicado em 18/10/2023 e 2017/17.0.1.2 em 29/05/2026. Os registros adquiridos contêm correções pontuais, não um changelog semântico exaustivo. Data do exercício, publicação da versão e aquisição do arquivo ficam separadas na evidência.

## Correspondência a comprovar

Os nomes da segunda coluna são literais do PDF, inclusive espaços. A tabela especifica o alvo da prova histórica; não declara identidade por semelhança de nomes. Os conceitos atuais de B2 permanecem aceitos.

| Alias atual | Coluna do dicionário de 2019 | Estágio / escopo atual de referência |
| --- | --- | --- |
| `VAL_RECE_PREV_ATUA` | `VL_RECEITA_PREVISAO_ATUALIZADA` | Previsão atualizada / receita total |
| `VAL_RECE_REAL` | `VL_RECEITA_REALIZADA` | Realizada / receita total |
| `VAL_DESP_DOTA_ATUA` | `VL_DESPESA_DOTACAO_ATUALIZADA` | Dotação atualizada / despesa total |
| `VAL_DESP_EMPE` | `VL_DESPESA_EMPENHADA` | Empenhada / despesa total |
| `VAL_DESP_LIQU` | `VL_DESPESA_LIQUIDADA` | Liquidada / despesa total |
| `VAL_DESP_PAGA` | `VL_DESPESA_PAGA` | Paga / despesa total |
| `VL_DESP_DOTA_ATUA_EDU` | `VL_DOTACAO_ATUALIZADA EDUCACAO` | Dotação atualizada / Função 12 |
| `VL_DESP_EMPE_EDU` | `VL_DESPESA_EMPENHADA EDUCACAO` | Empenhada / Função 12 |
| `VL_DESP_LIQU_EDU` | `VL_DESPESA_ LIQUIDADA_EDUCACAO` | Liquidada / Função 12 |
| `VL_DESP_PAGA_EDU` | `VL_DESPESA_PAGA_EDUCACAO` | Paga / Função 12 |

## Três proposições restantes

| Proposição | Intervalo e conteúdo exatos |
| --- | --- |
| G1 — identidade temporal | 2016/P1 e 2017–2019/P6: ponte oficial coluna dos consolidados ↔ alias OData. 2020–2023/P6: definição aplicável de alias, conceito e estágio. 2024/P6: aplicabilidade dos aliases além dos rótulos da interface. Todos devem ser compatíveis com B2/2025. |
| G2 — unidade e escala | 2016/P1 e 2017–2024/P6: moeda, multiplicador e valores nominais/ajustados, explicitamente compatíveis com 2025. Tipos `texto`/`decimal` não resolvem essa proposição. |
| G3 — fronteira de agregação | 2016/P1 ↔ 2017/P6 e sequência até 2025: bruto/líquido, deduções Fundeb/outras, intraorçamentárias, perímetro da administração consolidada e despesas do exercício/restos a pagar. Função 12 deve permanecer distinguida do indicador legal MDE. |

**Menor entrega oficial capaz de fechar as três:** um dicionário ou nota pública FNDE/SIOPE de compatibilidade temporal de `Dados_Gerais_Siope`, com essa tabela de dez campos e regras de unidade/escopo/estágio, cobrindo intervalos exaustivos de exercícios/versões e indicando compatibilidade ou mudanças em relação a 2025. Trata-se da especificação de um documento necessário, ainda não localizado. Uma cadeia equivalente de documentos versionados também serve. Código CML/XML/Delphi ou fórmula interna não é requisito.

Os [metadados por exercício](https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads) e os [manuais municipais de 2016/2018](https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/manuais-do-siope) são artefatos oficiais identificados que podem apoiar a resposta. O metadado 2017 retornou HTTP 401; os links legados desses dois manuais, 404; o cabeçalho do consolidado 2008–2016 não pôde ser lido pelo transporte FTP disponível. Nenhum desses resultados é evidência de quebra ou inexistência de documentação. Outros pacotes anuais não foram presumidos inacessíveis.

As mudanças de classificação de precatórios Fundef e de tratamento dos indicadores legais 2016/2017 encontradas nas [notas oficiais](https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/notas-tecnicas) não demonstram, por si, uma quebra nos dez agregados desta missão.

## Materialização e validação

- Evidência: [TASK245 JSON](../evidence/TASK_245_SIOPE_OFFICIAL_TEMPORAL_CONTRACT_ACQUISITION_0.8.0.json), com lacunas por alias/intervalo, URLs, datas, versões e SHA-256 dos oito artefatos.
- Suporte revisado: [extrações e localizadores](../evidence/TASK_245_SIOPE_OFFICIAL_TEMPORAL_CONTRACT_ACQUISITION_0.8.0.support.json).
- Contrato financeiro corrente: [v2](../../config/siope_historical_financial_semantic_versioning.v2.json). A v1 e TASK241/242/244 permanecem intactas.
- Gate: `python scripts/github_task_245_official_temporal_contract_gate.py`. Avalia dimensões por alias/ano e propaga lacunas ou quebra positiva somente às métricas dependentes. Neste snapshot, aceita apenas as proposições temporais efetivamente revisadas; acrescentar flags de aprovação não cria prova.
- Testes: `python -m unittest discover -s tests -p test_task_245_official_temporal_contract.py -v`. Incluem mutações de todos os aliases/estágios, anos, dimensões, hashes, fontes, dependências, P1/P6, unidade e autorizações; casos sintéticos de cobertura completa, lacuna unitária e quebra positiva exercitam o avaliador sem autorizar promoção.

Preservados: 0.7.0 ACTIVE; 0.8.0 CANDIDATE; série 2016–2024; Gold 2025 BLOCKED_NOT_CALCULATED; métricas 7–8 NON_COMPARABLE sob o contrato atual. A aquisição não cria autorização futura, cálculo, publicação, recorrência ou alteração do Drive.
