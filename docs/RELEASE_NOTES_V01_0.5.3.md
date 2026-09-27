# SOFTWARE V01 0.5.3 CANDIDATE — M4E.3 Jornal Oficial: PDF → Silver/Gold/RAG

## Status
CANDIDATE. A release ativa continua sendo a 0.4.0 até validação ao vivo do índice/documento e do executor remoto.

## Avanço substantivo
A 0.5.3 transforma uma edição textual do Jornal Oficial em derivados auditáveis sem depender de LLM:

- hash SHA-256 do PDF-fonte;
- staging Bronze imutável, com bloqueio de sobrescrita divergente;
- extração textual por página via `pypdf==5.9.0`;
- gate `STOP_OCR_REQUIRED` quando o PDF não contém texto suficiente;
- minimização determinística de CPF, RG, e-mail e telefone nas camadas derivadas;
- preservação de CNPJ de pessoa jurídica para análise contratual;
- Silver em `pages_silver.jsonl`;
- eventos estruturados Gold em `events_gold.jsonl`;
- chunks RAG em `chunks_rag.jsonl`;
- manifesto da edição com proveniência e métricas;
- classificação conservadora de contrato, termo aditivo, apostilamento, ata, convênio, decreto, portaria, lei, resolução, edital e aviso de licitação;
- extração inicial de contrato, processo, edital, modalidade/número de licitação, contratado, CNPJ, objeto, valor e data de assinatura.

## Regra de privacidade
O PDF original é a evidência Bronze. Silver/Gold/RAG não persistem a transcrição bruta sem minimização. Identificadores pessoais reconhecidos são substituídos por marcadores de redação. Nomes próprios não são removidos automaticamente, porque podem ser semanticamente necessários em atos de nomeação e porque a identificação automática de pessoa natural ainda não tem contrato de precisão suficiente.

## Regra de OCR
Nenhum OCR é disparado silenciosamente. PDF sem camada textual suficiente produz `STOP_OCR_REQUIRED`. Uma futura rota de OCR deverá ser explícita, auditável e separada da extração textual nativa.

## QA local
- `compileall`: PASS
- testes unitários: 42/42 PASS
- regressões históricas V03–V17: 109/109 PASS
- fixture PDF textual de 2 páginas: PASS
- Bronze hash/imutabilidade: PASS
- PII minimization: PASS
- STOP de PDF sem texto: PASS
- contrato e portaria estruturados: PASS

## Gate ao vivo pendente
1. executar `journal-discover` em runtime externo;
2. validar uma URL de PDF realmente declarada pelo portal;
3. baixar um único PDF atual por rota oficial;
4. executar `journal-process` nesse PDF;
5. comparar manualmente uma amostra dos eventos extraídos com a edição original;
6. somente então habilitar coleta incremental do Jornal Oficial.
