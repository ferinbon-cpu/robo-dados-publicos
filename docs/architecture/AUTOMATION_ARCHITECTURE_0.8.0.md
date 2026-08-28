# ROBO_DADOS_PUBLICOS — Auditoria de arquitetura de automação 0.8.0

## 1. Objetivo

Esta revisão avalia como reduzir operação manual do repositório sem transformar conveniência operacional em autorização implícita de coleta, persistência, publicação ou inferência substantiva.

A decisão central é:

> **Agente pensa e propõe; política decide elegibilidade; workflow executa somente o que o contrato autoriza.**

Esta revisão é exclusivamente offline. Não executa o M8 ao vivo, não consulta fonte pública, não lê nem escreve Google Drive e não publica produto.

## 2. Base examinada

A revisão confronta três camadas já existentes:

1. os workflows, scripts, testes e contratos atualmente em `main`;
2. o manual técnico `MD_00_METODO_COLETA_TRATAMENTO_DADOS_PUBLICOS_IA_V17`;
3. a matriz acadêmica `MD_00_1_REFERENCIAL_ACADEMICO_E_MATRIZ_DE_INCORPORACAO_V02`.

Os MDs convergem com a implementação atual em pontos importantes:

- fonte oficial antes de interpretação por IA;
- Bronze imutável, Silver normalizada/rastreável e Gold submetida a QA;
- distinção entre extração, correspondência e interpretação por IA;
- relações sugeridas não são identidades financeiras;
- valores estruturados e aritmética crítica permanecem determinísticos;
- rebuild incremental deve seguir fechamento de dependências;
- idempotência evita escrita quando o conteúdo substantivo não mudou;
- maturidade e evidência precedem aumento de autonomia.

## 3. Pontos fortes comprovados

### 3.1 Fail-closed já é parte do desenho

Os gates atuais interrompem execução diante de ausência, duplicidade, drift e evidência incompatível. Esse padrão deve ser reutilizado para automação da própria engenharia.

### 3.2 Contratos e evidências já permitem decisão por máquina

O projeto possui contratos explícitos, testes de regressão, hashes, evidências pinadas e limites de efeitos remotos. Isso permite substituir decisões ad hoc por uma política versionada.

### 3.3 SIOPE histórico já foi generalizado

A existência de pipeline parametrizado reduz a necessidade de workflows anuais como arquitetura futura. Workflows históricos de prova podem permanecer como evidência, mas novas capacidades não devem multiplicar cópias anuais.

### 3.4 M8 é um bom piloto de autonomia controlada

O M8 histórico de produto possui efeitos conhecidos:

- 0 GET de fonte FNDE/SIOPE;
- 9 buscas de metadados no Drive;
- 9 downloads de Gold existentes;
- 0 writes no Drive;
- 0 publicação;
- bundle somente local/artifact GitHub;
- 8 séries de métricas e 72 observações Gold.

Porém, isso descreve o **comportamento do código**, não a capacidade máxima da credencial usada pelo workflow.

## 4. Dívidas arquiteturais encontradas

### 4.1 Não havia contrato estável para agentes

Antes desta revisão não existia `AGENTS.md`. Codex ou outro agente podia inferir regras a partir de muitos arquivos, mas não possuía uma fronteira curta, canônica e versionada de comportamento.

Correção desta revisão: `AGENTS.md`.

### 4.2 Não havia política de automação legível por máquina

Os limites estavam distribuídos entre MDs, workflows, testes e decisões históricas. Isso dificultava responder automaticamente a uma pergunta simples: “este gate pode rodar sem confirmação humana?”.

Correção desta revisão: `config/automation_policy.v1.json` + `robo_dados_publicos/automation/policy.py`.

### 4.3 Não há reusable workflows

O repositório não possui `workflow_call`. Há repetição de bootstrap, instalação, compileall, testes e regressão em vários workflows.

Recomendação: extrair reusable workflows somente depois que a política de risco estiver estável. Reuso deve reduzir duplicação, não misturar autorização entre gates.

### 4.4 CI offline está monolítico

