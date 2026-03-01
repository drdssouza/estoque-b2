APP_VERSION = "1.1.0"

# ─── COMO CONFIGURAR O VERIFICADOR DE VERSÃO ──────────────────────────────────
#
# 1. Suba este projeto no GitHub (repositório público ou privado).
#
# 2. O arquivo "latest_version.txt" (na raiz do projeto) contém apenas
#    o número da versão mais recente, ex: 1.2.0
#    Atualize esse arquivo a cada novo release.
#
# 3. Copie o link "Raw" do latest_version.txt no GitHub:
#    https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/latest_version.txt
#    e cole abaixo em UPDATE_CHECK_URL.
#
# 4. Em DOWNLOAD_URL, coloque o link da página de releases ou do instalador:
#    https://github.com/SEU_USUARIO/SEU_REPO/releases/latest
#
# Deixe as strings vazias para desativar a verificação.
# ──────────────────────────────────────────────────────────────────────────────

UPDATE_CHECK_URL = "https://raw.githubusercontent.com/drdssouza/estoque-b2/main/latest_version.txt"
DOWNLOAD_URL     = "https://github.com/drdssouza/estoque-b2/releases/latest"
