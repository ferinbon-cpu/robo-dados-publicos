# TASK 010N-R-E-M — one-shot direto do `$metadata` oficial SIOPE 2025

## Resultado

`STOP_DIRECT_METADATA_ACCESS_NO_EDMX`

A autorização one-shot `SIOPE2025-DIRECT-METADATA-20260829-02` foi recebida com o URL literal informado pelo owner:

`https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/$metadata`

Foi realizada exatamente uma tentativa direta. O ambiente retornou falha de fetch `Cache miss` e nenhum corpo EDMX foi obtido.

Não houve retry, search workaround, consulta municipal, ano, período, valores financeiros, autenticação, Drive, Gold ou engenharia reversa.

A camada de execução não expôs de forma confiável se algum tráfego de rede chegou a ser emitido antes do `Cache miss`; por isso o registro fail-closed usa `network_io_observed = UNKNOWN`, sem transformar a falha local em evidência sobre disponibilidade ou inexistência do endpoint FNDE.

## Efeito semântico

Nenhum.

Permanecem:

- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- evidência pública do contrato = `PARTIAL_OFFLINE`;
- fechamento anual = `UNKNOWN`;
- comparabilidade semântica = `UNKNOWN`;
- Gold 2025 = `UNKNOWN/BLOCKED`;
- série anual fechada = `2016–2024`;
- `0.8.0 = CANDIDATE`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Interpretação

`Cache miss` não prova que o endpoint não exista, não prova indisponibilidade do FNDE e não constitui evidência semântica. A autorização one-shot é tratada como consumida e nenhuma repetição é permitida sem nova autorização separada.
