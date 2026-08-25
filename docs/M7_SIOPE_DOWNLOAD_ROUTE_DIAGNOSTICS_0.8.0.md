# M7 — SIOPE download route diagnostics — 0.8.0 CANDIDATE

## Resultado do primeiro subgate ao vivo

O run `32793490217` (`M7 SIOPE download route discovery 0.8.0 #1`) terminou em `Failure` porque o gate retornou deliberadamente `STOP_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_GATE` com motivo `STOP_SIOPE_DOWNLOAD_ROUTE_NOT_EXPLICITLY_DISCOVERED`.

Isso não representa falha do CI ou quebra de runtime. Antes do STOP, passaram preflight, dry-run, compileall, `213/213` testes unitários e `109/109` regressões históricas.

A evidência sanitizada confirmou que não houve download do artefato, `HEAD`, submissão de formulário, bypass de CAPTCHA, escrita remota, coleta, processamento, recorrência ou schedule.

## Limitação observada

O primeiro payload de STOP preservou a segurança, mas não preservou diagnósticos suficientes para distinguir entre:

- ausência de scripts declarados;
- scripts declarados mas não lidos;
- scripts acima do limite de tamanho;
- erro de content-type/rede em scripts opcionais;
- presença de marcadores de exportação no HTML sem rota literal;
- ausência efetiva de qualquer rota explícita.

## Incremento diagnóstico

Esta etapa mantém exatamente o mesmo escopo de rede do subgate e acrescenta somente metadados sanitizados ao STOP:

- bytes da página;
- quantidade de scripts declarados;
- quantidade de scripts lidos;
- quantidade de falhas de scripts e códigos de falha;
- total de bytes de scripts lidos;
- presença/contagem de marcadores públicos de exportação em HTML, scripts inline, atributos de evento, `data-*`, `href` e `action`;
- quantidade de candidatas de rota.

Nenhum corpo HTML/JavaScript, URL de script, query string, token ou conteúdo bruto é incluído no artifact.

## Segurança preservada

- mesmo host oficial permitido;
- GET-only;
- sem `HEAD`;
- sem chamada à rota candidata;
- sem download do `.txt.gz`;
- sem POST/form submission;
- sem CAPTCHA bypass;
- sem OAuth/Drive;
- sem coleta/processamento;
- sem recorrência/schedule.

Uma nova execução manual só deve ocorrer após CI integral dessa alteração e merge em `main`.