`ci-offline.yml` contém muitas etapas M7 de desenho, dry-run e revisão em sequência. Isso oferece regressão ampla, porém aumenta tempo, acoplamento e dificuldade de manutenção.

Recomendação posterior: separar suites por domínio e reutilizar uma base comum, preservando um agregador obrigatório para PR/main.

### 4.5 Workflows históricos one-off continuam presentes

Eles têm valor de auditoria, mas não devem ser usados como modelo para novos anos/fontes após a generalização parametrizada.

Recomendação: manter evidência histórica, marcar workflows superseded/deprecated em inventário e impedir que novos fluxos sejam copiados por ano.

### 4.6 M8 é read-only por código, mas não por credencial provada

O workflow M8 usa `GOOGLE_DRIVE_REFRESH_TOKEN`, o mesmo nome de credencial da infraestrutura capaz de escrita. O bootstrap histórico oferecia `drive` e `drive.file`, mas não `drive.readonly`.

Consequência: remover o clique agora reduziria a defesa em profundidade. Um bug futuro poderia ampliar o efeito do workflow além do esperado pela política.

Correção desta revisão: o bootstrap passa a suportar explicitamente `https://www.googleapis.com/auth/drive.readonly`, sem modificar o default nem o token existente.

Próxima etapa necessária: gerar um refresh token separado com esse escopo, armazená-lo como `GOOGLE_DRIVE_READONLY_REFRESH_TOKEN` e provar sua incapacidade de escrita antes de autorizar no-click.

### 4.7 `main` não possui proteção de branch observada

Na data desta revisão, a API do GitHub reportou `main` como `protected=false`.

Isso não impede o funcionamento atual, mas é incompatível com uma futura meta de merge/autonomia mais ampla: um agente ou integração com permissão de push não deveria depender apenas de disciplina para evitar bypass de PR/CI.

Recomendação: criar futuramente ruleset/branch protection exigindo PR e checks obrigatórios antes de considerar auto-merge por agente. **Esta revisão não altera a proteção da branch.**

## 5. Modelo de risco adotado

### T0 — OFFLINE

Exemplos: testes, lint/compile, dry-run, validação de contrato, consistência de evidência local.

- rede de fonte: não;
- Drive: não;
- mutação: não;
- auto-run: permitido.

### T1 — REMOTE_READONLY

Exemplos: releitura bounded de Gold já persistido.

- efeitos remotos: somente leitura;
- publicação: não;
- auto-run: condicional;
- requisito adicional: credencial de capacidade estritamente read-only comprovada.

### T2 — CREATE_ONLY

Exemplos: Bronze/Silver/Gold novos após preflight de colisão.

- mutação: sim, bounded/create-only;
- auto-run: bloqueado nesta política;
- confirmação humana explícita continua obrigatória.

### T3 — MUTATING_OR_PUBLICATION

Exemplos: publicação em `08_OUTPUTS`, update, replace, delete, schedule/recorrência ou expansão equivalente de efeitos.

- auto-run: bloqueado;
- autorização separada obrigatória.

## 6. Estado do M8 após esta revisão

**Decisão:** `BLOCK` para no-click.

Isso não significa que o M8 seja inseguro em seu contrato atual. Significa que os pré-requisitos para remover a confirmação humana ainda não estão completos.

Bloqueadores formais:

1. `CURRENT_WORKFLOW_REQUIRES_MANUAL_CONFIRMATION`;
2. `CURRENT_REFRESH_TOKEN_CAPABILITY_IS_NOT_PROVEN_READONLY`;
3. `READONLY_REFRESH_TOKEN_SECRET_NOT_WIRED`.

O workflow ao vivo permanece intacto nesta revisão.

## 7. Caminho para o primeiro no-click

### Gate A — política e documentação offline

Esta revisão:

- adiciona `AGENTS.md`;
- adiciona política machine-readable;
- adiciona gate offline da política;
- adiciona testes fail-closed;
- adiciona suporte de bootstrap `drive.readonly`;
- mantém M8 manual.

### Gate B — credencial de menor privilégio

Ação humana única:

