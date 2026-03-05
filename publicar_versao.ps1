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
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = ""

# Pega a versão do tauri.conf.json
$conf = Get-Content "src-tauri\tauri.conf.json" | ConvertFrom-Json
$VERSION = $conf.version
Write-Host "Compilando versão v$VERSION..." -ForegroundColor Green

# Build
npm run tauri build
if ($LASTEXITCODE -ne 0) { Write-Error "Build falhou"; exit 1 }

# Caminhos dos artefatos
$BUNDLE = "src-tauri\target\release\bundle"
$SETUP  = "$BUNDLE\nsis\Controle B2_${VERSION}_x64-setup.exe"
$SIG    = "$SETUP.sig"
$JSON   = "$BUNDLE\updater\latest.json"   # gerado automaticamente pelo tauri build

Write-Host "Artefatos gerados:" -ForegroundColor Cyan
Write-Host "  Installer: $SETUP"
Write-Host "  Signature: $SIG"
Write-Host "  Manifest:  $JSON"

# Cria tag e release no GitHub
$TAG = "v$VERSION"
git add -A
git commit -m "chore: release $TAG" 2>$null
git tag $TAG
git push origin main --tags

gh release create $TAG `
    "$SETUP" `
    "$SIG" `
    "$JSON#latest.json" `
    --title "Controle B2 $TAG" `
    --notes "Atualização automática disponível. O sistema irá notificar os usuários."

Write-Host "`nPublicado com sucesso! v$VERSION já esta disponivel para atualização automatica." -ForegroundColor Green
