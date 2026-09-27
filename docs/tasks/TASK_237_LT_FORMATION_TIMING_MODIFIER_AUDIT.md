# TASK 237 — auditoria do modificador temporal de formação em LT

## Objetivo

Registrar de forma auditável o estado da busca por um ato oficial posterior à publicação da Resolução SME nº 08/2025 que explique a redação operacional atual da SME segundo a qual a formação em Linguagens e Tecnologias para PSS 04/2025 pode ser apresentada ao Diretor de Escola durante o primeiro semestre letivo de 2026.

## Base canônica

`main` em `53b9f3f8140bd2136ef80bb8d9ff4916151d2175`, após TASK 236 e CI offline pós-merge #1802 verde.

## Por que esta task existe

TASK 235 materializou o texto primário da Resolução SME nº 08/2025. TASK 236 materializou a cadeia normativa de Linguagens e Tecnologias. A página operacional atual da SME cita o mesmo Art. 11 §5º(b), mas apresenta um prazo operacional diferente para a comprovação da formação. Essa diferença não pode ser resolvida por inferência.

## Janela bounded investigada

17/12/2025 a 31/01/2026.

A janela **não está fechada** nesta task. Portanto esta task não materializa `NO_CANDIDATE_LOCATED_IN_BOUNDED_WINDOW`.

## Evidência obtida

A execução TinyFish `4fc0515a-cc80-4448-ba93-2916d8d8e910` aplicou a janela oficial e inspecionou edições individuais, incluindo 7172, 7171, 7170, 7169, 7168 e 7166. Ela ficou estacionada no passo 81 ao verificar a edição 7166 e permaneceu `running` sem progresso em consultas sucessivas.

Como fallback, foram inspecionados diretamente PDFs oficiais ecrie das edições 7141, 7143, 7144, 7145, 7146, 7148 e 7149. Nenhum dos alvos de busca foi localizado nesse subconjunto. Buscas indexadas exatas também não localizaram ato oficial posterior; continuaram trazendo principalmente a publicação originária 7139 e a própria página operacional.

## Estado canônico

`OPEN_UNRESOLVED_INCOMPLETE_BOUNDED_SCAN`.

Isso significa somente:

- nenhum modificador oficial posterior foi **estabelecido** pelas buscas concluídas;
- a janela bounded completa ainda não foi fechada;
- o travamento/rate-limit/403/target_unreachable são problemas de transporte, não fatos jurídicos;
- a página operacional pode provar o fluxo atual observado, mas não altera por si só o texto normativo primário;
- a divergência `LT_FORMATION_TIMING_DIVERGENCE` permanece aberta.

## Guardas fail-closed

Nunca converter:

- `NO_INDEXED_CANDIDATE_LOCATED` em “não existe modificador”;
- `SCAN_INCOMPLETE_TRANSPORT_STALL` em resultado negativo completo;
- inspeção parcial de PDFs em fechamento da janela;
- página operacional em instrumento de alteração normativa;
- ausência de hash binário em hash presumido.

## Próximo salto

Descobrir ou reutilizar uma interface direta/reproduzível do acervo do Jornal Oficial — preferencialmente endpoint, manifesto ou lista estruturada — e fechar as edições faltantes da janela sem depender de navegação manual edição por edição.

Cobertura contextual permanece **38/38**; esta task melhora autoridade e proveniência, não cria nova pergunta canônica.
