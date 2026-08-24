# M4E — primeiro gate de processamento — 0.6.1

## Escopo

Este gate lê somente a edição 7310 já existente em `01_BRONZE`. Ele não baixa novamente o documento da fonte pública.

## Gate concluído

O run `32761758504`, job `97541993609`, no commit `f9bb9afad3d519376157f5acbdc4dc2cd18bec15`, concluiu em 46 segundos com `PASS_GITHUB_JOURNAL_PROCESSING_GATE`. Todas as 16 verificações passaram.

O input `confirm_processing` e a chamada do gate foram retirados do workflow ativo após a promoção. Esta execução não deve ser repetida pela interface normal.

## Critérios de PASS

- versão `0.6.1`, status `CANDIDATE` durante o gate e `ACTIVE` após promoção;
- referência privada do Bronze presente no estado remoto;
- hash e tamanho do PDF exatamente iguais ao contrato;
- extrator `pypdf` na versão exata `6.10.0`;
- `PASS_DOCUMENT_PROCESSING`;
- 76 páginas, 195.540 caracteres, 53 eventos, 148 chunks e 68 tarefas;
- cinco derivados criados ou reutilizados somente após hash idêntico;
- 68 tarefas persistidas no estado;
- estado remoto substituído e log append-only criado;
- origem pública não chamada;
- nenhum ID remoto ou segredo exibido;
- resultado final `PASS_GITHUB_JOURNAL_PROCESSING_GATE`.

## Fora do escopo

- nova aquisição do PDF;
- coleta recorrente;
- agendamento;
- execução dos resolvers de contratos ou TCE-SP;
- TDA;
- promoção automática de identidade financeira.

## Tentativa segura registrada

O primeiro acionamento, run `32758683064`, parou em `STOP_PROCESSING_CONTRACT` antes de gravar derivados. A origem do desvio foi o pin legado `pypdf==5.9.0`, não o PDF, o OAuth ou o Drive. O gate agora também trava a versão do extrator.

O segundo acionamento, run `32760805877`, parou antes do acesso ao Drive porque o preflight importava a dependência antes da instalação. A ordem foi corrigida e protegida por teste de regressão. Ambas as tentativas foram fail-closed e não deixaram saídas parciais.
