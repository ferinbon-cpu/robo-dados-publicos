# M4B — autorização do Google Drive para o Python externo

O Google Drive conectado ao ChatGPT e o programa Python são clientes diferentes. O software externo precisa de autorização própria.

## Opção A — acesso ao Drive atual

Use o escopo:

`https://www.googleapis.com/auth/drive`

Ele permite ao robô ler/escrever o repositório já existente, mas é um escopo amplo/restrito. Para um projeto privado de teste, deve ser configurado no Google Cloud e autorizado conscientemente; para distribuição pública existem exigências adicionais de verificação.

## Opção B — acesso mínimo

Use:

`https://www.googleapis.com/auth/drive.file`

É mais restrito, mas o app só acessa arquivos que ele próprio cria ou que forem explicitamente abertos/compartilhados com ele via fluxo apropriado. Para usar esta opção de maneira limpa, o ideal é criar um repositório dedicado controlado pelo próprio app e migrar a semente para ele.

## Bootstrap recomendado

1. Criar/selecionar projeto no Google Cloud.
2. Ativar Google Drive API.
3. Configurar a tela de consentimento OAuth.
4. Criar um cliente OAuth do tipo Desktop app.
5. Executar uma única vez:

```bash
python scripts/oauth_bootstrap_drive.py --client-id SEU_CLIENT_ID --client-secret SEU_CLIENT_SECRET --scope drive --output fora_do_git/tokens.json
```

6. Guardar o `refresh_token` como secret do executor em nuvem.
7. Nunca enviar `tokens.json`, client secret ou refresh token para GitHub/Drive público.

O script usa navegador + callback local em `127.0.0.1`, PKCE e `access_type=offline`.

## Produção

O runtime deverá receber apenas secrets por ambiente/secret manager:

- `GOOGLE_DRIVE_CLIENT_ID`
- `GOOGLE_DRIVE_CLIENT_SECRET`
- `GOOGLE_DRIVE_REFRESH_TOKEN`

O módulo `storage/drive_rest.py` renova access tokens automaticamente e usa a API REST do Drive sem biblioteca externa.

## Fontes oficiais consultadas na especificação

- Google OAuth 2.0 for iOS & Desktop Apps: https://developers.google.com/identity/protocols/oauth2/native-app
- Google Drive API scopes: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
