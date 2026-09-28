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

## Resultado da sessão autorizada

`STOP_AREA_IDENTITY_NOT_PROVEN_BEFORE_TOP_ACTION`. A página oficial carregou e os quatro bindings inline da área Despesa reproduziram o mesmo destino. A identidade AreaOrigin não pôde ser comprovada na superfície DOM disponível. Por isso houve 1 navegação, 0 aberturas de área, 0 consultas, 0 retries e 0 PNCP. Não é consulta negativa nem ausência de empenho. A contagem HTTP total de subrecursos não é exposta pelo navegador. Evidência sanitizada: `docs/evidence/TASK_284_TDA_NAMESPACE_ACQUISITION_0.8.0.json`. Autorização desta sessão consumida; nenhum executor reutilizável ou retry foi habilitado.

## Governança e resposta ao review

O DeepSeek run 36316780069, tentativa 2, revisou o head `8276ac4a96095af7b9a766f7848fa11cece173e1` e retornou CHANGES_REQUESTED (review SHA-256 `544126ca0ed2c9379e90153fdc1dac03a0a667d007683dd9100a2f7a70fa8859`). O parecer afirmou ausência de credential_capability/blockers e habilitação automática. Esses campos já estavam presentes: `PUBLIC_BROWSER_NO_AUTH`, `auto_allowed=false`, blockers explícitos e ausência de workflow/trigger. Não se alega credencial read-only comprovada nem elegibilidade automática.

AGENTS.md §§5 e 7 condiciona **perder o clique humano**, não a classificação de leitura manual pública, à credencial read-only comprovada. A autorização operacional veio do prompt explícito do proprietário (registrada no contrato e na issue #907); não do agente ou do tier. O próprio `evaluate_gate()` retorna `BLOCK/POLICY_AUTO_ALLOWED_FALSE`. Testes agora exercitam o validador central e a mutação `auto_allowed=true`, que para em `STOP_AUTO_READONLY_CREDENTIAL_NOT_PROVEN`. Não se reclassifica leitura para T2/T3 nem se remove o gate para obter aprovação.

Mudanças de política continuam exigindo revisão explícita antes de merge, e o autor não pode fazer self-merge (AGENTS.md §12). A #905 é a PR real, empilhada; a #906 existe apenas para executar os workflows de main sobre o mesmo head e deve ser fechada, nunca mesclada. O review anterior não foi sobrescrito nem declarado PASS; o novo head requer nova revisão. O teste de contexto também mantém um limite fixo separado que rejeita políticas obrigatórias maiores que o orçamento, sem alterar a política de produção.
