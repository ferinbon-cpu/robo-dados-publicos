# TASK 238 — inventário determinístico da janela JOM para LT

## Objetivo

Substituir a dependência da navegação manual/browser da TASK 237 pelo coletor já existente do próprio projeto (`JornalOficialLimeira.discover_month`) e materializar um gate puro que só reconhece uma janela como inventariada quando dezembro/2025 e janeiro/2026 estiverem completos e reconciliados.

A janela de interesse permanece **17/12/2025 a 31/01/2026** e a divergência `LT_FORMATION_TIMING_DIVERGENCE` permanece **OPEN_UNRESOLVED**.

## O que esta task faz

- reutiliza o índice oficial `https://www.limeira.sp.gov.br/jornaloficial`;
- reutiliza a implementação robots-aware e sem URL guessing de `robo_dados_publicos/journal/official.py`;
- reutiliza o padrão de runtime da TASK 217C;
- registra o inventário já conhecido de rotas oficiais;
- cria `task238_lt_modifier_jom_window.py`, que valida relatórios mensais completos e produz um inventário bounded;
- falha se `reported_total_items` não reconciliar com a quantidade de edições parseadas;
- falha em paginação parcial, duplicidade, host não oficial, HTTP não seguro ou data fora do mês;
- filtra o inventário completo dos dois meses para a janela 17/12/2025–31/01/2026.

## O que esta task NÃO faz

- não executa live discovery neste commit;
- não baixa PDFs;
- não usa nome de arquivo eCrie para inferir edição/data;
- não cria hash de binário não adquirido;
- não declara que uma URL descoberta prova conteúdo;
- não fecha a divergência de LT;
- não transforma ausência de resultado indexado em ausência de ato jurídico.

## Estado documental já conhecido

O portal oficial reporta 23 itens em dezembro/2025 e 22 em janeiro/2026. Na fatia de dezembro da janela foram observadas as edições 7141–7150. A TASK 237 já inspecionou diretamente sete delas (7141, 7143, 7144, 7145, 7146, 7148 e 7149) sem target hit.

Para janeiro, o resultado canônico da TASK 217C e o CSV de alvos da TASK 219 já materializam 12 rotas oficiais exatas, edições 7161–7172. O próprio portal indexa, por exemplo, a edição 7153 em 08/01/2026, mas as dez linhas iniciais de janeiro ainda precisam ser recuperadas pelo `discover_month()` completo em vez de preenchidas por inferência.

Antes de uma nova descoberta mensal, há **19 rotas oficiais exatas conhecidas** e **13 gaps de rota** na janela. Uma tentativa atual de fetch direto dos URLs eCrie conhecidos retornou `target_unreachable`; isso é falha de transporte, não ausência de termo nem invalidação da identidade documental.

## Gate de completude

`PASS_COMPLETE_BOUNDED_WINDOW_INVENTORY` exige simultaneamente:

1. dois relatórios, dezembro/2025 e janeiro/2026;
2. `status == PASS_DISCOVERY` em ambos;
3. `reported_total_items == count == len(editions)`;
4. paginação dentro do limite bounded;
5. identidades e `source_id` sem duplicidade;
6. `logical_key` coerente com a edição;
7. data pertencente ao mês declarado;
8. URL HTTPS em host oficial permitido.

Mesmo após esse PASS, `content_inspection_performed` continua `false`, `modifier_candidate_established` continua `false` e `absence_inference_allowed` continua `false`.

## Próximo passo

Depois que este PR fechar verde, executar uma **descoberta live bounded separadamente autorizada** apenas para dezembro/2025 e janeiro/2026. Canonizar o inventário resultante. Somente depois abrir um gate separado de inspeção de conteúdo primário para os termos da divergência.

## Guardas

- `INDEX_IDENTITY_NE_PDF_CONTENT`
- `DISCOVERED_URL_NE_DOWNLOADED_SOURCE`
- `PARTIAL_DISCOVERY_NE_COMPLETE_MONTH`
- `REPORTED_TOTAL_MISMATCH_NE_COMPLETE_MONTH`
- `TARGET_UNREACHABLE_NE_NO_TARGET_TERM`
- `COMPLETE_WINDOW_INVENTORY_NE_COMPLETE_CONTENT_INSPECTION`
- `NO_URL_GUESSING`
- `NO_BINARY_HASH_INVENTION`
- `LT_FORMATION_TIMING_DIVERGENCE_REMAINS_OPEN_UNLESS_EXACT_PRIMARY_MODIFIER_FOUND`
- `NO_CONTEXTUAL_COVERAGE_CHANGE`
