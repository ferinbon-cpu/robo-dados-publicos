# SOFTWARE V01 0.6.1 ACTIVE — M4E processamento controlado promovido

## Promoção

A candidata 0.6.1 foi promovida após o run `32761758504` concluir com `PASS_GITHUB_JOURNAL_PROCESSING_GATE`. A evidência candidata permanece em `release_manifest_v01_0.6.1.json`; a identidade ativa está em `release_manifest_v01_0.6.1_active.json`.

## Resultado comprovado

- PDF imutável da edição 7310 reconfirmado por SHA-256 e tamanho;
- `pypdf==6.10.0` confirmado;
- 76 páginas e 195.540 caracteres extraídos;
- 53 eventos Gold, 148 chunks RAG e 68 tarefas;
- cinco derivados criados;
- estado remoto substituído e log append-only criado;
- origem pública não chamada;
- secrets e IDs remotos não publicados.

## Segurança preservada

O workflow ativo não oferece mais os gatilhos de coleta ou processamento. Agendamento, recorrência, novas fontes e execução automática da reconciliação permanecem desabilitados. `MATCH_CANDIDATE` continua insuficiente para identidade financeira e o TDA continua bloqueado.

## Próximo gate

`M4E_FIRST_RECONCILIATION_EXECUTION_GATE`: executar uma amostra limitada e explicitamente aprovada das tarefas já persistidas, sem converter correspondências candidatas em identidade financeira.
