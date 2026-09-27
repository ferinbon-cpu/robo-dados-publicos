# CODEX TASK 001 — SIOPE regime discovery 2000–2026

## Objetivo

Preparar, **sem execução remota de dados**, a próxima expansão histórica do pipeline SIOPE de Limeira/SP. A missão deve priorizar a fronteira recente (2025 e 2026) e, em seguida, reconciliar os regimes históricos anteriores a 2016 usando documentação oficial, evidência interna já provada e implementações independentes registradas no projeto.

## Leitura obrigatória antes de trabalhar

Além de `AGENTS.md`, `config/automation_policy.v1.json` e `config/codex_engineer_policy.v1.json`, ler integralmente:

- `docs/research/SIOPE_HISTORICAL_REGIME_EVIDENCE_V1.md`;
- as evidências versionadas da fronteira 2016/2017 e da generalização 2016–2024;
- `MD_00_2_REFERENCIAIS_TECNICOS_PRIOR_ART_E_FONTES_OFICIAIS_V01.md` apenas como referência técnica persistente quando estiver acessível ao ambiente humano/agentic; o PR deve continuar reproduzível apenas com o que está versionado no repositório.

A missão deve reconciliar três classes de evidência:

1. `OFFICIAL_PRIMARY`: FNDE/SIOPE — dicionário, dados analíticos, manuais e downloads históricos;
2. `INTERNAL_PROVEN`: provas do próprio `robo-dados-publicos`;
3. `INDEPENDENT_IMPLEMENTATION`: código externo como `tuffyli/RA_work`.

Implementação externa nunca promove sozinha um contrato operacional.

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

## Fatos e evidências que devem ser preservados

1. A série atualmente provada e persistida cobre 2016–2024.
2. Para o contrato anual já validado, 2016 usa `P1` e 2017–2024 usam `P6`.
3. O PR histórico que corrigiu a fronteira temporal exige regressão explícita contra `2016=P6` e `2017=P1`.
4. A documentação oficial do FNDE deve ser tratada como evidência primária de regime para 2008–2016, mas não como prova automática do schema atual de `Dados_Gerais_Siope`.
5. O mapa inicial deve reconhecer 2008–2015 como **oficialmente documentados para regime anual/P1**, ainda pendentes de prova do recurso/schema/campos/comparabilidade das 8 métricas atuais.
6. Os manuais/downloads oficiais de 2005–2007 devem ser examinados antes de propor qualquer contrato live para esses anos.
7. A implementação `tuffyli/RA_work` usa `f_periodo <- function(ano) ifelse(ano <= 2016, 1, 6)` e tenta anos `2000:2024`; isso é corroboração/pista, não prova do nosso contrato para 2000–2007.
8. 2025 e 2026 não devem ser tratados como equivalentes a 2024 por suposição: schema, períodos disponíveis, fechamento anual e campos necessários precisam ser provados em gate separado antes de live execution.
9. 2026 é exercício corrente e deve permanecer distinguível de anos anuais fechados.

## Entregáveis obrigatórios do PR

### A. Mapa de regimes versionado

Criar uma configuração machine-readable que represente no mínimo:

- `2017–2024`: `PROVEN`, P6 para consolidação anual já validada internamente;
- `2016`: `PROVEN`, P1 anual já validado internamente;
- `2008–2015`: `OFFICIAL_DOCUMENTED_CANDIDATE_RUNTIME`, P1 anual documentado, mas resource/schema/metric contract ainda não provado pelo nosso runtime;
- `2005–2007`: `LEGACY_DOCUMENTED_CANDIDATE`, dependente de reconciliação de manuais/downloads/schema;
- `2000–2004`: `CANDIDATE_EXTERNAL_ONLY` até encontrar corroboração oficial suficiente;
- `2025`: `UNPROVEN_RECENT`, nunca promover por continuidade presumida;
- `2026`: `UNPROVEN_CURRENT_YEAR`, explicitamente provisório/corrente e fora da série anual fechada até gate próprio.

Cada regime deve permitir declarar:

