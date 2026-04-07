# Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use std::process::Command;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Get the main window
            let window = app.get_window("main").unwrap();
            
            // Set window to be draggable
            window.set_decorations(false).unwrap();
            
            // Set always on top
            window.set_always_on_top(true).unwrap();
            
            // Start Python backend
            std::thread::spawn(|| {
                let _ = Command::new("python")
                    .args(&["main.py"])
                    .current_dir("..")
                    .spawn();
            });
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}