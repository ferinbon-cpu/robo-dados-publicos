# ROBO_DADOS_PUBLICOS SOFTWARE V01 — 0.5.0 CANDIDATE

## Marco
M4E — coleta determinística de fontes públicas com inventário, estado incremental, Bronze imutável e quarentena por contrato.

## Novidades
- inventário declarativo de fontes em JSON, com IDs únicos e HTTPS obrigatório;
- validação explícita de URL, nome de arquivo e tipos MIME esperados;
- estado persistente por fonte (`ETag`, `Last-Modified`, hash, status e arquivo remoto);
- GET condicional para evitar downloads desnecessários;
- payload novo gravado em `01_BRONZE` com nome qualificado por timestamp + SHA-256;
- hash já conhecido tratado como duplicata, sem nova gravação em Bronze;
- tipo de conteúdo inesperado enviado para `11_QUARENTENA` e convertido em `STOP_SOURCE_CONTRACT`;
- `dry-run` de fontes sem rede e sem escrita;
- comando `sources-validate` para validar contrato antes de qualquer coleta;
- `run` aceita `--source-config` e mantém o modo infraestrutura-only quando nenhuma fonte é configurada;
- nenhuma URL oficial foi habilitada por suposição: o arquivo `config/sources.example.json` é apenas um contrato desativado.

## Segurança e integridade
- credenciais continuam exclusivamente fora do repositório;
- Bronze continua imutável por hash;
- aquisição permanece separada da transformação;
- erro de contrato não vira “melhor palpite”: vai para quarentena/STOP;
- o blocker metodológico V17/V18 continua independente.

## Estado
**CANDIDATE**. Os testes locais validam a infraestrutura de coleta. A promoção depende de duas provas ao vivo ainda pendentes: (1) executor GitHub Actions autenticado e (2) primeiro conector oficial de fonte pública validado ponta a ponta.
