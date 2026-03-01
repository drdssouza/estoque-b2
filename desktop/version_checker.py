import threading
import urllib.request
from PySide6.QtCore import QObject, Signal


def _is_newer(latest: str, current: str) -> bool:
    """Retorna True se latest > current usando comparação semântica (X.Y.Z)."""
    try:
        def to_tuple(v):
            return tuple(int(x) for x in v.strip().split('.'))
        return to_tuple(latest) > to_tuple(current)
    except Exception:
        return False


class VersionChecker(QObject):
    """Verifica atualizações em background sem bloquear a UI.

    Emite `update_available(latest_version)` na thread principal via
    conexão enfileirada do Qt (thread-safe por padrão).
    """

    update_available = Signal(str)  # versão mais nova disponível

    def __init__(self, current_version: str, check_url: str):
        super().__init__()
        self._current = current_version
        self._url = check_url

    def start(self):
        """Inicia a verificação em uma daemon thread (não bloqueia o encerramento)."""
        if not self._url:
            return
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            with urllib.request.urlopen(self._url, timeout=5) as resp:
                latest = resp.read().decode('utf-8').strip()
            if _is_newer(latest, self._current):
                self.update_available.emit(latest)
        except Exception:
            pass  # sem internet ou URL inválida — ignora silenciosamente
