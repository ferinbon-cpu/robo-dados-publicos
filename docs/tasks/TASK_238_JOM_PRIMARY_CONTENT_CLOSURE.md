# TASK 238 — fechamento primário bounded do JOM para LT

## Objetivo

Encerrar o gate de conteúdo primário da divergência `LT_FORMATION_TIMING_DIVERGENCE`, preservando a diferença entre:

- fechamento negativo **da janela bounded**; e
- afirmação global de inexistência de ato modificador.

A primeira passa a ser permitida. A segunda continua proibida.

## Base canônica

Esta wave parte do `main` em:

`760fbaa52defbb27c2d25dfa9cc98465a1e3ca55`

A v2 de `config/lt_formation_timing_jom_direct_discovery.v2.json` permanece preservada como estado histórico anterior, no qual ainda havia três edições pendentes. O estado terminal desta wave está em:

`config/lt_formation_timing_jom_direct_discovery.v3.json`

A evidência primária materializada está em:

`docs/evidence/TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json`

## Método

Foi usada uma sonda efêmera e read-only no GitHub Actions, reaproveitando o runtime oficial de descoberta do repositório e `pypdf` para inspeção dos PDFs. A sonda:

- não escreveu no Drive;
- não escreveu no repositório durante a execução;
- não sintetizou URLs de PDF;
- aceitou apenas rotas declaradas pelo JOM oficial;
- resolveu a edição 7151 pelo filtro oficial exato de data + `numeroEdicao=7151`;
- calculou SHA-256 dos PDFs baixados;
- extraiu todas as páginas dos três alvos sem erro;
- procurou os termos-alvo e preservou os contextos dos hits amplos.

Execução:

- GitHub Actions run: `34651289623`;
- artifact: `10284047484`;
- schema: `TASK238_JOM_PRIMARY_PROBE_WAVE3_V2`;
- resultado: `PASS_PROBE_ALL_TARGETS_INSPECTED`.

O TinyFish/browser-agent **não foi usado para o fechamento primário**. A política daqui em diante é preferir HTTP oficial reproduzível e runtimes do repositório, usando TinyFish apenas quando indispensável.

## Edição 7142 — 18/12/2025

PDF oficial:

`https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_17122025183058.pdf`

- 243 páginas;
- 141.361.660 bytes;
- SHA-256 `4c90b13d6ba6360a142e3c287ce45a65e2a47fa52068cad9847420baf9791ced`;
- zero erros de extração;
- três hits do gatilho `08/2025`.

Os três hits são falsos positivos para a divergência LT:

1. página 73 — dado/figura do Cadastro Único referente a agosto de 2025;
2. página 180 — substring numérica da Portaria nº 2.508/2025;
3. página 228 — substring numérica da Notificação de Fiscalização de Obras nº 208/2025.

Não foram localizados os alvos exatos `Linguagens e Tecnologias`, `PSS 04/2025`, `Resolução SME`, `Resolução nº 08`, `Resolução 08/2025` ou `primeiro semestre`.

Status:

`CLEARED_BY_COMPLETE_PRIMARY_PDF_INSPECTION`

## Edição 7151 — 06/01/2026

PDF oficial:

`https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_05012026203147.pdf`

- 125 páginas;
- 44.002.985 bytes;
- SHA-256 `ec298a6cff290723c97d24c291e36ef2c2044713b0fc5082b4560329e1d1dab8`;
- zero erros de extração;
- três hits do gatilho `08/2025`.

Os hits pertencem a assuntos tributários e socioassistenciais/CMDCA, incluindo Termo nº 08/2025 do CMDCA/SEPROSOM. Nenhum deles pertence à Resolução SME nº 08/2025, ao PSS 04/2025 ou a LT.

Não foram localizados os alvos exatos `Linguagens e Tecnologias`, `PSS 04/2025`, `Resolução SME`, `Resolução nº 08`, `Resolução 08/2025` ou `primeiro semestre`.

Status:

`CLEARED_BY_COMPLETE_PRIMARY_PDF_INSPECTION`

## Edição 7168 — 28/01/2026

PDF oficial:

`https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_27012026163638.pdf`

- 70 páginas;
- 11.091.327 bytes;
- SHA-256 `bb224c0c975e26989bab6932726ae6aa900d729a1a3344ecc6316ca578140d09`;
- zero erros de extração;
- 17 hits do gatilho amplo `formação`.

Os hits se distribuem entre:

- política municipal de governo digital;
- formação esportiva em termos de fomento;
- Edital de Credenciamento retificado da Escola em Tempo Integral 2026 para oficinas extracurriculares da SME.

No bloco da SME aparecem `linguagens artísticas`, formação de banda/fanfarra e formação acadêmica de oficineiros. Isso não corresponde ao alvo exato `Linguagens e Tecnologias`, nem ao PSS 04/2025 ou a modificador da Resolução SME nº 08/2025.

Status:

`CLEARED_BY_COMPLETE_PRIMARY_PDF_INSPECTION`

## Reconciliação final dos candidatos

A matriz completa de candidatos ficou:

- 7142 — limpa por inspeção integral do PDF oficial;
- 7146 — limpa pela inspeção primária registrada na TASK 237;
- 7150 — limpa pela Portaria IPML nº 244/2025;
- 7151 — limpa por inspeção integral do PDF oficial;
- 7163 — limpa por inspeção primária direta;
- 7168 — limpa por inspeção integral do PDF oficial;
- 7172 — limpa por contexto primário independente do IPML.

Pendências:

`[]`

## Estado terminal bounded

A janela de 17/12/2025 a 31/01/2026 contém 33 edições consecutivas, 7140–7172. O inventário está completo, a triagem foi reconciliada e todos os candidatos amplos foram submetidos a contexto ou inspeção primária suficiente.

Portanto:

- `inventory_closed = true`;
- `discovery_triage_complete = true`;
- `primary_content_closed = true`;
- `pending_primary_editions = []`;
- `modifier_candidate_established = false`;
- `bounded_negative_result = true`;
- `audit_state = BOUNDED_WINDOW_COMPLETE_NO_MODIFIER_CANDIDATE_LOCATED`.

A afirmação permitida é:

> Na janela completa de 17/12/2025 a 31/01/2026, não foi localizado no JOM candidato a ato modificador da redação relativa ao prazo de formação em Linguagens e Tecnologias da Resolução SME nº 08/2025.

A afirmação proibida continua sendo:

> Não existe ato modificador em qualquer data ou fonte.

## Divergência normativa

A divergência permanece:

`LT_FORMATION_TIMING_DIVERGENCE = OPEN_UNRESOLVED`

O fechamento negativo da janela não transforma a página operacional da SME em ato normativo e não autoriza substituir silenciosamente o texto primário da Resolução SME nº 08/2025.

Para resolver a divergência será necessária nova evidência primária exata — por exemplo, ato modificador fora desta janela bounded ou outra fonte normativa primária que explique a redação operacional atual.

## Cobertura

A cobertura contextual permanece:

`38/38_UNCHANGED`
