# TASK 010H — handoff humano e caracterização offline do codec CML/CZIP

## Resultado

O arquivo `Metadados_Mun_2025.zip` foi recebido por handoff humano e analisado somente de forma estática/offline. O binário não é versionado no repositório.

A classificação inicial permanece `USER_MEDIATED_OFFICIAL_DOWNLOAD_CANDIDATE`. O hash calculado sobre os bytes recebidos é:

`41511c141e1af025ae2b565085583d6a3ab7b4577862f8ebdc308605101c1e5b`

Tamanho: `6,586,598` bytes.

A origem relatada é a superfície oficial FNDE/SIOPE Downloads, opção Municipal → Metadados de 2025. Como não há checksum oficial independente pinado e o status de autenticação do navegador não foi explicitamente reportado, o handoff não é promovido automaticamente a `PROVEN_OFFICIAL_BYTES`.

## Segurança estrutural do ZIP externo

O arquivo é um ZIP válido com 146 entradas:

- 144 `.cml`;
- 2 `.czip`;
- zero path traversal;
- zero caminhos absolutos;
- zero symlinks;
- zero membros marcados como criptografados pelo próprio ZIP;
- todos os membros usam DEFLATE;
- total lógico: `6,567,382` bytes;
- total comprimido: `6,569,922` bytes.

Os timestamps internos vão de `2026-08-27 01:33:34` a `2026-08-27 01:43:56`. O formato ZIP não fornece timezone suficiente para inferir fuso; portanto esses valores são preservados apenas como timestamps locais do archive.

## Codec/container interno

Os `.cml` e `.czip` não são texto claro nem ZIP padrão por assinatura. Arquivos maiores apresentam entropia próxima de 8 bits/byte e o ZIP externo não consegue comprimi-los de forma útil. Isso é compatível com conteúdo previamente comprimido, cifrado ou ofuscado, mas não prova algoritmo específico.

Todos os 144 `.cml` compartilham um prefixo binário comum de 40 bytes:

`442d68fb56d3e72adb7e95e0f7b003795a1d3ae15f98ca334c7a557c58277593163a4cf918d59be1`

Os dois `.czip` compartilham os primeiros 32 bytes com os `.cml`, mas seguem com sequência distinta. Não atribuir significado a esses bytes sem prova do codec.

Uma busca literal nos bytes codificados não encontrou `NUM_POPU`, `VAL_RECE_REAL`, `VAL_DESP_EMPE`, `Municipal` ou `2025`. Esse resultado **não prova ausência** desses conceitos: o conteúdo ainda não foi decodificado.

## Arquivos internos promissores

O inventário contém nomes que tornam o pacote altamente relevante para a auditoria semântica futura, incluindo:

- `Metadados.cml`;
- `ME_Item.cml`;
- `ME_Pasta_Coluna.cml`;
- `ME_Valores_FUNDEB.cml`;
- `ME_Valores_INEP.cml`;
- `ME_Valores_MDE.cml`;
- `Dados_Municipio.cml`;
- `Periodo.cml`;
- `Parametro.cml`;
- `RREO_FUNDEB_Municipal_2025.czip`;
- `RREO_Municipal_2025.czip`.

Nomes de arquivo, entretanto, não são bridge semântica.

## Próximo gate

A próxima etapa deve permanecer offline/read-only e tentar identificar um leitor reproduzível para `.cml/.czip` sem executar conteúdo do pacote.

Ordem preferida:

1. procurar leitor/codec já existente no repositório — busca atual não encontrou implementação;
2. caracterizar estruturalmente o container;
3. obter, se necessário por handoff humano, um artefato oficial do software SIOPE para **análise estática apenas**, sem execução, procurando rotinas/strings/bibliotecas responsáveis por abrir `.cml/.czip`;
4. opcionalmente usar um pacote histórico manualmente obtido, preferencialmente 2024, para comparação binária e validação de continuidade do codec;
5. somente depois implementar decoder offline reproduzível;
6. somente depois inspecionar `NUM_POPU` e os dez aliases;
7. promoção semântica, se houver, exige review/gate separado.

## Estado canônico preservado

- `0.7.0 = ACTIVE`;
- `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- fechamento 2025 = `UNKNOWN`;
- comparabilidade = `UNKNOWN`;
- Gold 2025 = `UNKNOWN/BLOCKED`;
- série fechada = `2016–2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

A evidência sanitizada correspondente está em `docs/evidence/TASK_010H_SIOPE_2025_USER_HANDOFF_CODEC_CHARACTERIZATION_0.8.0.json`.
