# TASK284 — aquisição unitária do testemunho de namespace

Issue #907. Gate separado da TASK283 T0; autorizado pelo prompt explícito do proprietário de 26/09/2026. Não autoriza execução automática nem consume TASK281. Não há workflow novo.

## Preflight e execução manual

1. Versionar `config/task284_tda_namespace_acquisition.v1.json`; executar testes do gate e preflights de repositório, política e engenheiro antes de navegar.
2. Em uma única sessão pública, navegar uma vez para `https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418`. Não autenticar, repetir navegação ou chamar endpoints diretamente.
3. Revalidar a área Despesa e sua ação oficial, abrir uma vez, identificar Detalhe do Empenho pelo nome/origem da sessão fresca. AreaId histórico não é seletor válido.
4. Observar somente metadados públicos de DOM necessários ao binding; não persistir cookies, tokens, valores ocultos ou HTML bruto. Exigir `FILTEREDIT_<AreaId>_epn`, `FILTERCOMBO_<AreaId>_exe`, labels e opção 2026 únicos dentro de `AREAFILTER_<AreaId>`.
5. Exigir um controle visível de submit e argumento exato do filtro. Argumento apenas AreaId exige documentação/corpo oficial da função que prove a derivação; o validador atual deliberadamente para nessa situação. Não invocar funções adivinhadas ou selecionar o primeiro controle.
6. Só se o binding e a sintaxe numérica forem provados, preencher 2026 e 3286 e submeter uma vez. Sem retries, paginação, download extra, drilldown ou exploração lateral. Persistir apenas observação sanitizada e hashes. Uma falha de acesso ou binding encerra a sessão, não prova inexistência do empenho.

O navegador pode gerar subrequisições de recursos da página. Registrar separadamente navegações/ações explícitas e contagem HTTP quando observável; não declarar total de GETs que a superfície usada não permite medir. Nenhuma requisição PNCP é permitida.

## Interpretação

Um filtro `3286` que retorne `03286-01` não demonstra, sozinho, a convenção contábil. O testemunho precisa relacionar explicitamente representação completa, número contábil, exercício original e entidade, ou explicar a convenção com aplicabilidade ao caso. A TASK283 continua rejeitando dicionários autodeclarados. Qualquer prova futura exige adaptador revisado e mutações de entidade, exercício, número e sufixo. Atribuição de pagamento permanece falsa.

## Alternativa que resolve a lacuna

Obter da Prefeitura a Nota de Empenho original ou o extrato de integração TDA/CN-SIFPM → AUDESP que contenha a relação `03286-01` → `numeroEmpenho=3286`, `anoEmpenho=2026`, entidade Prefeitura de Limeira. Não há URL unitária do documento comprovada. O ponto de entrada oficial acima é um controle de aquisição, não uma URL presumida de download.

Alternativamente, custodiar as remessas reais `Empenho de Contrato` e `Ajuste`, com o mesmo `codigoContrato`, código oficial de município/entidade e referência ao Contrato 45/2026, mais o identificador municipal de origem ou sua regra oficial. O schema AUDESP não contém a regra de remoção de `-01`; ele apenas restringe a gramática de destino. Um exemplo de outro contrato não resolve esta identidade.
