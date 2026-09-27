# M4B — autorização do Google Drive para o Python externo

O Google Drive conectado ao ChatGPT e o programa Python são clientes diferentes. O software externo precisa de autorização própria.

## Opção A — acesso ao Drive atual

Use o escopo:

`https://www.googleapis.com/auth/drive`

Ele permite ao robô ler/escrever o repositório já existente, mas é um escopo amplo/restrito. Para um projeto privado de teste, deve ser configurado no Google Cloud e autorizado conscientemente; para distribuição pública existem exigências adicionais de verificação.

## Opção B — acesso mínimo para arquivos controlados pelo app

Use:

`https://www.googleapis.com/auth/drive.file`

É mais restrito, mas o app só acessa arquivos que ele próprio cria ou que forem explicitamente abertos/compartilhados com ele via fluxo apropriado. Para usar esta opção de maneira limpa, o ideal é criar um repositório dedicado controlado pelo próprio app e migrar a semente para ele.

## Opção C — leitura estrita para gates no-click

Use:

`https://www.googleapis.com/auth/drive.readonly`

Esse escopo é a opção preferida para gates classificados como `T1_REMOTE_READONLY`: eles podem listar metadados e baixar objetos existentes, mas a credencial não deve possuir capacidade de criar, atualizar ou excluir arquivos.

A existência de código que só chama GET **não basta** para autorizar auto-run se o refresh token usado pelo workflow tiver sido emitido com escopo mais amplo. Por isso, a credencial read-only deve ser gerada separadamente e nunca substituir silenciosamente a credencial de escrita já usada pelos gates persistentes.

## Bootstrap recomendado em computador local

1. Criar/selecionar projeto no Google Cloud.
2. Ativar Google Drive API.
3. Configurar a tela de consentimento OAuth.
4. Criar um cliente OAuth do tipo Desktop app.
5. Para runtime com escrita já autorizada, executar uma única vez:

```bash
python scripts/oauth_bootstrap_drive.py --client-id SEU_CLIENT_ID --client-secret SEU_CLIENT_SECRET --scope drive --output fora_do_git/tokens.json
```

6. Para um gate estritamente read-only, gerar outro refresh token com `--scope drive.readonly`.
7. Guardar cada refresh token como secret distinto do executor em nuvem.
8. Nunca enviar token JSON, client secret ou refresh token para Git.

O helper local usa navegador + callback local em `127.0.0.1`, PKCE e `access_type=offline`.

## Bootstrap M8 no Google Cloud Shell

A versão atual do `gcloud` rejeita a combinação `--no-launch-browser` com `--client-id-file`. O fluxo `--no-browser` exige uma segunda máquina com navegador **e** gcloud instalado, portanto não resolve o caso de uso em que o usuário opera somente pelo navegador e pelo Cloud Shell.

Para o M8, o caminho Cloud Shell usa um OAuth client **dedicado do tipo Aplicativo da Web** e o proxy autenticado de Web Preview do próprio Cloud Shell.

Primeiro obtenha o URI exato da sessão:

```bash
python3 scripts/bootstrap_m8_readonly_secret_cloudshell.py --print-redirect-uri
```

No Google Cloud, crie um novo OAuth 2.0 Client ID do tipo **Aplicativo da Web** e cadastre exatamente o URI impresso como **URI de redirecionamento autorizado**. Não reutilize o Desktop client histórico para esse fluxo.

Depois execute:

```bash
python3 scripts/bootstrap_m8_readonly_secret_cloudshell.py
```

O helper:

1. exige o ambiente oficial do Cloud Shell por meio de `WEB_HOST` e usa a porta 8080 do Web Preview;
2. pede o Web Client ID e o Client Secret apenas no terminal; o secret usa entrada oculta;
3. solicita somente `https://www.googleapis.com/auth/drive.readonly`, `access_type=offline` e `prompt=consent`;
4. recebe o callback por HTTPS no proxy autenticado do Cloud Shell e valida `state` exatamente;
5. troca o código por tokens sem gravar arquivo de token;
6. exige escopo exatamente read-only tanto na resposta OAuth, quando presente, quanto no `tokeninfo` do access token;
7. cria por stdin três Repository Secrets dedicados:
   - `GOOGLE_DRIVE_READONLY_CLIENT_ID`
   - `GOOGLE_DRIVE_READONLY_CLIENT_SECRET`
   - `GOOGLE_DRIVE_READONLY_REFRESH_TOKEN`
8. verifica apenas os nomes dos secrets por `gh secret list`;
9. nunca imprime client secret, refresh token ou access token.

Esse helper **não executa o M8**, **não autoriza no-click**, **não publica dados** e **não autoriza batch futuro**.

### Checkpoint read-only provisionado

O helper Cloud Shell já concluiu com `PASS_M8_READONLY_SECRETS_PROVISIONED`, escopo `drive.readonly` e prova `token_response_and_tokeninfo_exact`, sem expor valores de secrets e sem persistir arquivo de token.

O workflow M8 agora mapeia somente os três secrets dedicados para as variáveis esperadas pelo cliente Drive. Antes de qualquer lookup/download, ele executa:

```bash
python scripts/github_m8_readonly_credential_capability_gate.py
```

Esse gate troca o refresh token por um access token, consulta `tokeninfo` e falha se o escopo não for **exatamente** `drive.readonly`. Ele não chama a Drive API e não prova a capacidade por tentativa de escrita.

A primeira execução live do M8 **continua manual**. `workflow_call`, no-click, publicação e batch futuro permanecem bloqueados até a prova live e uma revisão posterior da policy.

## Bootstrap M8 em Windows local

Se um dia o repositório estiver disponível localmente, continua existindo o wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_m8_readonly_secret.ps1
```

Esse caminho local usa o Desktop client e permanece separado do fluxo Cloud Shell.

## Produção — credencial com escrita

O runtime histórico recebe:

- `GOOGLE_DRIVE_CLIENT_ID`
- `GOOGLE_DRIVE_CLIENT_SECRET`
- `GOOGLE_DRIVE_REFRESH_TOKEN`

O módulo `storage/drive_rest.py` renova access tokens automaticamente e usa a API REST do Drive sem biblioteca externa.

## Produção — credencial somente leitura

Para isolamento de capacidade, o caminho M8 usa o trio dedicado:

- `GOOGLE_DRIVE_READONLY_CLIENT_ID`
- `GOOGLE_DRIVE_READONLY_CLIENT_SECRET`
- `GOOGLE_DRIVE_READONLY_REFRESH_TOKEN`

**Estado em 0.8.0:** credencial read-only provisionada e comprovada no bootstrap; wiring dedicado preparado; primeira prova live do produto ainda pendente e obrigatoriamente manual. A retirada do clique só poderá ser considerada em gate/PR posterior após auditoria dessa primeira execução.

## Fontes oficiais consultadas na especificação

- Google OAuth 2.0 for Web Server Applications: https://developers.google.com/identity/protocols/oauth2/web-server
- Google Drive API scopes: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Google Cloud Shell Web Preview: https://cloud.google.com/shell/docs/using-web-preview
- gcloud ADC login: https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login
- GitHub CLI `gh secret set`: https://cli.github.com/manual/gh_secret_set
