# ROBO_CODEX — Engenheiro de PR 0.8.0

## Decisão arquitetural

O primeiro estágio do ROBO_CODEX usa **Codex Cloud autenticado pela conta ChatGPT**, conectado ao repositório GitHub. Não usa `openai/codex-action`, não requer `OPENAI_API_KEY` no GitHub e não recebe qualquer credencial operacional do Google Drive.

A função do agente é engenharia de software: analisar, implementar, testar e propor alterações em branch/PR. A função de autorizar efeitos remotos continua pertencendo à política, aos gates e ao owner.

## Fluxo

1. Owner cria/seleciona uma tarefa de engenharia.
2. Codex lê `AGENTS.md`, `config/automation_policy.v1.json` e `config/codex_engineer_policy.v1.json`.
3. Codex trabalha em branch isolada.
4. Codex executa validações offline compatíveis com a tarefa.
5. Codex produz PR, nunca escreve diretamente em `main`.
6. GitHub Actions executa os checks obrigatórios independentes do agente.
7. Merge continua subordinado à branch protegida e revisão humana quando aplicável.
8. T2/T3 não são executados pelo agente e exigem autorização separada.

## Por que Codex Cloud e não codex-action neste estágio

A Action oficial do Codex é adequada para cenários em que o owner quer controlar o agente dentro do GitHub Actions, mas exige uma chave de API do provedor como secret. Para este repositório, a primeira versão evita introduzir uma nova credencial de IA no GitHub e mantém a superfície de secrets mínima.

Uma futura migração para `openai/codex-action` deve ser tratada em PR/gate separado, com action fixada por SHA, `permission-profile` mínimo, `drop-sudo`/usuário sem privilégio e sem qualquer secret de Drive no mesmo job.

## Limites do agente

O agente não pode:

- alterar ou ler secrets;
- receber credenciais Drive;
- executar publicação;
- executar persistência T2;
- mudar ruleset/proteção de `main`;
- fazer self-merge;
- transformar uma hipótese de schema/regime em fato;
- promover compliance fiscal ou identidade financeira;
- fabricar evidência de CI, hashes, IDs ou runs.

## Paths sensíveis

Mudanças em workflows, `AGENTS.md`, política de automação, política Codex, persistência e publicação exigem revisão explícita antes de merge. A existência de um patch tecnicamente correto não é autorização para executar seus efeitos.

## Primeiro piloto

`docs/tasks/CODEX_TASK_001_SIOPE_REGIME_DISCOVERY.md`

O piloto é T0/offline e deve produzir somente arquitetura, configuração, fixtures e testes para descobrir regimes SIOPE 2005–2026. Ele não faz GET live e não toca no Drive.

## Evolução pretendida

- V1: engenheiro de PR sob demanda;
- V2: revisão automática de PRs pelo Codex, sem segredos operacionais;
- V3: diagnóstico de CI e proposta automática de correção em PR, ainda sem T2/T3;
- qualquer autonomia sobre coleta/persistência/publicação permanece fora deste plano até gate específico.
