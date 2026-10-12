# TASK298 — Análise do STOP_TASK296_PARTIAL_BATCH_REVIEW_ARTIFACT no lote P03

## Prova da execução

- Workflow manual TASK296 P03 em `main`, run **38187881571**: https://github.com/ferinbon-cpu/robo-dados-publicos/actions/runs/38187881571
- Job `114614082102`, `failure` **apenas no gate final**, após o upload **bem-sucedido** do artifact parcial `11720442335`.
- Artifact `task296-jom-P03-originais-manifesto` tem 4229 bytes, SHA256 do ZIP `5beb9cd83797eea23d88536d055b4c7b331257b6f4ff4f6da143d93814f6922e`, expira em 19/10/2026.
- O artifact contém **somente manifest.json**: 9 edições solicitadas, 9 `get_attempts`, 0 `validated_count`, 9 `failed_count`, 0 bytes transferidos/arquivados, zero retries.
- Todas as nove solicitações HTTP deram `HTTPError` **antes de qualquer corpo PDF**: 7194, 7195, 7196, 7197, 7198, 7199, 7200, 7213 e 7214.
- **A implementação antiga perde `exc.code`**, preservando apenas a classe `HTTPError`. Logo NÃO há base para afirmar se o status foi 403, 404, 429, 500 ou 502, ou se faltam os PDFs. Um `HTTPError` não invalida identidades da matriz.
- Resultado correto: `PARTIAL_STOP_REVIEW`; nenhum PDF novo custodiado no Drive SME, 122 edições confirmadas em custódia e 70 candidatas ainda pendentes.

## Ajuste seguro proposto

- Expor `http_status` e `code: HTTP_<status>` quando urllib informar status, sem registrar corpo de erro, URL nova, cookies nem cabeçalhos sensíveis.
- Em erro HTTP 403/429/500/502/503/504, interromper novas consultas do MESMO LOTE, registrar os itens não tentados `NOT_ATTEMPTED_SOURCE_HTTP_CIRCUIT_BREAKER` e manter resultado como `PARTIAL_STOP_REVIEW`. Um 404 permanece erro individual, sem inferir bloqueio geral.
- Corrigir fechamento do descritor de arquivo na checagem de assinatura `%PDF-`.
- Não altera universo de 88 URLs, plano de 10 lotes, `workflow_dispatch`, exigência manual `main`, nem permissões. Não agenda execução, não adiciona retries, não reduz validações e não escreve no Drive.
- Testes offline simulam 403, 429, 502 e 404, conferindo chamadas máximas e manifestos.
- Esta PR não autoriza rerun do P03. Antes de qualquer nova consulta real, observar CI, fazer merge após revisão e obter confirmação explícita do proprietário.

**Próximo passo:** após aprovação do código, uma nova execução manual do P03 (se autorizada) diferenciará status de indisponibilidade versus link específico com até uma primeira consulta quando houver bloqueio generalizado. Não usar TinyFish ou outros acessos remotos não autorizados. Até então, P03 fica em `STOP_REMOTE_HTTP_UNCLASSIFIED`.
