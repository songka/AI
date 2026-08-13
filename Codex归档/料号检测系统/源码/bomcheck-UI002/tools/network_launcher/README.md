# Network launcher

`bomcheck_web.exe` and `bomcheck_app.exe` are PyInstaller one-file packages. Starting them directly from SMB can be slow because the bootloader reads and extracts the bundled archive from the network path.

Build these launchers and put them beside the existing exe files on the SMB share:

- `bomcheck_web_launcher.exe` launches `bomcheck_web.exe`
- `bomcheck_app_launcher.exe` launches `bomcheck_app.exe`

On startup, the launcher copies the matching main exe to:

`%LOCALAPPDATA%\BOMCheck\exe-cache\...`

It only recopies when the source exe size or last-write time changes, then starts the cached local copy. Shared `config.json` and data paths are still read by the main application, so business data remains centralized.

Build:

```powershell
powershell -ExecutionPolicy Bypass -File tools\network_launcher\build_network_launchers.ps1
```

Output:

- `dist\network_launcher\*_launcher.exe`
- also copied to `dist\single_exe\*_launcher.exe` when that folder exists

Deployment tip: ask users to open `bomcheck_web_launcher.exe` instead of `bomcheck_web.exe` from the SMB folder.

