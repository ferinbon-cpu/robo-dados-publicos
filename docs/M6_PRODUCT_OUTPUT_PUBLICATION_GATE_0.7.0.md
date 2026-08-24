# M6 — Gate controlado de publicação da saída 0.7.0

## Objetivo

Validar uma primeira publicação real da camada de produto da candidata `0.7.0` sem transformá-la em rotina automática e sem reabrir coleta, processamento ou reconciliação.

A release ativa permanece `0.6.3`. A `0.7.0` permanece `CANDIDATE` até decisão posterior de promoção.

## Escopo exato da escrita

O gate pode criar **exatamente três itens novos** dentro da pasta canônica `08_OUTPUTS`:

1. uma Planilha Google importada de `table.csv`;
2. um `report.pdf` com nome controlado;
3. um manifesto JSON de conclusão, gravado por último.

Não há update, replace, delete, overwrite, criação de pasta, agendamento ou expansão para outras saídas.

## Pré-condições antes da primeira escrita

Antes de chamar uma operação de criação no Drive, o gate deve:

- validar a identidade `0.7.0 CANDIDATE` sobre `0.6.3 ACTIVE`;
- validar o contrato imutável do gate;
- construir o bundle local em diretório temporário;
- verificar `report.json`, `report_card.json` e `manifest.json`;
- verificar a lista exata dos seis artefatos de conteúdo;
- recomputar tamanho e SHA-256 de cada arquivo;
- confirmar `READY_WITH_CAUTION` para o primeiro relatório técnico;
- consultar `importFormats` da API do Drive e comprovar suporte atual de `text/csv` para Google Sheets;
- listar `08_OUTPUTS` e encerrar se qualquer um dos três nomes planejados já existir.

## Ordem da publicação

A ordem é deliberada:

1. Google Sheet;
2. PDF;
3. manifesto de conclusão.

O manifesto é o marcador de conjunto completo e, por isso, só pode ser criado depois de Sheet e PDF terem sido criados e verificados.

## Verificação remota

Depois de cada criação, o gate relê os metadados do item e verifica apenas o necessário para integridade operacional:

- nome esperado;
- MIME esperado;
- pertencimento a `08_OUTPUTS`;
- tamanho, quando aplicável a PDF e JSON.

Os IDs remotos são usados apenas em memória para essa verificação e não são publicados no resultado do gate nem no manifesto de conclusão.

## Falha parcial

O gate não tenta apagar automaticamente arquivos já criados. Se, por exemplo, a Planilha Google for criada e o PDF falhar:

- a execução termina em `STOP`;
- `created_count` informa quantas criações ocorreram;
- `partial_write_possible=true` sinaliza revisão humana;
- o manifesto de conclusão não é criado;
- uma nova tentativa com os mesmos nomes será barrada pela política de colisão.

Isso evita que um mecanismo de recuperação introduza deleções automáticas não revisadas.

## Conteúdo do primeiro gate

O primeiro relatório é explicitamente técnico. Ele registra a validação da própria camada de produto e contém cautela indicando que não é análise substantiva de orçamento, contrato, fornecedor, política pública ou pessoa.

## Workflow

O workflow dedicado é `.github/workflows/product-output-publication-gate.yml`.

Características:

- somente `workflow_dispatch`;
- confirmação booleana explícita;
- sem `schedule`;
- permissões GitHub `contents: read`;
- ações fixadas por SHA;
- suíte completa e regressões antes do gate;
- dry-run local sem rede antes da publicação real;
- artifact final contém somente `result.json` sanitizado;
- workflow de produção principal continua sem rota para publicação de produto.

## Critério de sucesso do gate ao vivo

O gate só será considerado aprovado quando uma execução manual em `main` demonstrar:

- `PASS_M6_PRODUCT_OUTPUT_PUBLICATION_GATE`;
- `created_count = 3`;
- Google Sheet criada;
- PDF criado;
- manifesto de conclusão criado por último;
- ausência de overwrite;
- ausência de IDs remotos e secrets no artifact do GitHub;
- verificação independente de que os três itens esperados existem em `08_OUTPUTS`.

Somente depois dessa auditoria a promoção da `0.7.0` para `ACTIVE` pode ser considerada.