1. gerar refresh token com `drive.readonly`;
2. armazenar como `GOOGLE_DRIVE_READONLY_REFRESH_TOKEN` no GitHub;
3. nunca expor o token em conversa, commit, log ou artifact.

### Gate C — prova live da credencial read-only

PR separado deve:

- trocar somente o M8 para o novo secret;
- manter `workflow_dispatch` e confirmação humana nesta primeira prova;
- comprovar leitura das 9 Gold;
- comprovar tentativa de escrita **não necessária** e, se for desenhado um teste de capability, fazê-lo sem criar resíduo remoto;
- pinjar evidência do run.

A forma preferida de prova de capacidade é introspectar/validar o escopo efetivo do token ou usar endpoint apropriado de token metadata, e não realizar escrita destrutiva como teste.

### Gate D — reusable worker

Depois da prova:

- extrair o worker M8 para reusable workflow com `workflow_call`;
- secrets declarados explicitamente;
- `contents: read`;
- sem herança ampla de secrets;
- policy gate executado antes do worker.

### Gate E — no-click orchestrator

Só então um orquestrador em `main` poderá chamar automaticamente o M8 T1 após condições explícitas, por exemplo merge/CI verde e política `AUTO_ALLOWED`.

O orquestrador nunca deve chamar T2/T3 apenas porque um T0/T1 terminou com PASS.

## 8. Papel de Codex e agentes

### Permitido

- analisar arquitetura;
- procurar duplicação;
- refatorar;
- criar/reparar testes;
- diagnosticar CI;
- manter documentação;
- preparar branch/PR;
- propor mudanças de contrato.

### Não autorizado autonomamente

- coletar nova fonte;
- persistir dados;
- publicar produto;
- habilitar recurrence/schedule;
- remover confirmação humana de gate T2/T3;
- promover relação semântica a identidade financeira;
- concluir compliance MDE/Fundeb.

A IA pode aumentar a produtividade da engenharia sem assumir a autoridade do sistema de governança.

## 9. Plugins e integrações

O conector GitHub já cobre a principal necessidade de engenharia nesta fase. Plugins adicionais são opcionais e devem entrar somente quando trouxerem capacidade específica ausente.

Codex é mais útil como colaborador de engenharia do que como executor de dados. Um futuro workflow agentic pode revisar código, documentação e CI, mas deve produzir proposta/PR e permanecer abaixo da policy-as-code.

## 10. Reusable workflows, triggers e secrets

Princípios para a próxima etapa:

1. reutilizar lógica determinística comum;
2. não transformar reuso em propagação implícita de secrets;
3. declarar secret mínimo por worker;
4. não usar `workflow_run` genérico como atalho para gates com credenciais amplas;
5. manter policy check antes de qualquer execução remota automática;
6. nenhuma cadeia automática deve elevar permissões ou tier.

## 11. OIDC

OIDC deve ser estudado para workloads em Google Cloud que aceitem identidade federada e credenciais de curta duração. Ele pode reduzir long-lived cloud credentials.

Não se presume, nesta revisão, que OIDC substitua diretamente a autorização OAuth de usuário necessária para acessar o repositório pessoal no Google Drive. Essa decisão exige prova específica posterior.

## 12. Decisões que permanecem bloqueadas

- M8 no-click: bloqueado até credencial read-only separada e comprovada;
- publicação em `08_OUTPUTS`: separada e não autorizada por esta revisão;
- 2015 ou anos anteriores do SIOPE: não abrir;
- future batch: false;
- schedule/recorrência: não autorizados;
- overwrite/delete/replace: não autorizados;
- conclusão automática MDE/Fundeb/auditoria: não autorizada.

## 13. Critério de sucesso arquitetural

O projeto alcançará o primeiro estágio de autonomia útil quando:

1. T0 rodar automaticamente;
2. T1 rodar automaticamente apenas com credencial realmente read-only;
3. T2/T3 continuarem bloqueados sem autorização explícita;
4. agentes puderem preparar e revisar PRs sem poder ampliar seus próprios privilégios;
5. o sistema sempre consiga explicar por que uma ação foi executada ou bloqueada.

Esse desenho remove cliques de baixo risco sem remover governança.
