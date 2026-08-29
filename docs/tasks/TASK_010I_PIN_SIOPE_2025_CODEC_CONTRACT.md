# TASK 010I-PIN — contrato reproduzível do codec CML/CZIP SIOPE 2025

## Resultado

`IDENTIFIED_REPRODUCIBLE_CODEC_CONTRACT_READY_FOR_IMPLEMENTATION`

Esta etapa não implementa ainda o decoder de produção. Ela apenas transforma em contrato canônico a descoberta que já havia sido reproduzida localmente, evitando que o Codex precise inferir detalhes ausentes.

## Por que esta etapa existe

A primeira tentativa de implementação da TASK 010I parou corretamente em:

`STOP_MISSING_PINNED_CODEC_CONTRACT`

O `main` ainda classificava o codec como `NOT_PROVEN`, embora a análise estática do instalador e a reprodução local já tivessem identificado um contrato capaz de decodificar todos os 146 containers do pacote entregue pelo proprietário.

O objetivo desta task é eliminar essa diferença entre descoberta local e evidência canônica.

## Handoff analisado sem execução

### Metadados 2025

- arquivo: `Metadados_Mun_2025.zip`;
- tamanho: `6.586.598` bytes;
- SHA-256: `41511c141e1af025ae2b565085583d6a3ab7b4577862f8ebdc308605101c1e5b`;
- 146 containers internos.

### Instalador

- nome recebido: `Siope_2025_Anual-25.0.5.6.exe.exe`;
- tamanho: `29.772.070` bytes;
- SHA-256: `3c85dd4195a31e67131b8e550509dc2d014ead3279bda26656192feeaac86bc2`;
- formato detectado: PE32/Inno Setup;
- string interna: `SIOPE Ano Base 2025 (Anual)`.

O instalador não foi executado. Nenhuma DLL foi carregada. Nenhum CML/CZIP foi executado.

## Contrato da chave

A constante usada na derivação é:

`Bkj$%3W`

A passphrase reproduzida para os metadados é vazia.

O comportamento de `TDCP_hash.UpdateStr` aplicado à `UnicodeString` usa `Length(Str)` como quantidade de bytes. Para `Bkj$%3W`, isso produz somente os primeiros sete bytes do UTF-16LE:

`42 00 6b 00 6a 00 24`

SHA-1:

`1ef164301c8949207c0066d3270407cae797b7c6`

A chave Blowfish de 256 bits é formada pelo digest de 20 bytes seguido de `0xFF` até 32 bytes:

`1ef164301c8949207c0066d3270407cae797b7c6ffffffffffffffffffffffff`

## IV e DCP1COMPAT

O comportamento compatível com DCPcrypt/DCP1COMPAT é:

1. criar oito bytes `FF`;
2. cifrar esse bloco em Blowfish-ECB com a chave acima;
3. usar o resultado como IV inicial.

IV reproduzido:

`69fbe9f873a4758b`

A implementação pública do DCPcrypt também documenta esse comportamento quando `DCP1COMPAT` está definido e não é fornecido um IV explícito.

## Header e framing

CML e CZIP usam o mesmo framing criptográfico observado.

- header: 32 bytes;
- o header corresponde à chave de 32 bytes cifrada em Blowfish-CBC com o IV inicial;
- header esperado:

`442d68fb56d3e72adb7e95e0f7b003795a1d3ae15f98ca334c7a557c58277593`

O ciphertext do payload começa no offset 32.

Não foi observado PKCS#5/PKCS#7 padding no framing reproduzido.

A saída decifrada é diretamente um ZIP interno.

## Streaming que reproduz o pacote real

O decoder deve reproduzir literalmente o comportamento observado:

- leitura em chunks de `0x401` (`1025`) bytes;
- blocos completos de 8 bytes: CBC normal;
- CV carregado = último ciphertext completo;
- resto de 1 a 7 bytes: `EncryptECB(CV)` fornece o keystream, aplicado por XOR apenas aos bytes restantes;
- o resto parcial não substitui o CV carregado para o chunk seguinte;
- o próximo chunk continua a partir do último ciphertext completo anterior.

Essa regra não deve ser substituída por uma API genérica de CBC com padding.

## Reprodução local

Usando somente leitura de bytes e parsing offline:

- headers exatos: `146/146`;
- containers que produziram ZIP válido: `146/146`;
- ZIPs internos com CRC válido: `146/146`;
- falhas: `0`.

Exemplos:

- `Metadados.cml` → ZIP contendo `Metadados.xml`;
- `Dados_Municipio.cml` → ZIP contendo `Dados_Municipio.xml`;
- os dois `.czip` também produzem ZIPs válidos.

Nenhum byte oficial decodificado é versionado por esta task.

## Relação com DCPcrypt

Como referência pública complementar, o código-fonte do DCPcrypt mostra:

- `TDCP_hash.UpdateStr` chamando `Update(Str[1], Length(Str))`;
- `DCP1COMPAT` preenchendo o IV implícito com `0xFF` antes de `EncryptECB`;
- tratamento de resto inferior a um bloco com `EncryptECB(CV)` e XOR.

Referências de apoio:

- `https://github.com/SnakeDoctor/DCPcrypt/blob/master/DCPcrypt2.pas`
- `https://github.com/SnakeDoctor/DCPcrypt/blob/master/DCPblockciphers.pas`

Essas fontes complementam a análise; a prova operacional do contrato desta task é a reprodução `146/146` no pacote observado.

## Limites semânticos

Identificar o codec não prova automaticamente o significado de `NUM_POPU` nem dos aliases financeiros.

Portanto permanecem:

- `S1_NUM_POPU = NOT_PROVEN`;
- `S2_FINANCIAL_ALIAS_BRIDGE = NOT_PROVEN`;
- `annual_closure_status = UNKNOWN`;
- `semantic_comparability_status = UNKNOWN`;
- `gold_metrics_status = UNKNOWN/BLOCKED`;
- série anual fechada = `2016–2024`;
- `2026 = UNPROVEN_CURRENT_YEAR`.

## Próximo gate

O próximo gate permitido é somente:

`IMPLEMENT_LITERAL_OFFLINE_DECODER_AND_REPRODUCE_146_OF_146`

A implementação deve usar fixtures sintéticas versionadas/runtime-only e aceitar o pacote real apenas como input local opcional. Instalador, ZIP oficial, CML/CZIP e XMLs reais não devem ser commitados.

Somente depois da implementação e reprodução independente pelo código do repositório poderá existir review semântico separado para S1/S2.
