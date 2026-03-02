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
        .invoke_handler(tauri::generate_handler![
            get_data_dir,
            backup_database,
            write_bytes,
            open_file,
        ])
        .run(tauri::generate_context!())
        .expect("Erro ao iniciar o aplicativo Controle B2");
}
