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

A existência de código que só chama GET **não basta** para autorizar auto-run se o refresh token usado pelo workflow tiver sido emitido com escopo mais amplo. Por isso, o token read-only deve ser gerado separadamente e nunca substituir silenciosamente o token de escrita já usado pelos gates persistentes.

## Bootstrap recomendado

1. Criar/selecionar projeto no Google Cloud.
2. Ativar Google Drive API.
3. Configurar a tela de consentimento OAuth.
4. Criar um cliente OAuth do tipo Desktop app.
5. Para runtime com escrita já autorizada, executar uma única vez:

```bash
python scripts/oauth_bootstrap_drive.py --client-id SEU_CLIENT_ID --client-secret SEU_CLIENT_SECRET --scope drive --output fora_do_git/tokens.json
```

6. Para um gate estritamente read-only, gerar **outro refresh token**:

```bash
python scripts/oauth_bootstrap_drive.py --client-id SEU_CLIENT_ID --client-secret SEU_CLIENT_SECRET --scope drive.readonly --output fora_do_git/tokens_readonly.json
```

7. Guardar cada `refresh_token` como secret distinto do executor em nuvem.
8. Nunca enviar `tokens.json`, `tokens_readonly.json`, client secret ou refresh token para GitHub/Drive público.

O script usa navegador + callback local em `127.0.0.1`, PKCE e `access_type=offline`.

## Produção — credencial com escrita

O runtime histórico recebe secrets por ambiente/secret manager:

- `GOOGLE_DRIVE_CLIENT_ID`
- `GOOGLE_DRIVE_CLIENT_SECRET`
- `GOOGLE_DRIVE_REFRESH_TOKEN`

O módulo `storage/drive_rest.py` renova access tokens automaticamente e usa a API REST do Drive sem biblioteca externa.

## Produção — credencial somente leitura

A política de automação reserva o nome:

- `GOOGLE_DRIVE_READONLY_REFRESH_TOKEN`

O cliente e o secret podem continuar usando o mesmo OAuth client ID/secret; o que precisa ser separado é o refresh token emitido com `drive.readonly`.

**Estado em 0.8.0:** o bootstrap já suporta `drive.readonly`, mas o workflow M8 ainda usa a credencial histórica e permanece manual. A troca para o secret read-only e a retirada do clique só podem ocorrer em gate/PR posterior, depois que a nova credencial existir e for comprovada.

## Fontes oficiais consultadas na especificação

- Google OAuth 2.0 for iOS & Desktop Apps: https://developers.google.com/identity/protocols/oauth2/native-app
- Google Drive API scopes: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
