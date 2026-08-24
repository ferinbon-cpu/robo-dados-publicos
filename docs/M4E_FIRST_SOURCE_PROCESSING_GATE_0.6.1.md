# M4E — primeiro gate de processamento — 0.6.1

## Escopo

Este gate lê somente a edição 7310 já existente em `01_BRONZE`. Ele não baixa novamente o documento da fonte pública.

## Confirmação manual

No workflow `ROBO DADOS PUBLICOS`:

1. selecionar a branch `main`;
2. marcar `confirm_persistence`;
3. marcar `confirm_processing`;
4. executar uma única vez.

## Critérios de PASS

- versão `0.6.1`, status `CANDIDATE`;
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
