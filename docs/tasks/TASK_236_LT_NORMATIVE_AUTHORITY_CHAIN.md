# TASK 236 — cadeia de autoridade de Linguagens e Tecnologias

## Objetivo

Materializar, de forma bounded e auditável, a sequência oficial que levou da estruturação do Currículo de Linguagens e Tecnologias (LT) à sua utilização no processo de atribuição de 2026.

Esta task **não transforma a sequência cronológica em cadeia automática de alterações normativas**. Cada relação só é afirmada quando a fonte oficial a sustenta.

## Cadeia oficial materializada

1. **Portaria SME nº 26, de 23/09/2025** — Jornal Oficial edição 7081, 24/09/2025.
   - O art. 1º designa Comissão Mista com técnicos da SME e membros do CME para estruturar e regulamentar o Currículo de Linguagens e Tecnologias da Rede Municipal de Ensino de Limeira.
   - Papel: ato administrativo preparatório.

2. **Deliberação Conjunta CME/SME nº 001, de 28/10/2025** — Jornal Oficial edição 7107, 30/10/2025, pp. 6–11.
   - Título oficial comprovado: institui a disciplina extracurricular de Linguagens e Tecnologias e o respectivo currículo na Rede Municipal de Ensino de Limeira.
   - Papel: ato normativo curricular primário.
   - O **art. 8º foi recuperado diretamente da publicação primária na p. 9**: a inclusão de LT na jornada regular ajusta para **2 horas-aula semanais** Cultura Corporal e Movimento na Educação Infantil e Arte e Educação Física no Ensino Fundamental, nos âmbitos expressamente indicados pelo artigo.
   - O outline dos demais artigos serve apenas como navegação: ele **não é promovido a texto normativo exato** sem recuperação própria da publicação primária.

3. **Decreto nº 289, de 04/11/2025** — Jornal Oficial edição 7111, 05/11/2025.
   - Cita expressamente a Deliberação Conjunta CME/SME nº 001/2025, “em especial o art. 8º”.
   - Reabre, excepcionalmente, os dias 6 e 7/11/2025 para confirmação ou alteração de jornada dos Professores Especialistas de Arte e Educação Física para 2026.
   - Papel: ato executivo de implementação/modificação do Decreto 259/2025.

4. **Resolução SME nº 08, de 09/12/2025** — Jornal Oficial edição 7139, 16/12/2025.
   - Já materializada integralmente em nível de índice de artigos pela TASK 235.
   - Introduz LT de forma explícita nas regras de composição de jornada e atribuição para 2026.

5. **Página operacional de indicação/atribuição da SME** — snapshot de 11/09/2026.
   - Prova comportamento operacional observado na interface atual.
   - Não é tratada como instrumento de alteração normativa.

## O que esta task prova

- a Portaria 26 inicia uma estrutura de governança SME+CME para o currículo de LT;
- a Deliberação Conjunta 001 formalmente institui a disciplina extracurricular e seu currículo;
- o art. 8º da Deliberação, agora recuperado com proveniência de página, ajusta a carga horária dos componentes indicados para 2 horas-aula semanais em função da inclusão de LT;
- o Decreto 289 reconhece expressamente a Deliberação e cita seu art. 8º ao alterar a janela de confirmação/alteração de jornada para especialistas;
- a Resolução SME 08 incorpora LT ao processo de atribuição 2026;
- a página atual da SME representa a camada operacional corrente.

## O que esta task não prova

- que Portaria → Deliberação → Decreto → Resolução formem uma única cadeia de emendas;
- texto exato dos demais artigos da Deliberação 001 apenas a partir de um outline;
- que a página operacional tenha poder de alterar a Resolução SME 08;
- inexistência de ato posterior que tenha modificado prazo/requisito de formação;
- hash dos PDFs oficiais ainda não custodiados como bytes.

## Divergência de prazo de formação em LT

A TASK 235 registrou divergência entre:

- o texto primário publicado da Resolução SME 08, art. 11 §5º(b), que vincula a comprovação de formação no PSS 04/2025 ao fluxo de indicação/upload; e
- a página operacional atual, que admite apresentação da formação ao Diretor durante o primeiro semestre de 2026.

A recuperação do art. 8º da Deliberação 001 **não resolve essa divergência**: o artigo trata do ajuste de carga horária decorrente da inclusão de LT, não do prazo atual de comprovação de formação do PSS.

A TASK 236 mantém a divergência aberta. A resolução exige localizar ato oficial posterior com texto exato que modifique ou esclareça esse prazo.

## Correção do primeiro CI

O primeiro CI offline da TASK 236 (#1797) parou nos testes unitários porque o teste procurava uma frase minúscula dentro de um enum canônico propositalmente em maiúsculas (`authority_limit`). A correção preserva o enum e passa a validá-lo por igualdade exata. Nenhum dado substantivo foi alterado para acomodar o teste.

## Guardas

- `AUTHORITY_CHAIN_NE_AMENDMENT_CHAIN`
- `DELIB_ARTICLE_TEXT_NE_PROVEN_UNTIL_PRIMARY_TEXT_RECOVERED`
- `DELIB_ART8_PAGE_PROVENANCE_REQUIRED`
- `DELIB_OTHER_ARTICLES_NE_EXACT_TEXT_UNLESS_SEPARATELY_RECOVERED`
- `DECREE289_CROSS_REFERENCE_TO_DELIB_ART8_MUST_BE_PRESERVED`
- `DECREE289_CROSS_REFERENCE_NE_FULL_TEXT_OF_DELIB_ART8`
- `OPERATIONAL_PAGE_NE_NORMATIVE_AMENDMENT`
- `LT_FORMATION_TIMING_DIVERGENCE_REMAINS_OPEN_UNLESS_EXACT_MODIFIER_FOUND`
- `SEARCH_FAILURE_NE_NO_MODIFIER_EXISTS`
- `PRIMARY_TEXT_GT_DERIVED_SUMMARY`
- `NO_BINARY_HASH_INVENTION`
- `NO_CONTEXTUAL_COVERAGE_CHANGE`

Cobertura contextual permanece **38/38**.
