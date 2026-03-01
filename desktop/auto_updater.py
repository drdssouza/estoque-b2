"""
Auto-updater: baixa o instalador do GitHub Releases e o executa silenciosamente.

Fluxo:
  1. UpdateDownloadDialog é aberta com a URL do instalador.
  2. Um QThread faz o download com progresso.
  3. Ao terminar, executa o instalador com /SILENT /NORESTART.
  4. O app fecha para que o instalador possa sobrescrever os arquivos.
"""
import os
import sys
import tempfile
import subprocess

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                                QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
import urllib.request


class _DownloadThread(QThread):
    """QThread que baixa um arquivo e emite progresso para a UI principal."""

    progress = Signal(int)   # 0-100
    finished = Signal(str)   # caminho do arquivo baixado
    error    = Signal(str)   # mensagem de erro

    def __init__(self, url: str, dest: str):
        super().__init__()
        self._url  = url
        self._dest = dest

    def run(self):
        try:
            def _hook(block_count, block_size, total_size):
                if total_size > 0:
                    pct = min(100, int(block_count * block_size * 100 / total_size))
                    self.progress.emit(pct)

            urllib.request.urlretrieve(self._url, self._dest, reporthook=_hook)
            self.progress.emit(100)
            self.finished.emit(self._dest)
        except Exception as e:
            self.error.emit(str(e))


class UpdateDownloadDialog(QDialog):
    """Dialogo de progresso de download + execução do instalador."""

    def __init__(self, parent, version: str, installer_url: str):
        super().__init__(parent)
        self._version = version
        self._url     = installer_url
        self._dest    = None
        self._thread  = None

        self.setWindowTitle(f"Atualizando para v{version}")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setFixedHeight(190)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        self._setup_ui()
        self._start_download()

    # ── UI ───────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(14)

        self._status = QLabel(f"Baixando versão {self._version}…")
        self._status.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(self._status)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        self._bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7; border-radius: 5px;
                background-color: white; height: 24px;
                text-align: center; font-size: 12px; color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #27ae60; border-radius: 3px;
            }
        """)
        layout.addWidget(self._bar)

        self._note = QLabel("O aplicativo será fechado automaticamente para instalar.")
        self._note.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        layout.addWidget(self._note)

        btn_row = QHBoxLayout()
        self._btn_cancel = QPushButton("Cancelar")
        self._btn_cancel.setFixedHeight(36)
        self._btn_cancel.setCursor(Qt.PointingHandCursor)
        self._btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6; color: white;
                padding: 6px 20px; border-radius: 4px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        self._btn_cancel.clicked.connect(self._cancel)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_cancel)
        layout.addLayout(btn_row)

    # ── DOWNLOAD ──────────────────────────────────────────────────────

    def _start_download(self):
        fd, self._dest = tempfile.mkstemp(suffix='.exe', prefix='controle_b2_update_')
        os.close(fd)

        self._thread = _DownloadThread(self._url, self._dest)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_progress(self, pct: int):
        self._bar.setValue(pct)
        self._status.setText(f"Baixando versão {self._version}… {pct}%")

    def _on_finished(self, path: str):
        self._status.setText("Iniciando instalação…")
        self._btn_cancel.setEnabled(False)

        try:
            subprocess.Popen([path, '/SILENT', '/NORESTART'])
        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao instalar",
                f"Não foi possível iniciar o instalador:\n{e}"
            )
            self.reject()
            return

        # Fechar o app para liberar os arquivos antes do instalador sobrescrever
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()

    def _on_error(self, msg: str):
        QMessageBox.critical(
            self, "Erro no download",
            f"Não foi possível baixar a atualização:\n{msg}\n\n"
            "Baixe manualmente em:\ngithub.com/drdssouza/estoque-b2/releases"
        )
        self._cleanup()
        self.reject()

    def _cancel(self):
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait(2000)
        self._cleanup()
        self.reject()

    def _cleanup(self):
        try:
            if self._dest and os.path.exists(self._dest):
                os.remove(self._dest)
        except Exception:
            pass

    def closeEvent(self, event):
        self._cancel()
        event.accept()
