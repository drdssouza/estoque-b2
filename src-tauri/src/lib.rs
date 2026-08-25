use std::path::PathBuf;
use tauri::Manager;

/// Retorna o diretório de dados do app (onde o SQLite fica armazenado).
#[tauri::command]
fn get_data_dir(app: tauri::AppHandle) -> Result<String, String> {
    app.path()
        .app_data_dir()
        .map(|p| p.to_string_lossy().to_string())
        .map_err(|e| e.to_string())
}

/// Copia o arquivo .db para o destino especificado (com nome já calculado pelo frontend).
#[tauri::command]
fn backup_database(app: tauri::AppHandle, dest_path: String) -> Result<(), String> {
    let data_dir = app
        .path()
        .app_data_dir()
        .map_err(|e| e.to_string())?;

    let db_src = data_dir.join("controle_b2.db");

    if !db_src.exists() {
        return Err("Banco de dados não encontrado. Nenhum dado para fazer backup.".to_string());
    }

    let dest = PathBuf::from(&dest_path);
    if let Some(parent) = dest.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }

    std::fs::copy(&db_src, &dest_path).map_err(|e| e.to_string())?;
    Ok(())
}

/// Restaura o banco a partir de um arquivo .db escolhido pelo usuário.
///
/// A conexão com o banco precisa estar fechada antes de chamar (o frontend faz
/// isso), senão o SQLite estaria escrevendo em um arquivo que foi trocado.
/// Antes de sobrescrever, guarda uma cópia do banco atual — assim uma
/// restauração feita com o arquivo errado ainda é reversível.
/// Devolve o caminho dessa cópia de segurança (vazio se não havia banco).
#[tauri::command]
fn restore_database(app: tauri::AppHandle, src_path: String, stamp: String) -> Result<String, String> {
    use std::io::Read;

    let src = PathBuf::from(&src_path);
    if !src.exists() {
        return Err("Arquivo de backup não encontrado.".to_string());
    }

    // Todo banco SQLite começa com esta assinatura de 16 bytes.
    let mut header = [0u8; 16];
    std::fs::File::open(&src)
        .map_err(|e| e.to_string())?
        .read_exact(&mut header)
        .map_err(|_| "Arquivo inválido: não parece um banco de dados.".to_string())?;
    if &header != b"SQLite format 3\0" {
        return Err("Arquivo inválido: não é um banco de dados do Controle B2.".to_string());
    }

    let data_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&data_dir).map_err(|e| e.to_string())?;
    let db_dest = data_dir.join("controle_b2.db");

    let mut safety_copy = String::new();
    if db_dest.exists() {
        let backup_path = data_dir.join(format!("antes_da_restauracao_{stamp}.db"));
        std::fs::copy(&db_dest, &backup_path).map_err(|e| e.to_string())?;
        safety_copy = backup_path.to_string_lossy().to_string();
    }

    std::fs::copy(&src, &db_dest).map_err(|e| e.to_string())?;

    // -wal e -shm pertencem ao banco antigo; deixá-los para trás confunde o SQLite.
    for suffix in ["-wal", "-shm"] {
        let leftover = data_dir.join(format!("controle_b2.db{suffix}"));
        if leftover.exists() {
            let _ = std::fs::remove_file(leftover);
        }
    }

    Ok(safety_copy)
}

/// Grava bytes em disco (usado para salvar PDFs gerados no frontend).
#[tauri::command]
fn write_bytes(path: String, data: Vec<u8>) -> Result<(), String> {
    let dest = PathBuf::from(&path);
    if let Some(parent) = dest.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    std::fs::write(&path, data).map_err(|e| e.to_string())
}

/// Abre um arquivo com o programa padrão do sistema operacional.
#[tauri::command]
fn open_file(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("cmd")
            .args(["/C", "start", "", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_sql::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![
            get_data_dir,
            backup_database,
            restore_database,
            write_bytes,
            open_file,
        ])
        .run(tauri::generate_context!())
        .expect("Erro ao iniciar o aplicativo Controle B2");
}
