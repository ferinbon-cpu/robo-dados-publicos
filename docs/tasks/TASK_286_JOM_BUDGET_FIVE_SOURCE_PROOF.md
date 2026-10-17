# TASK 286 — Prova delimitada de PDFs JOM para suplementações da LOA 2026 (T0 carrier)

**Estado:** implementação offline inerte. O PR não autoriza executar a coleta. O operador deve cumprir o gate T1 separado e a política `AGENTS.md`.

## Motivo
LOA Lima 2027 precisa da dotação atualizada de 2026 por ação/fonte. Já possuímos 17 PDFs em Drive SME (16 edições JOM e LOA2026 separada). A edição 7211 de 28/03/2026, JOM página 5, contém o Decreto nº 62/2026; anexos I/II ainda não recuperados.

O índice do robô identificou 87 URLs de JOM que não fazem parte das 12 de agosto já preservadas. A TASK285 preparou a fila de edição 7211 e vizinhas. TASK286 usa a fixture existente diretamente e não depende do merge de TASK285.

## Limite do primeiro ensaio
- Cinco PDFs **exatos**: edições `7211`, `7208`, `7209`, `7210`, `7212`.
- Fonte: `docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv` com 87 URLs já validadas por `load_pinned_targets` da TASK219A.
- Não descobrir URLs novos, nem coletar fora da lista. Um GET por documento, sem retry, sem index GET.
- HTTPS e host final `ecrie.com.br`, caminho oficial permitido, tipo `application/pdf` ou octet-stream, assinatura `%PDF-`, parser `pypdf`, páginas >=1, hash SHA256.
- Limites: <= 200 MiB por PDF, <= 500 MiB agregados. Qualquer violação -> STOP (nenhum resultado canônico parcial).
- Não persistir PDFs/byte payload, texto integral, OCR nem anexos como artifacts; saída admissível nesta fase é **somente metadado de integridade de fonte**, sem identificação contábil e sem conclusão de ausência.
- Gate T1 deve fornecer confirmação exata `TASK286_APPROVE_5_EXACT_PDFS_SOURCE_READ_ONLY_NO_CUSTODY`, `implementation_sha` SHA de 40 caracteres, `exact_editions`, `max_document_gets=5`, limites de bytes e explícitas proibições de gravação e publicação.
- PR não registra consentimento de runtime. Owner é responsável pela autorização posterior, a ser pinada ao SHA revisado.
- Não foi criado nem modificado workflow. Não há disparo GitHub live e não houve PDF baixado pelo projeto nesta alteração.

## Diagnóstico de rede anterior a esta implementação
Na sessão de 10/10/2026, consulta direta de cinco URLs via ferramenta pública retornou `target_unreachable`. A consulta ao portal Limeira retornou 403. Isso NÃO comprova indisponibilidade global do JOM, somente falha dos acessos utilizados. O GitHub runner pode ter rede diferente; jamais repetir silenciosamente nem inferir ausência dos PDFs.

## Testes e dependências
`python -m unittest tests.test_task_286_jom_budget_five_source_proof -v`, sem internet (source fake), além dos gates usuais `AGENTS.md`. Os testes cobrem auth, source URL, integridade de PDF, host/content-type, contagens/efeitos e limite de bytes.
A API `execute_pilot` recebe `DocumentSource` injetável. Um orquestrador posterior deve passar a fonte live apropriada, após gate; nenhum T1 live é acionado automaticamente pelo import.

## Etapa T2 independente
Para **recuperar e arquivar os PDFs integrais na SME**, não basta a TASK286. Após relatório T1, criar operação create-only com preflight de colisão, custo/bytes e QA de readback SHA256, verificando destinos na pasta:
`/Google Drive/SME_LIMEIRA/LOA_LIMEIRA_2027/01_PDFS_ORIGINAIS/02_JOM_UNICAMP_BRONZE`
Pasta existente: https://drive.google.com/drive/folders/1XQ0Yp5c6Ms7eu3gCIwCMwE0fqIjimwEd
Nenhuma credencial SME nem ID privado de pasta deve ser inserido em artefato público com permissão de escrita.
Persistência e posterior publicação de planilhas/relatórios são gates separados.

## Artefatos antecedentes
- PR #915 TASK284: correção de completude da descoberta; CI 5/5 PASS.
- PR #916 TASK285: fila 5 URLs offline; CI 5/5 PASS.
- Inventário SME V14: https://docs.google.com/spreadsheets/d/1JZHgq8vD6uX8y8Wofyya6348LZCNael8-I0g8mcUUoc/edit
- Prova dos 17 PDFs já guardados na SME: QA por SHA256 (17/17, sem necessidade de redownload).
- Relatório V12 dos nove decretos: ainda sem anexos I/II.

**STATUS FINAL DESTE PATCH**: T0 TEST/REVIEW; GET live = 0; PDFs novos = 0; registros orçamentários extraídos = 0; merge feito pelo agente = não.
