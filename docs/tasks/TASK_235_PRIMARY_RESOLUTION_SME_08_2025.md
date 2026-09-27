# TASK 235 — Resolução SME nº 08/2025 em fonte primária

## Objetivo

Promover `SMELEGAL-018 — Atribuição de Aula` da situação em que a TASK 234 conhecia apenas o rastro operacional da Resolução SME nº 08/2025 para uma camada de **fonte normativa primária publicada**.

A TASK 235 **não reescreve retroativamente** a evidência histórica da TASK 234. O antigo `NOT_ACQUIRED` permanece no arquivo anterior como fotografia do estado daquela task; esta task cria um overlay posterior de autoridade.

## Fonte oficial

- Ato: **Resolução SME nº 08, de 09 de dezembro de 2025**;
- publicação: **(RETIFICAÇÃO)**;
- Jornal Oficial do Município de Limeira;
- edição **7139**;
- data de publicação: **16/12/2025**;
- PDF oficial: `https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_15122025182852.pdf`;
- resolução: páginas **168–186 de 203**;
- corpo normativo: **arts. 1º a 34**;
- Anexo I: páginas **184–186**.

O texto da publicação foi recuperado página a página a partir do PDF oficial indexado. O host bloqueou a obtenção direta do binário fora do fluxo do portal; por isso esta task **não inventa SHA-256 nem custódia binária**.

## O que passa a ser materializado

A matriz `config/education_assignment_resolution_08_2025_primary.v1.json` registra:

- identidade e autoridade da publicação oficial;
- índice completo dos 34 artigos, com página e assunto;
- Anexo I com cronograma de 15, 16 e 17/12/2025 e fase PSS 04/2025 em 15–16/01/2026;
- regras selecionadas de alto valor cotidiano para professor/rede;
- reconciliação bounded com a TASK 234;
- divergências que **não podem** ser resolvidas por inferência.

## Regras primárias de maior valor

Entre as regras agora ancoradas diretamente na publicação estão:

- composição de jornada e regras para especialistas de Arte/Educação Física;
- teto de **48 h/a semanais** no contrato PSS 04/2025;
- processo inicial de atribuição e fases do art. 11;
- ordem de atribuição ao longo do ano (art. 13);
- teto de **66 h/a** para cargo + carga suplementar em outra U.E. (art. 14);
- continuidade do atendimento a estudantes com deficiência em Projetos Especiais (art. 19);
- desligamento por **30 dias de ausência** para carga suplementar e PSS, cada qual com sua regra própria (arts. 22 e 23);
- espera de **45 dias** após desistência voluntária do PSS 04/2025 para nova indicação em outra modalidade aprovada (art. 23 §2º);
- avaliação trimestral e consequências para temporários (arts. 24–25);
- vedações de nova atribuição (art. 30);
- recurso em **2 dias úteis**, sem efeito suspensivo ou retroativo (art. 32);
- vigência na publicação, com efeitos retroativos a **06/12/2025** (art. 34).

## Divergência não reconciliada — Linguagens e Tecnologias

A publicação retificada registra, no art. 11 §5º(b), exigência de comprovação de formação de Linguagens e Tecnologias no fluxo de indicação/upload do PSS 04/2025, com anulação da indicação na falta do comprovante.

A página operacional atual da SME, porém, informa que essa formação pode ser apresentada ao Diretor ao longo do **1º semestre de 2026**, citando o mesmo dispositivo.

A TASK 235 registra isso como:

`UNRESOLVED_POSSIBLE_LATER_OPERATIONAL_OR_NORMATIVE_CHANGE`

Não é permitido:

- tratar a página operacional como emenda normativa automática;
- escolher silenciosamente uma das versões;
- afirmar revogação/alteração sem localizar ato modificador oficial.

## Limite de custódia

Esta task prova:

1. identidade da edição e do ato;
2. localização exata do ato no PDF oficial;
3. texto normativo recuperado página por página;
4. proveniência por artigo/página.

Esta task **não prova**:

- hash do arquivo PDF original;
- custódia binária no repositório;
- inexistência de ato posterior modificador;
- que toda instrução operacional da página SME esteja literalmente no texto da Resolução.

## Guardas

- `PRIMARY_PUBLICATION_TEXT_RECOVERED_NE_BINARY_CUSTODY`
- `RETIFICACAO_LABEL_MUST_BE_PRESERVED`
- `ARTICLE_PAGE_PROVENANCE_REQUIRED`
- `NO_UNSEEN_TEXT_RECONSTRUCTION`
- `PRIMARY_EXACT_ARTICLE_GT_OPERATIONAL_PAGE_FOR_NORMATIVE_WORDING`
- `OPERATIONAL_PAGE_MAY_PROVE_CURRENT_WORKFLOW_WITHOUT_AMENDING_NORM`
- `DO_NOT_TREAT_OPERATIONAL_PAGE_AS_AMENDMENT_WITHOUT_OFFICIAL_MODIFIER_TRACE`
- `TASK234_HISTORICAL_PLACEHOLDER_MUST_NOT_BE_SILENTLY_REWRITTEN`
- `BINARY_HASH_MUST_NOT_BE_INVENTED`
- `NO_CONTEXTUAL_COVERAGE_CHANGE`

## Efeito sobre cobertura

Cobertura contextual permanece **38/38**. Esta task melhora a **autoridade e profundidade normativa**, não cria uma 39ª pergunta canônica.
