# TASK 016 — intake offline de respostas autoritativas FNDE

## Escopo congelado

Esta tarefa é **somente preparatória e T0/offline**. Nenhuma resposta oficial foi recebida ou ingerida, nenhuma rede externa ou Google Drive foi usado e B1, B2 e B3 continuam `PENDING`. A evidência canônica TASK 011 e sua decisão `KEEP_B1_B2_B3_PENDING_NO_PROMOTION` não são alteradas.

O contrato em `config/fnde_authoritative_response_intake.v1.json` fixa protocolos, proposições ordenadas, estados permitidos, limites de excerto e o estado canônico sem promoção. O gate determinístico valida um intake por vez; ele não lê semanticamente uma resposta e não decide blockers.

## Modelo em duas etapas

1. **Revisão humana/offline:** depois de um handoff explícito de evidência real, o revisor registra cada proposição, um excerto mínimo sanitizado, localização exata e nota de avaliação. Conteúdo omitido não é inferido.
2. **Gate determinístico:** valida identidade, metadados do artefato, proveniência declarada, mapeamento integral, allowlists, privacidade, completude e ausência de promoção. Não usa LLM, rede nem mutação remota.

Uma resposta real somente pode declarar `AUTHORITATIVE_PROVEN` quando `provenance_checks` registra deterministicamente o handoff oficial mediado pelo usuário, o rótulo de autoridade observado, o protocolo exato observado, a verificação do hash bruto e a conclusão da revisão humana offline. Essa declaração prova apenas a suficiência estrutural da proveniência do intake, nunca o conteúdo substantivo do blocker. Fixtures usam uma estrutura de proveniência sintética distinta.

`INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW` significa apenas que a evidência está estruturada para uma **tarefa de decisão posterior e explícita**. Não significa `BLOCKER_PROVEN`: receber um artefato, reconhecer sua autoridade ou encontrar uma frase de apoio não responde automaticamente todas as proposições.

## Limite de privacidade do repositório público

O artefato bruto futuro deve permanecer fora do GitHub e ser representado somente por SHA-256, tamanho, MIME, data, protocolo e descrição sanitizada. Não se deve commitar automaticamente nomes, CPF, contatos, endereços, dados de conta/sessão, cookies, tokens, cabeçalhos de autenticação ou URLs privadas. Somente excertos mínimos que apoiem proposições podem ser candidatos a evidência pública. O gate rejeita commits de artefato bruto, excertos longos e padrões óbvios de dados pessoais ou secrets; ele não é um DLP geral nem faz OCR/aquisição.

Use o template em `docs/evidence/templates/TASK_016_FNDE_AUTHORITATIVE_RESPONSE_INTAKE_TEMPLATE.json`, copie identidades literalmente do contrato e execute:

```bash
python scripts/github_task_016_fnde_authoritative_response_intake_gate.py caminho/do/intake.json
```

Os fixtures são explicitamente sintéticos, não vieram do FNDE, não contêm dados pessoais reais e não promovem estado. A série fechada permanece 2016–2024, Gold 2025 permanece `UNKNOWN/BLOCKED`, 0.8.0 permanece `CANDIDATE`, e os estados semânticos/2025 permanecem congelados conforme o contrato.
