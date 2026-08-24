# Release 0.6.3 CANDIDATE

## Escopo

Transformar a evidência sanitizada de cada execução em uma leitura operacional simples, sem criar painel web, sem consultar novamente as fontes e sem alterar dados persistentes.

## Capacidade adicionada

- cartão de execução com saúde, versão, status, estado remoto e criação de log;
- cartão de fonte com status, quantidade habilitada e resultados sanitizados;
- cartões de métricas com taxa dos checks, fontes habilitadas, resultados e log;
- relatório equivalente em JSON e Markdown;
- resumo diretamente na página do GitHub Actions;
- artefato imutável por execução, retido por 30 dias;
- projeção estrita por lista permitida: campos arbitrários do payload não são propagados.

## Proteções

- nenhuma leitura adicional da origem;
- nenhuma escrita nova em `01_BRONZE`, `02_SILVER`, `03_GOLD`, `06_BANCOS`, `07_LOGS` ou `08_OUTPUTS`;
- o relatório deriva somente da evidência já sanitizada do gate;
- presença declarada de segredo ou identificador remoto encerra o relatório em `STOP_UNSAFE_INPUT_CONTRACT`;
- coleta, processamento, reconciliação, recorrência e agendamento continuam desabilitados;
- a versão ativa 0.6.2 permanece preservada.

## Como o operador verá o resultado

Após uma execução manual bem-sucedida, a página do workflow exibirá o bloco **Relatório de observabilidade — ROBO_DADOS_PUBLICOS**. O mesmo run oferecerá o artefato `observability-report-<run_id>` com `report.md`, `report.json` e os cartões JSON separados.

## Gate de promoção

Executar manualmente a candidata, confirmar que o resumo e o artefato estão presentes, revisar o contrato de privacidade `PASS` e só então decidir a promoção para `ACTIVE`.

## QA local

- compileall: PASS;
- testes unitários: 119/119 PASS;
- regressões históricas: 109/109 PASS;
- testes específicos de observabilidade: 7/7 PASS;
- preflight offline: 26/26 checks PASS;
- varredura de credenciais nos arquivos alterados: PASS.
