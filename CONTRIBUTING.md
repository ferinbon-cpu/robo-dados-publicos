# Contribuindo

Contribuições são bem-vindas quando preservam as fronteiras de segurança e a rastreabilidade do projeto.

## Regras essenciais

1. Não envie tokens, client secrets, refresh tokens, senhas, cookies, chaves privadas, `.env`, arquivos OAuth/ADC ou dumps de credenciais.
2. Não inclua dados pessoais desnecessários, bases restritas ou cópias integrais de materiais de terceiros sem direito de redistribuição.
3. Prefira fixtures sintéticas e pequenas. Dados públicos usados como evidência devem manter proveniência e limites de redistribuição claros.
4. Pull requests não autorizam coleta, persistência, publicação, overwrite/delete, recorrência ou scheduling. A autoridade vem dos contracts/gates apropriados.
5. Workflows de pull request devem operar com permissões mínimas e sem secrets. `pull_request_target`, `secrets: inherit` e permissões amplas exigem revisão de segurança e não devem ser introduzidos como atalho.
6. Mudanças que alterem semântica fiscal/educacional devem manter a separação entre extração, transformação determinística e interpretação; não promover automaticamente conclusões de compliance, MDE/Fundeb ou identidades fiscais.

## Fluxo recomendado

- crie uma branch;
- faça mudanças pequenas e auditáveis;
- adicione/atualize testes;
- execute os gates offline;
- abra pull request descrevendo efeitos permitidos e explicitamente não autorizados;
- aguarde os checks obrigatórios antes do merge.

## Repositório público e forks

Código vindo de forks deve ser tratado como não confiável. CI de pull request não deve depender de secrets do repositório. Workflows que usam credenciais remotas permanecem separados e sujeitos às regras de autorização do projeto.

## Licenciamento

A visibilidade pública, por si só, não concede licença de reutilização. Consulte o arquivo de licença quando ele existir; até uma decisão explícita do mantenedor, não presuma direitos além dos concedidos pela legislação aplicável.