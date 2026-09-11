# TASK 234 — Atribuição de classes/aulas 2026: autoridade oficial e regras operacionais

## Objetivo

Materializar uma camada auditável para `SMELEGAL-018 — Atribuição de Aula`, preservando a diferença entre **norma primária oficial**, **ato modificador oficial** e **página operacional oficial**.

A TASK 222 mantém esse item como `PENDENTE_CORPUS_INTEGRAL`. A TASK 234 não reescreve essa taxonomia retroativamente: ela acrescenta uma materialização oficial bounded para o ano letivo de 2026.

## Base canônica

- `main`: `4eb147a448c5d390fa0675f5dbad7a28a7301315`
- origem: merge da TASK 233 / PR #783
- CI offline pós-merge: run #1792 (`34598111119`) = `success`

## Fontes e precedência

### 1. Decreto Municipal nº 259/2025

Fonte oficial: Legislação Digital de Limeira.

- data: 30/09/2025;
- situação oficial observada em 11/09/2026: `Em vigor`;
- PA nº 34.939/2025;
- fundamento declarado: arts. 31, 32, 33 e 34 da LC 461/2009;
- escopo: inscrições, classificação e atos conexos para atribuição do ano letivo de 2026.

O PDF exportado é texto consolidado/anotado e já identifica os §§ 4º a 7º do art. 1º como incluídos pelo Decreto 289/2025. A própria fonte informa que o texto não substitui a publicação oficial; portanto a TASK não o rotula como fac-símile do Jornal Oficial.

### 2. Decreto Municipal nº 289/2025

Fonte oficial: Legislação Digital de Limeira.

- data: 04/11/2025;
- situação oficial observada em 11/09/2026: `Em vigor`;
- altera diretamente o Decreto 259/2025;
- cria novo período para confirmação/alteração da jornada dos especialistas de Arte e Educação Física para 2026.

### 3. Página operacional da SME

Fonte oficial da Secretaria Municipal de Educação:

`https://sme.limeira.sp.gov.br/indicacao_atribuicao_ps0.php`

A página é explicitamente destinada às indicações de classes/turmas em substituição para o ano letivo de 2026 e cita:

- **Resolução SME nº 08, de 09/12/2025**;
- publicação no Jornal Oficial de Limeira em **16/12/2025**;
- arts. 30, 23, 23 §2º e 11 §5º, b, para regras específicas reproduzidas ou resumidas na própria página.

Essa evidência é forte para provar o uso operacional oficial e as regras efetivamente exibidas. Ela **não** equivale à posse do texto integral da Resolução.

## Resultado materializado

O arquivo `config/education_assignment_2026_authority.v1.json` contém:

- identidade/status das duas normas oficiais;
- 15 regras bounded do Decreto 259/289 com artigo e escopo;
- tabela de pontuação e critérios de desempate;
- 11 regras bounded da página operacional SME;
- identidade/publicação declarada da Resolução SME 08;
- limites explícitos de custódia e vigência;
- exclusão de dados pessoais usados no login da página.

## Semântica de autoridade

A precedência fica:

1. `PRIMARY_NORMATIVE_OFFICIAL_CONSOLIDATED`;
2. `PRIMARY_NORMATIVE_MODIFIER`;
3. `OFFICIAL_OPERATIONAL_PAGE_WITH_EXACT_ACT_CITATIONS`;
4. `DERIVED_SME_LEGAL_COVERAGE_MAP`.

Isso impede que o Cérebro Normativo derivado sobrescreva uma norma oficial atual e, ao mesmo tempo, impede que uma página operacional seja promovida artificialmente a texto integral da Resolução.

## Resolução SME nº 08/2025 — limite deliberado

Nesta task:

- `full_original_custody = NOT_ACQUIRED`;
- não são reconstruídos artigos ausentes;
- não é inferida vigência formal integral apenas porque a SME usa a Resolução na página corrente;
- a futura aquisição exata do Jornal Oficial de 16/12/2025 continua sendo um salto separado.

## Privacidade

A página de indicação usa CPF, data de nascimento e recurso de geolocalização. Nenhum desses dados é coletado ou materializado. A TASK guarda somente regras públicas e metadados normativos.

## Guardas principais

- `CURRENT_SME_OPERATIONAL_PAGE_NE_FULL_RESOLUTION_TEXT`;
- `DECREE259_CURRENT_STATUS_EM_VIGOR`;
- `DECREE289_MODIFIES_DECREE259`;
- `OPERATIONAL_PAGE_EXACT_ACT_CITATION_NE_BINARY_CUSTODY`;
- `NO_INFERENCE_BEYOND_VISIBLE_ARTICLES`;
- `NO_APPLY_2026_RULE_TO_OTHER_SCHOOL_YEARS`;
- `NO_PERSONAL_DATA_MATERIALIZATION`;
- `OFFICIAL_PRIMARY_GT_DERIVED_SME_LEGAL_FOR_CURRENT_RULE`;
- `CONSOLIDATED_EXPORT_NE_OFFICIAL_GAZETTE_REPLACEMENT`;
- `NO_CONTEXTUAL_COVERAGE_CHANGE`.

## Não efeitos

Sem escrita no Drive, sem serving/publicação, sem agendamento/recorrência e sem alteração da cobertura contextual 38/38.
