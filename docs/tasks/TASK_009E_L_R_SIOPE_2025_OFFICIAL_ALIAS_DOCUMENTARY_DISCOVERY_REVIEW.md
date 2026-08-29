# TASK 009E-L-R — revisão offline da descoberta documental oficial SIOPE 2025

## Conclusão

A sessão one-shot autorizada em TASK 009E-L foi executada dentro do contrato e não produziu evidência suficiente para promover `NUM_POPU` nem a identidade dos dez aliases financeiros atuais.

O resultado correto permanece fail-closed:

- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `semantic_comparability_status = UNKNOWN`;
- `annual_closure_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN`;
- série anual fechada = `2016–2024`;
- 2026 = `UNPROVEN_CURRENT_YEAR`.

## Contrato observado

A autorização `SIOPE2025-ALIAS-DOC-DISCOVERY-20260828-01` permitia no máximo 12 URLs oficiais distintas. A sessão abriu 11 URLs, uma única vez cada, e parou sem consumir o 12º slot por ausência de alvo oficial suficientemente justificado.

Não houve retry, autenticação, cookies, OAuth, credenciais, reutilização da rota SharePoint 401, login Antonieta/gov.br, consulta financeira de Limeira, parâmetros município/ano/período em endpoint de dados, download de pacote binário, Drive, publicação ou cálculo Gold.

Um endereço histórico do portal de dados FNDE redirecionou para `dados.gov.br`, fora da allowlist exata; o alvo não foi seguido. A rota oficial de FAQ terminou em fronteira de autenticação; não houve login nem nova tentativa.

## S1 — `NUM_POPU`

O Dicionário de Dados SIOPE 2019 não apresentou campo `NUM_POPU`, nem definição de população, fonte oficial da população ou regra de referência temporal/vintage aplicável ao recurso corrente. O tutorial 2024 e as páginas atuais abertas — SIOPE, manuais, base legal/conceitual, notas técnicas e “Mais sobre o Siope” — também não forneceram os quatro elementos necessários ao gate S1.

Logo, não é legítimo interpretar `NUM_POPU` como população IBGE de determinado ano por inferência, mesmo que isso pareça plausível operacionalmente.

## S2 — dez aliases financeiros

O Dicionário 2019 reafirmou os dez conceitos históricos já pinados na TASK 007: previsão atualizada e realização da receita; dotação atualizada, empenho, liquidação e pagamento da despesa; e as quatro contrapartes de despesa com educação.

Nenhuma fonte aberta nesta sessão, porém, publicou uma ponte explícita aplicável ao regime corrente/2025 entre esses conceitos históricos e os aliases atuais `VAL_RECE_PREV_ATUA`, `VAL_RECE_REAL`, `VAL_DESP_DOTA_ATUA`, `VAL_DESP_EMPE`, `VAL_DESP_LIQU`, `VAL_DESP_PAGA`, `VL_DESP_DOTA_ATUA_EDU`, `VL_DESP_EMPE_EDU`, `VL_DESP_LIQU_EDU`, `VL_DESP_PAGA_EDU`.

A semelhança lexical continua sendo pista, não prova.

## Autorização consumida

A autorização era one-shot e está consumida, mesmo tendo sobrado 1 URL no orçamento. Esse saldo não constitui autorização residual para nova busca. Qualquer nova descoberta remota requer novo gate e nova autorização explícita do proprietário.

## Próximo passo

Não repetir busca ampla nos mesmos índices oficiais. Só reabrir uma trilha remota quando houver uma nova classe de evidência concreta, por exemplo:

- documentação oficial nova/atualizada que publique layout/dicionário corrente;
- URL pública oficial direta para conteúdo textual do metadata/layout 2025;
- nota técnica ou manual oficial que defina `NUM_POPU`, sua fonte e vintage;
- documentação oficial do serviço que explicite o mapeamento dos aliases atuais.

Até lá, 2025 permanece estruturalmente provado, mas semanticamente não promovido.
