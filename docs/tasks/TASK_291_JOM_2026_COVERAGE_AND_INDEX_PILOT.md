# TASK291 — Descobrir universo completo de edições do JOM Limeira 2026

Data: 10/10/2026. Responsável: owner. Este PR entrega **fase piloto** e matriz numérica offline, NÃO os PDFs faltantes. Os 9 lotes B01–B09 já arquivaram o subconjunto de 87 URLs previamente fixadas.

## Prova do ponto de partida (fonte vs lacuna)
- SME Drive, pasta `1XQ0Yp5c6Ms7eu3gCIwCMwE0fqIjimwEd`: 99 identidades de edições de 2026 (87 do fixture TASK219A + 12 edições adicionais 7304–7315).
- O intervalo numérico `7151..7328` possui 79 lacunas relativas a essas 99, **sem qualquer presunção de que todos os 79 números tenham sido publicados**; o fim do universo posterior a 22/09 não foi estabelecido.
- Página indexada do portal referente a janeiro/2026: **22 resultados declarados**, mas só 12 na primeira página. Um crawler que não pagina é incompleto.
- Página de setembro indexada expõe `7326` em 18/09 seguida de `7237` em 19/09 e `7238` em 22/09. Não normalizar para `7327/7328` sem capa de PDF; registrar anomalia como tal.
- Acessos diretos ao portal por cliente web atual retornaram **403**; não tentar bypass do portal nem pedir credenciais. A prova GitHub proposta tem STOP para 403 e robots disallow.
- Link fornecido pelo owner originalmente usa `dataDiario=6/5/2025` (2025); o recorte da nova pesquisa é jan–dez/2026, com estoque até 10/10 e revisita de períodos futuros.
- Diário Oficial do Município e Diário Oficial separado da Câmara têm fontes e números diferentes; **não misturar**.

## O que este PR efetivamente implementa
1. `task291_jom_2026_gap_ledger.py` — reconciliação T0 determinística usando a fixture SHA-verificada, os nove lotes e as doze edições adicionais do SME, publicada apenas como **79 lacunas NUMÉRICAS candidatas** (nenhuma URL PDF sintética).
2. `task291_jom_2026_index_pilot.py` — um gate manual que testa o acesso à página `/robots.txt` do município e **somente dois índices**, `?ano=2026&mes=1` e `?ano=2026&mes=9`. Total de GETs máximo 3, limites de bytes rígidos; sem redirect/retry, PDF GET, cache-bypass, Drive ou publicação. Usa analisador oficial preexistente `JornalOficialLimeira` e reconstituição do total visível que pode estar dividida em várias tags (falha identificada na TASK284, PR #915 ainda não mesclado).
3. `task291-jom-2026-index-pilot-manual.yml` — `workflow_dispatch` no `main` protegido, autorização booleana por owner, primeira tentativa apenas. Cria um manifesto JSON `PASS` ou `STOP` com GETs usados e links indexados vistos; artefato expira em 7 dias.
4. Testes unitários offline para parcialidade 22/12, robots `Disallow`, HTTP 403 sem retry, bloqueio de redirects, host não reconhecido e orçamento de rede; política `T1_REMOTE_READONLY` adicionada a `config/automation_policy.v1.json`, `auto_allowed=false`.

## Próximos gates NÃO autorizados automaticamente
**TASK292** (após evidência de PASS/STOP do piloto): descobrir índices de todos os meses jan–out/2026 com paginação real, mas só com URLs de paginação **emitidas pelo próprio HTML oficial**; deduplicar par `edicao/data/link`; confrontar total declarado com itens recuperados e todos os arquivos SME. STOP se total faltar, diferir, ocorrer conflito de identidade ou o servidor bloquear. Se 403, planejar canal oficial alternativo (pedido de dados/arquivo municipal), não usar bypass.

**TASK293** (somente após manifesto definitivo de URLs por edição): produzir lotes fechados com até 9 PDF GETs, URLs oficiais pinadas, previa SHA+capacidade, branch PR revisado e autorização owner para cada lote; enviar Drive SME create-only e prova de SHA-256 readback; nenhuma coleta prematura.

**TASK294**: minerar texto e anexos de orçamento 2026 sem misturar créditos autorizados com empenhos/liquidações/pagamentos, preservando origem, órgão, unidade, ação, fonte, valores e cancelamentos. Prioridade LDO/LOA 2027, EITI, educação, FUNDEB.

## Checklist do PR
- [ ] Gates offline e CI verde no SHA definitivo
- [ ] Owner review/merge na `main`; não self-merge (AGENTS.md)
- [ ] Owner executar workflow manual piloto **uma vez** (não existe agendamento)
- [ ] Ler retorno/manifesto: PASS ou STOP, não fingir sucesso se 403
- [ ] Arquivar manifesto e atualizar checkpoint SME
- [ ] Aprovar TASK292 para descoberta exaustiva em etapa distinta

Evidências públicas indexadas em 10/10/2026:
- <https://limeira.sp.gov.br/jornaloficial/?ano=2026&mes=1>
- <https://limeira.sp.gov.br/jornaloficial/?ano=2026&mes=2>
- <https://limeira.sp.gov.br/jornaloficial/?ano=2026&mes=5>
- <https://limeira.sp.gov.br/jornaloficial/>
