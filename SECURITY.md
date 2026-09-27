# Política de segurança

Este repositório usa separação explícita entre código público, credenciais privadas e gates de execução.

## Não publique segredos

Nunca abra issue, discussão, pull request, log ou artifact contendo tokens, refresh tokens, client secrets, senhas, cookies, chaves privadas, arquivos OAuth/ADC ou outros valores de autenticação. Nomes de secrets e exemplos vazios são permitidos; valores reais não são.

Se um segredo for exposto, a resposta correta é revogá-lo/rotacioná-lo e tratar o histórico afetado antes de divulgar o repositório. Apenas apagar o arquivo no commit mais recente não remove o valor do histórico Git.

## Relato de vulnerabilidade

Quando o recurso **Private vulnerability reporting** estiver habilitado no GitHub, prefira esse canal para falhas que possam permitir acesso indevido, execução com secrets, escrita/publicação não autorizada ou bypass de gates. Não inclua credenciais reais no relato.

Se o canal privado não estiver disponível, entre em contato com o mantenedor pelo perfil do GitHub sem publicar detalhes exploráveis ou segredos; combine um canal privado antes de enviar material sensível.

## Fronteiras de segurança do projeto

- credenciais ficam fora do repositório e são fornecidas por GitHub Actions/ambiente autorizado;
- Bronze é imutável por contrato;
- publicação é uma ação separada e explicitamente gated;
- T2/T3 e operações destrutivas não são autorizadas por contribuições de código;
- ausência, duplicidade ou drift de evidência deve falhar fechado;
- pull requests externos não devem receber secrets nem adquirir autoridade de execução remota.

Uma contribuição que altera autorização, escopo OAuth, permissões de workflow, persistência, publicação, overwrite/delete, recorrência ou scheduling exige revisão explícita de segurança.