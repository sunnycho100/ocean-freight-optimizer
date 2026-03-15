# Windows Desktop Build

This project can be packaged as a Windows installer (`.exe`) using Electron Builder.

## Prerequisites

- Windows machine
- Node.js installed
- Python 3 installed on the build machine
- PyInstaller installed on the build machine:
  - `py -3 -m pip install pyinstaller`
- Required Python packages installed in your project environment

## Build Installer

From project root:

```bat
build_desktop_windows.bat
```

Or manually:

```bat
cd freight-ui
npm run backend:build
npm run desktop:build
```

## Output

- Installer: `freight-ui\dist\Ocean Freight Optimizer Setup <version>.exe`
- Unpacked app: `freight-ui\dist\win-unpacked\`
- Frozen backend: `backend_bin\api_server.exe`

## Notes

- Packaged app now prefers `backend/bin/api_server.exe` (no Python runtime required on target machine).
- In frozen mode, background jobs run through the same executable via `--run-job`.
- On packaged runs, backend resources are synced to a writable app data folder at launch.
- Logs remain available in the app through the Task Logs panel.
