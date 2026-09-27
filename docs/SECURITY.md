# Segurança operacional

1. Nunca versionar token, senha, OAuth client secret ou chave de API.
2. Usar variáveis de ambiente ou secret manager do executor.
3. Bronze permanece imutável; derivação recebe hash/proveniência.
4. Schema desconhecido vai para STOP/QUARENTENA.
5. LLM não é fonte final de números.
6. Mudanças em Silver/Gold só entram após QA.
7. Escrita remota deve ser idempotente e registrar log de run.


## 0.4.0 — runtime não interativo
- OAuth refresh token somente em secret store/variável injetada no processo.
- O programa não imprime access token, refresh token, client secret ou client ID em logs de execução.
- Estado persistente é sincronizado em arquivo SQLite separado de secrets.
- Tokens efêmeros via `GOOGLE_DRIVE_ACCESS_TOKEN` nunca são persistidos pelo provider.
- App OAuth em Testing não é adequado ao agendamento permanente porque o refresh token expira em 7 dias.
