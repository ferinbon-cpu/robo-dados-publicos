# M4E promotion review — software 0.5.8

## Decisão

`PASS_USER_AUTHORIZED`. A candidata 0.5.8 pode assumir a identidade de release ativa.

## Critérios verificados

- pacote candidato remoto preservado e confirmado por SHA-256;
- Jornal Oficial, cadastro municipal, TCE-SP e ledger com evidência ao vivo;
- QA completo e regressões históricas sem falha;
- runtime ativo grava 0.5.8 como `LATEST_SOFTWARE_VERSION` e `NONE` como candidata corrente;
- candidato e manifesto candidato permanecem preservados;
- nenhuma promoção automática para `financial_identity`;
- TDA permanece bloqueado e coleta de produção permanece opt-in;
- gate GitHub permanece pendente e não é confundido com promoção local da release.

## Resultado

Promoção aprovada. Próxima ação: `M4D_GITHUB_LIVE_GATE`.
