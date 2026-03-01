import sys
import webbrowser
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from PySide6.QtWidgets import QApplication, QMessageBox
from desktop.ui.main_window import MainWindow
from desktop.version_checker import VersionChecker
from version import APP_VERSION, UPDATE_CHECK_URL, DOWNLOAD_URL


def _show_update_dialog(parent, latest_version):
    msg = QMessageBox(parent)
    msg.setWindowTitle("Atualizacao disponivel")
    msg.setIcon(QMessageBox.Information)
    msg.setText(
        f"Nova versao disponivel: <b>v{latest_version}</b><br>"
        f"Versao instalada: v{APP_VERSION}<br><br>"
        "Deseja baixar a atualizacao agora?"
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
    btn_download = msg.addButton("Baixar atualizacao", QMessageBox.AcceptRole)
    msg.addButton("Agora nao", QMessageBox.RejectRole)
    msg.exec()
    if msg.clickedButton() == btn_download and DOWNLOAD_URL:
        webbrowser.open(DOWNLOAD_URL)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

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