- anos cobertos;
- período esperado/candidato;
- classe e fonte de evidência;
- schema esperado ou desconhecido;
- campos obrigatórios;
- aliases permitidos;
- métricas Gold potencialmente calculáveis;
- métricas não comparáveis;
- cautelas semânticas e release notes relevantes;
- estado de prova (`PROVEN`, `DOCUMENTED`, `CANDIDATE`, `UNKNOWN` ou equivalente fail-closed);
- evidência necessária para promoção futura.

### B. Matriz de reconciliação por fonte

Produzir uma matriz que responda, para cada intervalo/ano relevante:

- qual documento oficial sustenta o regime;
- se a evidência se refere ao `Dados_Gerais_Siope`, outra família SIOPE ou apenas ao sistema desktop legado;
- qual período anual é documentado/candidato;
- quais campos atuais estão comprovados, ausentes ou desconhecidos;
- quais das 8 métricas Gold atuais seriam calculáveis **se** os campos existirem;
- quais métricas podem ter quebra semântica apesar de nomes semelhantes;
- quais correções históricas/release notes exigem regime ou adapter próprio.

A matriz não pode converter ausência de evidência em equivalência.

### C. Gate offline de descoberta

Implementar um gate T0 que:

- não faça rede;
- não use secrets;
- valide o mapa de regimes e a matriz de evidência;
- falhe se 2025/2026 forem promovidos a `PROVEN` sem evidência pinada;
- falhe se 2008–2015 forem marcados como schema atual provado apenas por causa do regime P1 documentado;
- falhe se 2000–2007 forem incluídos em lote live automaticamente;
- falhe se 2026 for confundido com exercício anual fechado;
- preserve `future_batch_execution_authorized=false`;
- preserve separação entre evidência oficial de regime e prova live do resource/schema.

### D. Testes de regressão

Adicionar testes para, no mínimo:

- 2016=P1;
- 2017=P6;
- 2008–2015 não podem virar `PROVEN_CURRENT_SCHEMA` sem evidência interna/live posterior;
- drift de período;
- promoção indevida de 2025/2026;
- promoção indevida de 2005–2007;
- promoção indevida de 2000–2004 com base apenas no loop externo `2000:2024`;
- expansão de lote sem autorização;
- ausência de qualquer dependência de Drive/secrets no gate offline.

### E. Plano dos gates live futuros — apenas desenho

Documentar, sem executar, a sequência preferida:

1. discovery read-only de 2025;
2. verificar existência de Limeira e períodos disponíveis;
3. verificar schema/campos necessários às 8 métricas atuais;
4. decidir se 2025 pode integrar a série anual fechada;
5. discovery separado de 2026 como exercício corrente/provisório;
6. discovery read-only de uma pequena amostra 2008–2015 para testar resource/schema e comparabilidade antes de qualquer batch;
7. somente depois desenhar blocos históricos 2008–2015;
8. 2005–2007 em gate próprio de legado, após reconciliação dos manuais/downloads;
9. 2000–2004 somente se surgir respaldo oficial suficiente além da implementação externa.

Nenhum desses gates live é autorizado por esta TASK 001.

## Critério de pronto

O PR só pode ser declarado pronto se:

- `AGENTS.md`, `config/automation_policy.v1.json` e `config/codex_engineer_policy.v1.json` forem respeitados;
- `docs/research/SIOPE_HISTORICAL_REGIME_EVIDENCE_V1.md` tiver sido incorporado na análise;
- nenhum efeito remoto tiver ocorrido;
- os comandos mínimos de validação tiverem sido executados ou explicitamente marcados como não observados;
- CI obrigatório estiver verde;
- o PR listar claramente o que permanece `DOCUMENTED`, `CANDIDATE` ou `UNKNOWN`;
- nenhuma execução live ou persistência for autorizada pelo próprio agente.

## Resultado esperado

Ao final, o repositório deve estar pronto para uma segunda tarefa humana/agentic separada que implemente o **discovery read-only de 2025** sob gate próprio e, em paralelo, possua um mapa de regimes suficientemente rigoroso para planejar a futura validação 2008–2015 sem repetir a engenharia reversa já documentada. Esta missão não executa nenhum discovery live.
