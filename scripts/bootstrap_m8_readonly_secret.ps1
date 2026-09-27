$ErrorActionPreference = 'Stop'

# Local-only helper for Windows. It prompts for OAuth client credentials without
# writing them to disk, delegates browser OAuth + GitHub secret storage to the
# Python helper, then clears the temporary environment variables.

function ConvertFrom-SecureStringPlainText([Security.SecureString] $Secure) {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python não encontrado no PATH.'
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) não encontrado no PATH.'
}

gh auth status --hostname github.com
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI não está autenticado. Execute gh auth login antes deste helper.'
}

$clientId = Read-Host 'Google OAuth Desktop Client ID'
$secureClientSecret = Read-Host 'Google OAuth Desktop Client Secret' -AsSecureString
$clientSecret = ConvertFrom-SecureStringPlainText $secureClientSecret

try {
    $env:GOOGLE_DRIVE_CLIENT_ID = $clientId
    $env:GOOGLE_DRIVE_CLIENT_SECRET = $clientSecret

    python scripts/bootstrap_m8_readonly_secret.py --repo ferinbon-cpu/robo-dados-publicos
    if ($LASTEXITCODE -ne 0) {
        throw 'Provisioning read-only terminou em STOP. O secret não deve ser considerado pronto.'
    }
}
finally {
    Remove-Item Env:GOOGLE_DRIVE_CLIENT_ID -ErrorAction SilentlyContinue
    Remove-Item Env:GOOGLE_DRIVE_CLIENT_SECRET -ErrorAction SilentlyContinue
    $clientSecret = $null
    $secureClientSecret = $null
    $clientId = $null
}
