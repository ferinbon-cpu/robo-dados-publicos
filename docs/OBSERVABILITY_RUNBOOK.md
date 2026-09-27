# Runbook de observabilidade — ROBO_DADOS_PUBLICOS

## Onde ver o resultado de uma execução

A candidata `0.6.3` não exige aplicativo web próprio para operação básica. O primeiro ponto de observação é o GitHub Actions.

### 1. GitHub Actions — Summary

Caminho:

1. abrir o repositório `ferinbon-cpu/robo-dados-publicos`;
2. abrir **Actions**;
3. escolher **ROBO DADOS PUBLICOS**;
4. abrir a execução desejada;
5. consultar o **Summary**.

O Summary apresenta somente projeção sanitizada:

- saúde geral da execução;
- status do gate;
- versão e estado da release;
- checks aprovados/total;
- modo do estado remoto;
- confirmação de criação do log append-only;
- situação da fonte na execução;
- métricas operacionais;
- situação do contrato de privacidade.

Secrets, hashes, `remote_id` e payload bruto não são incluídos.

### 2. GitHub Actions — Artifacts

Na mesma execução, a seção **Artifacts** recebe:

`observability-report-<github.run_id>`

Retenção: 30 dias.

Conteúdo esperado:

```text
observability-report/
├── report.md
├── report.json
└── cards/
    ├── run.json
    ├── source_execution.json
    ├── metrics.json
    ├── health.json
    └── source_contract.json   # somente quando um cartão de fonte é fornecido
```

O arquivo `report.md` é a leitura humana. `report.json` é o pacote estruturado para futura interface, planilha ou API. Os arquivos em `cards/` permitem auditoria por dimensão.

### 3. Google Drive — auditoria persistente

A observabilidade não cria uma nova escrita no Drive. O runtime já autorizado continua usando:

- `06_BANCOS` para o estado persistente;
- `07_LOGS` para log append-only.

Esses artefatos são a trilha privada e persistente. O relatório do GitHub é uma projeção operacional sanitizada e não substitui essa auditoria.

## O que acontece quando o gate falha

O workflow captura a saída do gate em arquivo temporário de runner e tenta gerar o relatório antes de propagar a falha. Assim, uma falha operacional não deve ser transformada em sucesso apenas porque o relatório foi produzido.

O arquivo bruto temporário:

- permanece em `$RUNNER_TEMP`;
- não é incluído no artifact;
- não é usado como camada Bronze/Silver/Gold;
- desaparece com o runner.

Se o contrato de privacidade não declarar explicitamente `secret_values_exposed=false` e `remote_identifiers_exposed=false`, o relatório entra em `STOP_UNSAFE_INPUT_CONTRACT`.

## Significado dos estados principais

- `HEALTHY`: gate aprovado e contrato sanitizado aprovado;
- `ATTENTION`: evidência disponível, mas não suficiente para declarar saúde plena;
- `STOPPED`: falha de gate ou contrato de privacidade inseguro;
- `NOT_CONFIGURED`: dimensão não aplicável ou ainda não configurada, sem convertê-la artificialmente em zero ou falha.

Nos cartões de saúde de fonte permanecem separados `freshness`, `completeness`, `consistency`, `collection` e `latency`. Não existe escore composto oculto.

## Limites da 0.6.3

Esta interface não habilita:

- coleta recorrente;
- `schedule`;
- repetição dos gates históricos de coleta/processamento/reconciliação;
- reconciliação ampla;
- identidade financeira automática;
- painel web próprio.

A próxima camada de produto poderá consumir `report.json` sem alterar o motor de coleta e auditoria.
