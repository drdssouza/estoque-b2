import shutil
from pathlib import Path
from datetime import datetime


class BackupController:
    def __init__(self, data_dir=None):
        import sys
        if data_dir is None:
            if getattr(sys, 'frozen', False):
                base = Path(sys.executable).parent
            else:
                base = Path.cwd()
            data_dir = base / "data"
        self.data_dir = Path(data_dir)

    def create_backup(self, dest_folder):
        """
        Copia todos os .parquet de data/ para dest_folder/backup_YYYYMMDD_HHMMSS/.
        Retorna o caminho da pasta criada.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = Path(dest_folder) / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        parquet_files = list(self.data_dir.glob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(f"Nenhum arquivo .parquet encontrado em: {self.data_dir}")

        for src in parquet_files:
            shutil.copy2(src, backup_path / src.name)

        return str(backup_path)
