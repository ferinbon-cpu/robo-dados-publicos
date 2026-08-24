# M4E — primeira tentativa de processamento — 2026-08-24

## Execução

- workflow: `M4E processing gate 0.6.1`;
- run público: `32758683064`;
- commit: `db3b2c678faf76a6a24c3a919d270eec08007c26`;
- resultado: `STOP_PROCESSING_CONTRACT`;
- segurança: nenhum secret ou identificador remoto exposto.

## O que passou

- referência privada do Bronze presente no estado;
- URL, SHA-256 e status da fonte compatíveis;
- download do Drive com hash e tamanho exatos;
- 76 páginas e `PASS_DOCUMENT_PROCESSING`;
- Bronze não recriado;
- origem pública não chamada.

## Motivo do STOP

O ambiente do GitHub instalou `pypdf==5.9.0`, enquanto as métricas históricas haviam sido produzidas com `pypdf==6.10.0`. O extrator legado observou 186.745 caracteres, 50 eventos, 142 chunks e 65 tarefas, divergindo do contrato de 195.540 caracteres, 53 eventos, 148 chunks e 68 tarefas.

O gate interrompeu antes do commit dos cinco derivados, da persistência do estado e da criação do log operacional. Portanto, a falha foi fail-closed e não deixou saída parcial no Drive.

## Correção

- fixar `pypdf==6.10.0` em `requirements.txt` e `pyproject.toml`;
- incorporar nome e versão do extrator ao contrato JSON;
- verificar a versão antes do download e do processamento;
- manter as métricas originais, agora associadas explicitamente ao extrator que as produziu;
- exigir novo CI offline antes de repetir o gate ao vivo.

## Segunda tentativa e correção da ordem do workflow

O run `32760805877`, no commit `d18c0c83d07ba50b7c9215558b47a8995afeb81e`, parou no preflight antes da instalação das dependências. O novo preflight verificava a versão instalada de `pypdf`, mas a etapa `Instalar dependências` ainda estava posicionada depois dele. O resultado foi `ModuleNotFoundError` sem acesso ao Drive e sem qualquer processamento ou escrita.

A correção posiciona a instalação determinística de `requirements.txt` antes do preflight de runtime e adiciona um teste de regressão que exige essa ordem. A validação de presença dos secrets permanece antes da instalação e continua sem exibir valores.
