# TASK 237 — Auditoria bounded de modificador do prazo de formação em Linguagens e Tecnologias

## Objetivo

Investigar, em fonte oficial do Jornal Oficial de Limeira, se existe ato posterior à publicação da **Resolução SME nº 08/2025** que explique a divergência já preservada pelas TASKs 235/236 sobre o momento de comprovação da formação em **Linguagens e Tecnologias** para docentes do PSS 04/2025.

Esta task não parte da premissa de que há ou não há modificador. Ela existe para testar essa hipótese em uma janela oficial bounded e manter a resposta fail-closed.

## Base canônica

`main` de partida: `53b9f3f8140bd2136ef80bb8d9ff4916151d2175` — TASK 236 já mesclada e pós-merge validada.

## Janela primária

- início: **17/12/2025**;
- fim: **31/01/2026**;
- arquivo oficial: `https://www.limeira.sp.gov.br/jornaloficial/`;
- URL oficial filtrada: `https://www.limeira.sp.gov.br/jornaloficial/?dataDe=17%2F12%2F2025&dataAte=31%2F01%2F2026&numeroEdicao=&busca=`;
- total observado no índice oficial para a janela: **33 itens**.

O total de 33 itens prova o universo retornado pelo filtro do arquivo, mas **não prova por si só** que os 33 corpos PDF já foram inspecionados.

## Termos-alvo

A auditoria procura referências a:

- Resolução SME nº 08/2025;
- art. 11 §5º(b);
- PSS 04/2025;
- formação em Linguagens e Tecnologias;
- retificação, alteração, instrução, comunicado ou esclarecimento;
- a redação operacional equivalente a “ao longo do 1º semestre letivo de 2026”.

## Estado deste checkpoint

A execução navegada oficial ainda está marcada como **`SEARCH_IN_PROGRESS`**. O `run_id` canônico é `4fc0515a-cc80-4448-ba93-2916d8d8e910`.

Durante o progresso, foram observadas inspeções de edições como 7142, 7151, 7172, 7171, 7170, 7169, 7168 e 7166. Essa lista é **não exaustiva** e não pode ser convertida em afirmação de cobertura completa da janela.

Buscas de índice/web não trouxeram candidato concreto, mas isso também não constitui prova negativa jurídica.

## Regra de resultado

Há três estados possíveis:

1. **candidato primário localizado** — só conta se houver publicação oficial exata que altere, retifique, complemente ou operacionalize o prazo relevante;
2. **`NO_CANDIDATE_LOCATED_IN_BOUNDED_WINDOW`** — permitido somente após a inspeção bounded estar comprovadamente concluída; significa apenas que nenhum candidato foi localizado na janela inspecionada;
3. **busca incompleta/falha** — não produz conclusão negativa.

Em todos os casos, ausência de achado ≠ ausência de ato jurídico.

## Relação com TASKs 235 e 236

A divergência `LT_FORMATION_TIMING_DIVERGENCE` permanece **`OPEN_UNRESOLVED`** neste checkpoint.

- TASK 235: texto primário da Resolução SME 08/2025;
- TASK 236: cadeia normativa/implementação de LT e art. 8º exato da Deliberação Conjunta 001/2025;
- TASK 237: procura bounded por eventual ato posterior específico sobre o prazo de comprovação da formação.

A página operacional atual da SME prova o fluxo observado, mas **não é tratada como instrumento de alteração normativa**.

## Guardas

- `SEARCH_IN_PROGRESS_NE_BOUNDED_NEGATIVE_RESULT`
- `PARTIAL_EDITION_PROGRESS_NE_COMPLETE_WINDOW_INSPECTION`
- `NO_CANDIDATE_LOCATED_NE_NO_MODIFIER_EXISTS`
- `SEARCH_FAILURE_NE_NO_MODIFIER_EXISTS`
- `OPERATIONAL_PAGE_NE_NORMATIVE_AMENDMENT`
- `PRIMARY_TEXT_GT_OPERATIONAL_PAGE_FOR_NORMATIVE_WORDING`
- `LT_FORMATION_TIMING_DIVERGENCE_REMAINS_OPEN_UNLESS_EXACT_MODIFIER_FOUND`
- `NO_BINARY_HASH_INVENTION`
- `NO_CONTEXTUAL_COVERAGE_CHANGE`

## Gate de promoção

Este checkpoint não deve ser mesclado como resultado final enquanto a execução continuar em `SEARCH_IN_PROGRESS`. Antes do PR final, o config, a evidência e os testes devem ser atualizados para refletir o resultado terminal real da janela.
