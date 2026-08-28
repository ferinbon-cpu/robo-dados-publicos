# CODEX TASK 001 — SIOPE regime discovery 2005–2026

## Objetivo

Preparar, **sem execução remota de dados**, a próxima expansão histórica do pipeline SIOPE de Limeira/SP. A missão deve priorizar a fronteira recente (2025 e 2026) e, em seguida, mapear os regimes históricos anteriores a 2016.

## Autoridade desta missão

Esta missão autoriza somente trabalho de engenharia em branch/PR: leitura do repositório, análise de evidências versionadas, documentação, fixtures, código offline, testes e proposta de contratos.

Ela **não autoriza**:

- GET ao SIOPE/FNDE/Olinda ou outra fonte ao vivo;
- leitura do Google Drive com credenciais operacionais;
- qualquer escrita no Drive;
- criação de Bronze/Silver/Gold;
- publicação em `08_OUTPUTS`;
- overwrite, replace ou delete;
- schedule, recurrence, retry ou paginação;
- alteração de ruleset/branch protection;
- leitura, criação ou alteração de secrets;
- conclusão automática de MDE/Fundeb/compliance.

Na dúvida: STOP e registrar a lacuna.

## Fatos já comprovados que devem ser preservados

1. A série atualmente provada e persistida cobre 2016–2024.
2. Para o contrato anual já validado, 2016 usa `P1` e 2017–2024 usam `P6`.
3. O PR histórico que corrigiu a fronteira temporal exige regressão explícita contra `2016=P6` e `2017=P1`.
4. 2025 e 2026 não devem ser tratados como equivalentes a 2024 por suposição: schema, períodos disponíveis, fechamento anual e campos necessários precisam ser provados em gate separado antes de live execution.
5. 2026 é exercício corrente e deve permanecer distinguível de anos anuais fechados.

## Entregáveis obrigatórios do PR

### A. Mapa de regimes versionado

Criar uma configuração machine-readable que represente no mínimo:

- `2017+`: regime bimestral/consolidação anual candidata em P6, sem estender automaticamente para 2025/2026 sem prova;
- `2008–2016`: regime anual/P1 como hipótese de engenharia a validar contra evidência oficial e schema;
- `2005–2007`: legado desconhecido até prova.

Cada regime deve permitir declarar:

- anos cobertos;
- período esperado/candidato;
- schema esperado;
- campos obrigatórios;
- aliases permitidos;
- métricas Gold potencialmente calculáveis;
- métricas não comparáveis;
- cautelas semânticas;
- estado `PROVEN`, `CANDIDATE` ou `UNKNOWN`.

### B. Gate offline de descoberta

Implementar um gate T0 que:

- não faça rede;
- não use secrets;
- valide o mapa de regimes;
- falhe se 2025/2026 forem promovidos a `PROVEN` sem evidência pinada;
- falhe se 2005–2015 forem incluídos em lote live automaticamente;
- falhe se 2026 for confundido com exercício anual fechado;
- preserve `future_batch_execution_authorized=false`.

### C. Testes de regressão

Adicionar testes para, no mínimo:

- 2016=P1;
- 2017=P6;
- drift de período;
- promoção indevida de 2025/2026;
- promoção indevida de 2005–2007;
- expansão de lote sem autorização;
- ausência de qualquer dependência de Drive/secrets no gate offline.

### D. Plano do primeiro gate live futuro

Documentar, sem executar, a sequência preferida:

1. discovery read-only de 2025;
2. verificar existência de Limeira e períodos disponíveis;
3. verificar schema/campos necessários às 8 métricas atuais;
4. decidir se 2025 pode integrar a série anual fechada;
5. discovery separado de 2026 como exercício corrente/provisório;
6. somente depois abrir 2008–2015 em blocos pequenos por regime.

## Critério de pronto

O PR só pode ser declarado pronto se:

- `AGENTS.md`, `config/automation_policy.v1.json` e `config/codex_engineer_policy.v1.json` forem respeitados;
- nenhum efeito remoto tiver ocorrido;
- os comandos mínimos de validação tiverem sido executados ou explicitamente marcados como não observados;
- CI obrigatório estiver verde;
- o PR listar claramente o que permanece `CANDIDATE`/`UNKNOWN`;
- nenhuma execução live ou persistência for autorizada pelo próprio agente.

## Resultado esperado

Ao final, o repositório deve estar pronto para uma segunda tarefa humana/agentic separada que implemente o **discovery read-only de 2025** sob gate próprio. Esta missão não executa esse discovery.
