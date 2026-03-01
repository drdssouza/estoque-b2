import sys
import webbrowser
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from desktop.ui.main_window import MainWindow
from desktop.version_checker import VersionChecker
from version import APP_VERSION, UPDATE_CHECK_URL, DOWNLOAD_URL, INSTALLER_URL


def _resolve_icon():
    """Retorna o caminho do icon.ico tanto em dev quanto no executável compilado."""
    if getattr(sys, 'frozen', False):
        # PyInstaller onedir: arquivos de dados ficam em sys._MEIPASS
        return Path(sys._MEIPASS) / 'icon.ico'
    return root_dir / 'icon.ico'


def _show_update_dialog(parent, latest_version):
    msg = QMessageBox(parent)
    msg.setWindowTitle("Atualizacao disponivel")
    msg.setIcon(QMessageBox.Information)
    msg.setText(
        f"Nova versao disponivel: <b>v{latest_version}</b><br>"
        f"Versao instalada: v{APP_VERSION}<br><br>"
        "Deseja baixar e instalar a atualizacao agora?"
    )
    msg.setStyleSheet("""
        QMessageBox { background-color: #ecf0f1; }
        QMessageBox QLabel { color: #2c3e50; font-size: 14px; min-width: 340px; }
        QPushButton {
            background-color: #27ae60; color: white;
            padding: 8px 20px; border-radius: 4px;
            font-size: 13px; font-weight: bold; min-width: 80px;
        }
        QPushButton:hover { background-color: #229954; }
    """)
    btn_update = msg.addButton("Atualizar agora", QMessageBox.AcceptRole)
    msg.addButton("Agora nao", QMessageBox.RejectRole)
    msg.exec()

    if msg.clickedButton() != btn_update:
        return

    # Quando rodando como .exe: download automático do instalador
    if getattr(sys, 'frozen', False) and INSTALLER_URL:
        from desktop.auto_updater import UpdateDownloadDialog
        url = INSTALLER_URL.format(version=latest_version)
        dlg = UpdateDownloadDialog(parent, latest_version, url)
        dlg.exec()
    else:
        # Em desenvolvimento: abre o navegador (sem instalador disponível)
        if DOWNLOAD_URL:
            webbrowser.open(DOWNLOAD_URL)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = _resolve_icon()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.showMaximized()

    # Verificação de versão em background — não bloqueia a inicialização.
    # Se não houver internet ou a URL estiver vazia, ignora silenciosamente.
    checker = VersionChecker(APP_VERSION, UPDATE_CHECK_URL)
    checker.update_available.connect(
        lambda latest: _show_update_dialog(window, latest)
    )
    checker.start()
    app._version_checker = checker  # evita coleta pelo GC antes do sinal disparar

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
