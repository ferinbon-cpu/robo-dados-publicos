# TASK 238 — descoberta direta do JOM com gate separado de conteúdo

## Objetivo

Consolidar no issue canônico #794 o avanço obtido diretamente no arquivo oficial do Jornal Oficial de Limeira, preservando a separação probatória entre **inventário/triagem** e **inspeção do conteúdo primário**.

## Base

A consolidação original derivou do `main` em `96f4a0c81b6b358b9c57019b27bd2e4cc7706efd`, após o merge do PR #795. A segunda onda de clearance primário parte do `main` canônico em `771ef3db2e8356be88bc8f76d3691e41ab24e9c5`, após o PR #798.

## Correção em relação ao trabalho duplicado

O issue #796 e o PR #797 foram encerrados como duplicados. Eles trouxeram um achado válido que foi reconciliado no #794: a janela de 17/12/2025 a 31/01/2026 contém **33 edições consecutivas, 7140–7172**. A edição 7140, assim como a 7141, é de 17/12/2025.

O PR #797 avançava além do gate definido no #794 ao transformar silêncio ou falta de cruzamento na busca textual do portal em fechamento negativo da janela. Esta task não faz essa promoção.

## Regra metodológica

A busca do portal é usada como **triagem de descoberta**. Ela localiza poucos hits amplos e reduz o universo de documentos a inspecionar, mas não substitui leitura do PDF primário.

Portanto:

- `ZERO_HIT` no índice ≠ ausência no conteúdo do PDF;
- inventário completo ≠ conteúdo integralmente inspecionado;
- falha de transporte ≠ ausência jurídica;
- página operacional da SME ≠ ato normativo modificador.

Uma tentativa bounded posterior com navegador-agente terminou em `FAILED_BROWSER_SESSION_CLOSED_AFTER_RETRIES` após repetidas tentativas de operar o formulário do JOM. Essa falha não é evidência negativa. Para esta auditoria, o caminho principal passa a ser exclusivamente fonte primária direta ou espelho estático oficial/confiável, mantendo o navegador-agente fora do gate probatório.

## Inventário bounded

A identidade da janela está fechada em 33 edições, de 7140 a 7172. O manifesto integral está em `config/lt_formation_timing_jom_direct_discovery.v2.json`.

## Matriz de triagem

Os hits amplos relevantes do buscador oficial são:

- `08/2025` → 7142 e 7151;
- `formação` → 7163 e 7168;
- `artigo 11` → 7146;
- `Diretor de Escola` → 7150 e 7172.

A edição 7146 já havia sido inspecionada diretamente na TASK 237 com `target_hit=false`.

A edição 7172 foi contextualizada independentemente: o hit de `Diretor de Escola` aparece na Portaria IPML nº 014/2026, ato de aposentadoria, e não constitui modificador da Resolução SME nº 08/2025.

A edição **7163** foi resolvida por inspeção direta do PDF oficial de 58 páginas. O hit amplo de `formação` corresponde a **“FORMAÇÃO ESPORTIVA DA MODALIDADE ATLETISMO”**, em Termo de Fomento. No documento não foram localizados `Linguagens`, `08/2025`, `PSS 04/2025` ou `primeiro semestre`.

A edição **7150** foi resolvida por fonte primária do IPML. A **Portaria IPML nº 244/2025**, publicada na página **50 de 56** da edição 7150 em 31/12/2025, concede aposentadoria a **Carla Kalid dos Santos Fernandes** no cargo efetivo de **Diretor de Escola**. Esse ato explica diretamente o hit amplo `Diretor de Escola` como conteúdo previdenciário e não possui relação com LT, PSS 04/2025 ou alteração da Resolução SME nº 08/2025.

Fonte primária da 7150:
`https://www.ipml.com.br/site/sites/default/files/imce/segurados-aposentados/aposentadorias/2025/12_dezembro/244_-_carla_kalid_dos_santos_fernandes_-_portaria_244.pdf`

## Gate restante

Restam três edições para inspeção primária focalizada:

`7142, 7151, 7168`.

Há um espelho público da edição 7151 que cobre apenas as páginas internas **2–59 de 125**. A ausência de `08/2025` nesse fragmento não limpa a edição, porque as páginas 60–125 continuam fora daquela representação. Esse material é apenas parcial e não é promovido a prova de ausência.

Até que o gate restante seja concluído:

- `primary_content_closed = false`;
- `bounded_negative_result = false`;
- `modifier_candidate_established = false`;
- `LT_FORMATION_TIMING_DIVERGENCE = OPEN_UNRESOLVED`.

## Próximo passo

Identificar o contexto primário dos dois hits `08/2025` nas edições 7142 e 7151 e do hit `formação` na edição 7168. A prioridade é localizar atos componentes/espelhos estáticos ou representação textual confiável das páginas que contêm esses termos.

A cobertura contextual permanece **38/38**.
