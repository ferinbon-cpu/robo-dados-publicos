# TASK 238 — descoberta direta do JOM com gate separado de conteúdo

## Objetivo

Consolidar no issue canônico #794 o avanço obtido diretamente no arquivo oficial do Jornal Oficial de Limeira, preservando a separação probatória entre **inventário/triagem** e **inspeção do conteúdo primário**.

## Base

Branch derivada do `main` em `96f4a0c81b6b358b9c57019b27bd2e4cc7706efd`, após o merge do PR #795.

## Correção em relação ao trabalho duplicado

O issue #796 e o PR #797 foram encerrados como duplicados. Eles trouxeram um achado válido que deve ser reconciliado no #794: a janela de 17/12/2025 a 31/01/2026 contém **33 edições consecutivas, 7140–7172**. A edição 7140, assim como a 7141, é de 17/12/2025.

O PR #797, porém, avançava além do gate definido no #794 ao transformar silêncio ou falta de cruzamento na busca textual do portal em fechamento negativo da janela. Esta task não faz essa promoção.

## Regra metodológica

A busca do portal é usada como **triagem de descoberta**. Ela localiza poucos hits amplos e reduz o universo de documentos a inspecionar, mas não substitui leitura do PDF primário.

Portanto:

- `ZERO_HIT` no índice ≠ ausência no conteúdo do PDF;
- inventário completo ≠ conteúdo integralmente inspecionado;
- falha de transporte ≠ ausência jurídica;
- página operacional da SME ≠ ato normativo modificador.

## Inventário bounded

A identidade da janela está fechada em 33 edições, de 7140 a 7172. O manifesto integral está em `config/lt_formation_timing_jom_direct_discovery.v2.json`.

## Matriz de triagem

Os hits amplos relevantes do buscador oficial são:

- `08/2025` → 7142 e 7151;
- `formação` → 7163 e 7168;
- `artigo 11` → 7146;
- `Diretor de Escola` → 7150 e 7172.

A edição 7146 já havia sido inspecionada diretamente na TASK 237 com `target_hit=false`.

A edição 7172 pôde ser contextualizada independentemente: o hit de `Diretor de Escola` aparece na Portaria IPML nº 014/2026, ato de aposentadoria, e não constitui modificador demonstrado da Resolução SME nº 08/2025.

A edição **7163** também foi resolvida por inspeção direta do PDF oficial de 58 páginas. O hit amplo de `formação` corresponde a **“FORMAÇÃO ESPORTIVA DA MODALIDADE ATLETISMO”**, em Termo de Fomento. No documento não foram localizados `Linguagens`, `08/2025`, `PSS 04/2025` ou `primeiro semestre`, portanto esse hit não corresponde ao modificador procurado.

## Gate restante

Restam apenas quatro edições para inspeção primária focalizada:

`7142, 7150, 7151, 7168`.

Até que esse gate seja concluído:

- `primary_content_closed = false`;
- `bounded_negative_result = false`;
- `modifier_candidate_established = false`;
- `LT_FORMATION_TIMING_DIVERGENCE = OPEN_UNRESOLVED`.

## Próximo passo

Adquirir ou obter representação textual primária confiável dessas quatro edições e buscar os alvos LT/PSS/Resolução/prazo. TinyFish não é requisito do caminho principal; navegador-agente fica apenas como fallback caso a fonte oficial imponha interação que não possa ser reproduzida diretamente.

A cobertura contextual permanece **38/38**.
