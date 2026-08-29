# TASK 010J — decoder offline CML/CZIP SIOPE 2025

## Resultado

`LITERAL_OFFLINE_DECODER_IMPLEMENTED_SYNTHETICALLY_VALIDATED`

Esta task transforma o contrato canônico pinado em um parser Python offline. Ela não redescobre o algoritmo, não executa containers ou conteúdo interno, não acessa rede e não promove conclusões semânticas.

## Contrato reproduzido

A implementação valida a derivação SHA-1 peculiar de `UnicodeString`, a chave Blowfish de 32 bytes, o IV implícito DCP1COMPAT, o header cifrado de 32 bytes e o payload no offset 32. A decodificação lê chunks lógicos de 1025 bytes: blocos completos usam CBC com continuidade pelo último bloco cifrado completo; cada resto de 1 a 7 bytes usa XOR com o prefixo de `EncryptECB(CV)` e não avança o CV. Não há padding PKCS#5/PKCS#7.

O arquivo `config/siope_2025_cml_czip_codec_contract.v1.json` continua sendo a fonte normativa. Derivações intermediárias e constantes calculadas são comparadas ao contrato e qualquer drift termina em `STOP_TASK_010J_*`.

## Inspeção segura

O ZIP interno é processado somente em memória e nunca extraído. A inspeção:

- exige assinatura ZIP;
- verifica CRC;
- bloqueia path traversal, caminhos absolutos e symlinks;
- aplica limites de quantidade, profundidade, tamanho por entrada, tamanho total e taxa de compressão;
- aceita somente XML no ZIP decodificado;
- rejeita declarações DTD e entity antes de qualquer análise XML;
- retorna somente nomes, tamanhos e hashes, sem imprimir conteúdo XML.

A CLI recebe um caminho local explícito. Ela não procura nem baixa artefatos e não persiste bytes decodificados.

## Testes sintéticos

Os testes constroem ZIPs e containers determinísticos em runtime, incluindo CML e CZIP, limites exatos de chunk, múltiplos chunks, todos os tipos de remainder e casos fail-closed de framing, corrupção, CRC, paths e limites. Nenhum CML, CZIP, XML ou ZIP oficial foi versionado.

## Validação do pacote real

`REAL_PACKAGE_VALIDATION = NOT_RUN_LOCAL_ARTIFACT_UNAVAILABLE`

O arquivo local `Metadados_Mun_2025.zip` com SHA-256 esperado `41511c141e1af025ae2b565085583d6a3ab7b4577862f8ebdc308605101c1e5b` não estava disponível nesta implementação. Portanto, os resultados históricos pinados de 146 containers, 146 headers, 146 ZIPs e 146 CRCs **não** são reivindicados como reproduzidos por este código.

## Estados preservados

- `0.7.0 = ACTIVE`;
- `0.8.0 = CANDIDATE`;
- `2025 = PROVEN_STRUCTURAL_RECENT`;
- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série anual fechada = `2016-2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Limites e próximo gate

Esta task não decide `NUM_POPU`, os dez aliases financeiros, o fechamento anual ou Gold 2025. Não expande a série e não habilita recorrência. O próximo gate permitido é somente review semântico offline separado de `NUM_POPU` e dos dez aliases, depois da aceitação do parser. Gold 2025 permanece bloqueado.
