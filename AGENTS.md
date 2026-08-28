# AGENTS.md — ROBO_DADOS_PUBLICOS

Este arquivo define instruções estáveis para Codex e outros agentes que trabalhem neste repositório. Ele não autoriza execução remota, coleta, persistência ou publicação por si só.

## 1. Objetivo do repositório

O ROBO_DADOS_PUBLICOS coleta, preserva, transforma, valida e apresenta dados públicos de forma auditável. O desenho privilegia fonte oficial, proveniência, determinismo, reprodutibilidade e separação entre dado, cálculo, correspondência, interpretação e hipótese.

## 2. Regra principal para agentes

**Agente propõe e implementa dentro do contrato; contrato e gate autorizam execução.**

Nunca transforme uma capacidade tecnicamente possível em capacidade operacional autorizada apenas porque o código consegue executá-la.

A política canônica de automação está em `config/automation_policy.v1.json`. Na dúvida, a decisão é `BLOCK`.

## 3. Invariantes de dados e persistência

1. Bronze é imutável e append-only.
2. Persistência nova deve ser create-only quando o gate não autorizar explicitamente outro comportamento.
3. Nunca introduzir overwrite, replace, delete ou limpeza automática como recuperação silenciosa de falha.
4. Nunca habilitar retry, paginação, recorrência, schedule ou expansão de lote sem gate explícito que prove e limite essa capacidade.
5. Antes da primeira escrita remota, todo preflight exigido pelo contrato deve concluir.
6. Falta, duplicidade, drift, schema inesperado ou evidência insuficiente devem terminar em STOP/fail-closed.
7. IDs remotos, tokens, client secrets, refresh tokens e payloads sensíveis não pertencem a commits, issues, artifacts públicos ou logs.
8. Outputs publicados são uma etapa separada da leitura/transformação e exigem autorização própria.

## 4. Invariantes semânticos

1. Não inferir identidade financeira por similaridade textual.
2. Não converter relação `CANDIDATE_ONLY`, provável ou semântica em identidade canônica sem evidência e regra autorizadas.
3. Não produzir conclusão automática de compliance MDE/Fundeb, auditoria fiscal ou causalidade quando o contrato não autorizar explicitamente.
4. Não imputar valores ausentes silenciosamente.
5. Valores estruturados e aritmética crítica devem vir de dados estruturados e cálculo determinístico, não de texto livre de LLM.
6. Preservar distinções temporais, de regime, fonte, natureza contábil, estoque e fluxo.

## 5. Política de automação

Os níveis são definidos em `config/automation_policy.v1.json`:

- `T0_OFFLINE`: determinístico, sem rede de fonte/Drive e sem mutação; pode ser automático.
- `T1_REMOTE_READONLY`: pode se tornar automático somente com credencial cuja capacidade read-only esteja provada, efeitos remotos de escrita iguais a zero e publicação bloqueada.
- `T2_CREATE_ONLY`: persistência bounded/create-only; continua exigindo autorização humana explícita até gate posterior específico.
- `T3_MUTATING_OR_PUBLICATION`: update/replace/delete/publicação/recorrência ou equivalente; permanece manual e separado.

Um agente **não pode reclassificar o próprio trabalho** para um nível menos restritivo no mesmo patch que habilita sua execução automática. Mudança de tier exige revisão explícita da política e testes.

## 6. Workflows GitHub

Ao editar `.github/workflows/`:

1. preservar `permissions` mínimas;
2. manter actions de terceiros fixadas por SHA;
3. manter `persist-credentials: false` no checkout quando aplicável;
4. não adicionar `schedule`, `workflow_run`, `push`, `repository_dispatch` ou `workflow_call` a um gate manual para remover confirmação humana sem que a política o marque como elegível;
5. não passar secrets implicitamente a reusable workflows; declarar somente os necessários;
6. um reusable workflow chamado por outro não pode ser usado para ampliar permissões;
7. mudanças que adicionam rede ou escrita exigem testes fail-closed antes do primeiro efeito remoto.

## 7. OAuth e credenciais

- O token padrão histórico do Drive pode possuir escopo amplo; não assumir que um workflow é seguro para auto-run apenas porque seu código chama somente GET.
- Gates `T1_REMOTE_READONLY` só podem perder o clique humano quando usarem uma credencial separada e comprovadamente read-only.
- Nunca alterar silenciosamente a finalidade de um refresh token existente.
- Nunca registrar valores de secrets em fixtures ou documentação.

## 8. Uso de Codex/IA no projeto

Codex e outros agentes são apropriados para:

- revisão arquitetural;
- refatoração;
- geração e reparo de testes;
- análise de CI;
- documentação;
- propostas de PR;
- detecção de duplicação, drift e lacunas de contrato.

Eles não são autoridade para:

- autorizar coleta nova;
- autorizar persistência/publicação;
- decidir compliance fiscal;
- promover hipótese financeira a fato;
- remover gates de segurança por conveniência.

## 9. Comandos mínimos de validação

Antes de considerar um patch pronto, executar, quando compatível com o escopo:

```bash
python scripts/github_preflight.py
python scripts/github_automation_policy_gate.py
python -m compileall -q .
python -m unittest discover -s tests -v
python main.py selftest
```

Se algum comando não puder ser executado, registrar explicitamente o motivo no PR. Nunca declarar PASS não observado.

## 10. Definição de pronto

Um patch só está pronto quando:

- preserva os invariantes acima;
- possui testes para o novo comportamento e para o fail-closed relevante;
- não amplia efeitos remotos de forma implícita;
- deixa claro o que permanece bloqueado;
- mantém proveniência e evidência auditáveis;
- CI e regressão histórica passam antes de merge.

## 11. Pull requests e merge

- Preferir branch dedicada e PR pequeno/coeso.
- Não escrever diretamente em `main` para mudanças de engenharia.
- Verificar o head SHA antes do merge e usar proteção por SHA esperado quando a ferramenta permitir.
- Não misturar autorização operacional de um gate com refatoração ampla sem necessidade.
- Evidência de run ao vivo deve ser pinada separadamente depois que o run existir; nunca fabricar IDs, hashes ou contagens.
