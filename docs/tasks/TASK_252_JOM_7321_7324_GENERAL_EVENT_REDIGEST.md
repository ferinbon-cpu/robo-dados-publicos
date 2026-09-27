# TASK 252 — canonização TASK251 e redigest geral hash-pinned JOM 7321–7324

## Objetivo

A TASK252 fecha a prova binária das quatro edições descobertas pela TASK247, canoniza a recuperação live da TASK251 e prepara um carrier T1/read-only para redigest geral de eventos das edições 7321–7324.

A implementação/PR é estritamente offline. Nenhum GET documental é feito por este patch.

## Evidência canônica

A TASK251 foi mesclada em `ce0ef6348546c3ac1d48f69a6100e9907df98e8b` e executada uma única vez no runtime head `bff49e947de78b63a716e7d9589e52b65b9d69ad`.

- run: `35248412098`, success;
- job: `105294374835`, success;
- artifact: `10508475804`;
- artifact ZIP SHA-256: `20c3c7261c88ba2896060fbfe8f5c2e99099c575891c4fc332e719fbf2cdafd7`;
- JSON SHA-256: `fb750704960cdb251c210f901fca3ba174831c493b155744a1a0f4e90d6dc244`;
- resultado canônico: `4656c5230475385cf0bae9e960d2362c2978b16bf5ce7e2ae6d5f1e2d864a295`;
- status: `PASS_TASK251_BOUNDED_OVERSIZED_RECOVERY`.

A TASK251 provou 7323 e 7324. A evidência já pinada da TASK249 prova 7321 e 7322. A TASK252 materializa a visão binária 4/4:

| edição | data | bytes | páginas | SHA-256 | prova |
|---:|---|---:|---:|---|---|
| 7321 | 09/09/2026 | 4.307.520 | 11 | `099732bf…dc89` | TASK249 |
| 7322 | 10/09/2026 | 83.485.292 | 109 | `30ce94f2…4993` | TASK249 |
| 7323 | 11/09/2026 | 126.648.737 | 438 | `058fd702…d940` | TASK251 |
| 7324 | 12/09/2026 | 15.890.080 | 64 | `66fbb723…194b` | TASK251 |

Total esperado exato: **230.331.629 bytes**.

Isso prova identidade/integridade binária e contagem de páginas. Ainda não prova o conteúdo semântico das quatro edições.

## Carrier de redigest

O carrier reutiliza o precedente geral da TASK219A:

`PDF temporário -> JournalPdfProcessor -> events_gold redigidos -> classificação semântica derivada -> âncoras administrativas fortes`

Antes de qualquer processamento, o runtime deve exigir por edição:

- URL final idêntica à URL pinada;
- HTTP 200;
- `application/pdf`;
- assinatura `%PDF-`;
- bytes exatamente iguais ao valor já provado;
- SHA-256 exatamente igual ao hash já provado;
- contagem de páginas exatamente igual ao valor já provado.

A validação acima transforma qualquer drift de fonte em STOP, em vez de aceitar silenciosamente uma nova versão do documento.

## Fronteira de rede

Um futuro runtime autorizado pode executar apenas:

- zero GETs de índice;
- quatro GETs documentais exatos;
- máximo 250 MiB por documento;
- agregado esperado/máximo: 230.331.629 bytes;
- zero retry;
- zero redirect;
- zero descoberta alternativa.

## Persistência permitida no artifact futuro

Somente:

- resumos documentais sanitizados;
- eventos `events_gold` já redigidos pelo pipeline;
- classificação semântica compacta;
- âncoras administrativas fortes determinísticas.

Permanecem proibidos:

- PDF bruto;
- texto bruto de página;
- chunks RAG;
- tarefas contábeis;
- Drive/Bronze/Silver/Gold materializado;
- serving/publicação/promoção;
- PNCP/TCE join;
- schedule/recorrência.

Uma âncora forte não equivale a uma cadeia de identidade ponta a ponta.

## Autorização

O workflow fica inerte em `main`. O runtime exige autorização nova, vinculada ao SHA exato da implementação TASK252 mesclada. Autorizações TASK249/TASK250/TASK251 não podem ser reutilizadas.

O runtime branch só pode divergir do SHA de implementação por:

- `runtime/task252_owner_authorization.json`;
- `runtime_triggers/task252_jom_7321_7324_general_redigest.run`.

## Próximo gate

Após um eventual live bem-sucedido, o resultado de redigest deve ser canonizado antes de qualquer join, serving, publicação ou promoção. Resultado parcial nunca autoriza inferência de ausência.
