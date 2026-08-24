# SOFTWARE V01 0.6.0 CANDIDATE — M4E primeira coleta controlada

## Objetivo

Provar a primeira aquisição real de uma fonte pública pelo runtime GitHub → Drive, sem habilitar coleta recorrente. O alvo é somente a edição 7310 do Jornal Oficial de Limeira, já validada ao vivo em ambiente isolado.

## Contrato do artefato

- fonte: `LIMEIRA_JORNAL_OFICIAL_EDICAO_7310`;
- data de publicação: 22/08/2026;
- conteúdo esperado: `application/pdf`;
- tamanho esperado: 16.952.899 bytes;
- SHA-256 esperado: `78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680`;
- destino de PASS: `01_BRONZE`, com nome imutável qualificado por hash;
- divergência de tipo, hash ou tamanho: `11_QUARENTENA` e STOP.

## Travas operacionais

- `workflow_dispatch` continua sendo o único gatilho;
- `confirm_persistence` continua obrigatório;
- `confirm_source_collection` é uma confirmação adicional e nasce `false`;
- o inventário contém exatamente uma fonte;
- o agendamento continua desabilitado;
- nenhuma outra edição ou fonte será coletada neste gate.

## Validação offline

- compileall: PASS;
- testes: 92/92 PASS;
- regressões históricas: 109/109 PASS;
- preflight da candidata e do workflow: PASS;
- dry-run do inventário: sem rede e sem escrita;
- varredura de segredos: PASS.

## Próxima ação

`M4E_FIRST_SOURCE_COLLECTION_LIVE_GATE_0_6_0`: executar uma única vez com as duas confirmações manuais e exigir `PASS_GITHUB_SOURCE_COLLECTION_GATE`.
