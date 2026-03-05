# ── Controle B2 — Script de publicação de nova versão ──────────────────────────
# Uso: ./publicar_versao.ps1
# Requer: Node, Rust, VS Build Tools, gh CLI (GitHub CLI)

$KEY_FILE = "$env:USERPROFILE\.tauri\controle-b2.key"

if (-not (Test-Path $KEY_FILE)) {
    Write-Error "Chave privada não encontrada em $KEY_FILE"
    exit 1
}

# Lê a chave privada do arquivo
$env:TAURI_SIGNING_PRIVATE_KEY = Get-Content $KEY_FILE -Raw
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = "b2estoque"

# Pega a versão do tauri.conf.json
$conf = Get-Content "src-tauri\tauri.conf.json" | ConvertFrom-Json
$VERSION = $conf.version
Write-Host "Compilando versão v$VERSION..." -ForegroundColor Green

# Build (apenas NSIS para Windows — mais rápido que "all")
npm run tauri build -- --bundles nsis
if ($LASTEXITCODE -ne 0) { Write-Error "Build falhou"; exit 1 }

# Caminhos dos artefatos gerados pelo build
$BUNDLE = "src-tauri\target\release\bundle"
$SETUP  = "$BUNDLE\nsis\Controle B2_${VERSION}_x64-setup.exe"
$ZIP    = "$BUNDLE\nsis\Controle B2_${VERSION}_x64-setup.nsis.zip"
$ZIPSIG = "$ZIP.sig"

# Lê a assinatura e gera o latest.json para o auto-update
$SIG_CONTENT = Get-Content $ZIPSIG -Raw
$TAG = "v$VERSION"
$JSON_PATH = "$BUNDLE\nsis\latest.json"
$DOWNLOAD_URL = "https://github.com/drdssouza/estoque-b2/releases/download/$TAG/Controle.B2_${VERSION}_x64-setup.nsis.zip"

$latest = @{
    version  = $VERSION
    notes    = "Controle B2 $TAG - Atualização disponível"
    pub_date = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    platforms = @{
        "windows-x86_64" = @{
            signature = $SIG_CONTENT.Trim()
            url       = $DOWNLOAD_URL
        }
    }
} | ConvertTo-Json -Depth 5

$latest | Out-File -FilePath $JSON_PATH -Encoding utf8

Write-Host "Artefatos prontos:" -ForegroundColor Cyan
Write-Host "  Installer: $SETUP"
Write-Host "  ZIP:       $ZIP"
Write-Host "  Signature: $ZIPSIG"
Write-Host "  Manifest:  $JSON_PATH"

# Commit, tag e push
git add -A
git commit -m "chore: release $TAG" 2>$null
git tag $TAG
git push origin main --tags

# Cria o Release no GitHub com todos os artefatos
gh release create $TAG `
    "$SETUP" `
    "$ZIP" `
    "$ZIPSIG" `
    "${JSON_PATH}#latest.json" `
    --title "Controle B2 $TAG" `
    --notes "Atualização automática disponível. O sistema irá notificar os usuários."

Write-Host "`nPublicado com sucesso! v$VERSION já está disponível para atualização automática." -ForegroundColor Green
