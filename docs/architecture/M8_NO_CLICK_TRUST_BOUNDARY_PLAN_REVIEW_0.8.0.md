# M8 — revisão da trust boundary para no-click 0.8.0

## Contexto

A primeira prova live T1 read-only passou e foi pinada. O worker M8 também já foi extraído para um reusable workflow `workflow_call` com três secrets dedicados explícitos, `permissions: contents: read`, sem `secrets: inherit` e sem caller automático.

O bloqueador restante é a trust boundary do código que receberia secrets em execução automática.

## Evidência observada no GitHub

No checkpoint posterior ao PR #166:

- repositório `ferinbon-cpu/robo-dados-publicos`: `visibility=private`;
- `main`: `protected=false`;
- consulta da coleção de repository rulesets retornou HTTP 403 com mensagem `Upgrade to GitHub Pro or make this repository public to enable this feature.`;
- a documentação oficial do GitHub informa que rulesets e protected branches em repositórios privados estão disponíveis em GitHub Pro, Team e Enterprise Cloud.

Portanto, no plano/capability atual observado para este repositório privado, não existe a trust boundary GitHub que a policy exige para habilitar um caller automático portador dos secrets read-only.

## Decisão fail-closed

`M8_NO_CLICK` permanece `BLOCK`.

Não tornar o repositório público como atalho. A privacidade do repositório não deve ser sacrificada para habilitar uma automação T1.

Também não criar um caller automático no GitHub enquanto `main` puder ser alterado sem uma proteção equivalente à exigida pela policy.

## Caminhos possíveis

### Caminho A — GitHub Pro

Manter toda a orquestração no GitHub, fazer upgrade da conta/plano que hospeda o repositório privado, habilitar branch protection/ruleset para `main`, reler a proteção e só então preparar o trusted orchestrator T1 em PR separada.

Vantagem: menor mudança arquitetural. Desvantagem: cria dependência de plano pago para a trust boundary.

### Caminho B — manter M8 manual no GitHub

Nenhum custo ou mudança arquitetural. O worker reusable fica pronto, mas a execução M8 continua por `workflow_dispatch` com confirmação humana.

Vantagem: estado atual já é seguro e provado. Desvantagem: não entrega no-click.

### Caminho C — trust boundary externa no Google Cloud

Manter GitHub como origem de código/evidência, mas executar o T1 no-click em runtime externo controlado, com identidade/secret storage e artefato de execução pinado, sem depender de secrets liberados automaticamente por um branch GitHub desprotegido.

Esse caminho exige gate próprio de arquitetura e prova; não deve ser inferido como autorizado apenas porque o projeto já usa Google Cloud Shell. Nenhum scheduler, Cloud Run Job ou Secret Manager é criado por esta revisão.

## Recomendação técnica

Se o objetivo imediato for remover cliques com o mínimo de engenharia, o caminho A é o mais curto, desde que o usuário aceite o custo do GitHub Pro. Se a preferência for não criar dependência paga do GitHub, o caminho C é arquiteturalmente mais coerente para no-click, mas deve ser implementado e provado em gates separados.

Até essa decisão, o caminho B é o estado operacional seguro.

## Permanecem bloqueados

Publicação em `08_OUTPUTS`, T2/T3 automáticos, 2015 ou anteriores, future batch, retry, paginação, recorrência, schedule, overwrite/delete/replace, imputação e conclusões automáticas de compliance/auditoria fiscal.
