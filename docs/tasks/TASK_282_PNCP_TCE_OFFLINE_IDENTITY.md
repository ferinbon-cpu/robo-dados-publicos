# TASK 282 — identidade contábil qualificada e colisões offline

## Objetivo

A TASK282 endurece a identidade contábil usada na futura ponte contratação → execução. Ela é estritamente T0/offline e trabalha apenas com evidências já versionadas no repositório e com um derivado mínimo do ledger previamente custodiado pela TASK187.

A conclusão continua `UNRESOLVED`: esta task **não** liga uma compra a um empenho e **não** atribui pagamento a contratação.

## Problema demonstrado

Número + ano de empenho não é uma chave segura entre entidades.

A TASK187 já registra, em contrato versionado, o CSV oficial de despesas de Limeira/2026 como material previamente fornecido pelo owner e custodiado create-only. A TASK282 materializa no próprio repositório apenas o derivado mínimo necessário para revisar o novo achado: 682 pares número-ano com colisão entre entidades, representados compactamente em 20 intervalos, codificadas em 20 intervalos e sem fornecedor, valor, objeto ou histórico.

Arquivo canônico:

`docs/evidence/fixtures/task282/TASK_282_COLLISION_RANGES.json`

A partir desse arquivo qualquer CI/revisor pode reproduzir, sem Drive e sem rede, que existem 682 pares número-ano representados pelos 20 intervalos e associados a pelo menos duas entidades. Portanto a chave futura deve incluir, no mínimo, município, entidade, exercício original e número.

## Chave contábil

`CommitmentKey` contém:

- município;
- entidade;
- exercício original do empenho;
- número canônico do empenho.

O parser aceita somente a sintaxe TCE explicitamente observada `numero-ano`. Ele não remove sufixos de outros sistemas, não adivinha exercício e não normaliza `03286-01` para `3286-2026`.

## Caso 45/2026

As evidências já versionadas das TASK219AA/AB preservam a cadeia municipal:

`Contrato 45/2026 → E00010/2026 → TDA 03286-01`.

A fixture minimizada da TASK282 congela três observações contábeis do candidato TCE 3286/2026 da Prefeitura, nos estágios empenho, liquidação e pagamento, mas isso é somente uma coorte contábil observada.

A proposição ainda ausente é:

`TDA 03286-01 = TCE 3286/2026 na mesma entidade e no mesmo exercício original`.

Sem testemunho oficial dessa equivalência:

- `procurement_identity = UNRESOLVED`;
- `payment_attribution_authorized = false`;
- pareamento liquidação → pagamento individual permanece `UNRESOLVED`;
- nenhum valor é atribuído ao contrato.

## Minimização

A fixture da TASK282 não persiste CNPJ/CPF, valor, descrição da despesa ou histórico textual. O identificador de fornecedor pode ser usado transitoriamente pelo resolvedor apenas para detectar contradição dentro da mesma chave contábil; somente um fingerprint interno é comparado e ele é removido antes da saída pública.

Mudança de fornecedor dentro da mesma chave é tratada como STOP, não como transferência/novação implícita. Uma transferência válida exigiria relação oficial explícita e contrato próprio de dados.

## Reprodutibilidade

O gate de merge usa somente arquivos presentes no repositório:

- contrato TASK187;
- evidências TASK219AA/AB e TASK219H;
- sementes TASK264;
- fixture minimizada TASK282;
- witness compacto das 682 colisões;
- carrier TASK281 apenas para provar que ele permanece independente/inativo.

O CSV bruto de 17 MB não é necessário para executar, testar ou revisar a TASK282. A custódia e o SHA do ledger continuam pertencendo ao contrato histórico TASK187; esta task consome apenas o witness mínimo versionado.

## Invariantes

- fornecedor, objeto, valor, data próxima ou candidato único não criam identidade;
- número/ano sem entidade não identifica empenho municipal de forma segura;
- `id_despesa_detalhe` identifica observação TCE, não contrato;
- compromisso, liquidação e pagamento são estágios distintos;
- diferença de cobertura temporal não é divergência contábil automática;
- ausência de chave oficial termina em `UNRESOLVED`.

## Validação

Executar:

```bash
python scripts/github_preflight.py
python scripts/github_automation_policy_gate.py
python scripts/github_codex_engineer_policy_gate.py
python -m compileall -q .
python -m unittest discover -s tests -v
python main.py selftest
python -m robo_dados_publicos.research.task282_pncp_tce_bridge_audit
```

O último comando valida somente o witness repo-local de colisões, sem alegação de exaustividade do ledger.

Nenhum comando da TASK282 realiza fetch, Drive write, publicação ou consumo da TASK281.

## Próximo passo após merge

O próximo trabalho deve permanecer focado no caso 45/2026: localizar ou materializar um testemunho oficial que explique a equivalência entre `03286-01` e `3286/2026`, com entidade e exercício explícitos. Até lá, a ponte TDA → TCE permanece aberta.

Qualquer investigação de fonte externa posterior deve ser tratada em tarefa e gate próprios; ela não faz parte desta implementação T0.
