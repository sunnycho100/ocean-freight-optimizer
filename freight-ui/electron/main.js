const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const isDev = !app.isPackaged;
const uiRoot = path.resolve(__dirname, '..');
const devProjectRoot = path.resolve(__dirname, '..', '..');
const packagedBackendRoot = path.join(process.resourcesPath, 'backend');

let mainWindow = null;
let backendProcess = null;

function getBackendRoot() {
  const devApiPath = path.join(devProjectRoot, 'api_server.py');
  if (fs.existsSync(devApiPath)) return devProjectRoot;
  return preparePackagedBackend();
}

function preparePackagedBackend() {
  const runtimeBackendRoot = path.join(app.getPath('userData'), 'backend');
  const versionMarkerPath = path.join(runtimeBackendRoot, '.backend_version');
  const appVersion = app.getVersion();
  const packagedExePath = path.join(packagedBackendRoot, 'bin', 'api_server.exe');

  let packagedSignature = `${appVersion}|missing`;
  try {
    if (fs.existsSync(packagedExePath)) {
      const stat = fs.statSync(packagedExePath);
      packagedSignature = `${appVersion}|${stat.size}|${stat.mtimeMs}`;
    }
  } catch (e) {
    packagedSignature = `${appVersion}|stat-error`;
  }

  let shouldSync = !fs.existsSync(runtimeBackendRoot);
  if (!shouldSync) {
    try {
      const currentMarker = fs.existsSync(versionMarkerPath)
        ? String(fs.readFileSync(versionMarkerPath, 'utf-8')).trim()
        : '';
      shouldSync = currentMarker !== packagedSignature;
    } catch (e) {
      shouldSync = true;
    }
  }

  if (shouldSync) {
    fs.rmSync(runtimeBackendRoot, { recursive: true, force: true });
    fs.mkdirSync(runtimeBackendRoot, { recursive: true });
    fs.cpSync(packagedBackendRoot, runtimeBackendRoot, { recursive: true, force: true });
    fs.writeFileSync(versionMarkerPath, packagedSignature, 'utf-8');
  }

  return runtimeBackendRoot;
}

function getBackendLaunchCandidates(backendRoot) {
  const apiExe = path.join(backendRoot, 'bin', 'api_server.exe');
  const apiScript = path.join(backendRoot, 'api_server.py');
  const winVenvPython = path.join(backendRoot, '.venv', 'Scripts', 'python.exe');
  const unixVenvPython = path.join(backendRoot, '.venv', 'bin', 'python');
  const candidates = [];

  // Preferred for packaged no-Python distribution.
  if (fs.existsSync(apiExe)) {
    candidates.push({ command: apiExe, args: [] });
  }

  // Dev/source fallback via Python.
  if (fs.existsSync(apiScript)) {
    if (fs.existsSync(winVenvPython)) {
      candidates.push({ command: winVenvPython, args: [apiScript] });
    }
    if (fs.existsSync(unixVenvPython)) {
      candidates.push({ command: unixVenvPython, args: [apiScript] });
    }

    if (process.platform === 'win32') {
      candidates.push({ command: 'py', args: ['-3', apiScript] });
      candidates.push({ command: 'python', args: [apiScript] });
      candidates.push({ command: 'python3', args: [apiScript] });
    } else {
      candidates.push({ command: 'python3', args: [apiScript] });
      candidates.push({ command: 'python', args: [apiScript] });
    }
  }

  return candidates;
}

function formatCommand(candidate) {
  return `${candidate.command} ${candidate.args.join(' ')}`;
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForApiPort(portFile, timeoutMs = 60000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (fs.existsSync(portFile)) {
      const text = String(fs.readFileSync(portFile, 'utf-8')).trim();
      const port = Number(text);
      if (Number.isInteger(port) && port > 0) {
        return port;
      }
    }
    await delay(250);
  }
  throw new Error('Timed out waiting for API server port file');
}

function waitForApiPortFromProcess(process, portFile, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    let settled = false;

    const done = (fn, value) => {
      if (settled) return;
      settled = true;
      process.removeListener('error', onError);
      process.removeListener('exit', onExitBeforeReady);
      fn(value);
    };

    const onError = (err) => {
      done(reject, err);
    };

    const onExitBeforeReady = (code) => {
      done(reject, new Error(`Backend exited before startup (code ${code})`));
    };

    process.once('error', onError);
    process.once('exit', onExitBeforeReady);

    waitForApiPort(portFile, timeoutMs)
      .then((port) => {
        done(resolve, port);
      })
      .catch((err) => {
        done(reject, err);
      });
  });
}

async function startBackend() {
  const backendRoot = getBackendRoot();
  const portFile = path.join(backendRoot, '.api_port');

  try {
    if (fs.existsSync(portFile)) fs.unlinkSync(portFile);
  } catch (e) {
    // ignore stale file cleanup errors
  }

  const candidates = getBackendLaunchCandidates(backendRoot);
  if (candidates.length === 0) {
    throw new Error(
      `No backend runtime candidates found in: ${backendRoot}\n` +
      'Expected either backend/bin/api_server.exe or backend/api_server.py.'
    );
  }

  let lastError = null;
  const triedCommands = [];

  for (const candidate of candidates) {
    const commandText = formatCommand(candidate);
    triedCommands.push(commandText);
    console.log(`[desktop] Starting backend: ${commandText}`);

    let processHandle = null;
    try {
      try {
        if (fs.existsSync(portFile)) fs.unlinkSync(portFile);
      } catch (e) {
        // ignore stale file cleanup errors
      }

      processHandle = spawn(candidate.command, candidate.args, {
        cwd: backendRoot,
        env: {
          ...process.env,
          API_DEBUG: '0',
          PYTHONUNBUFFERED: '1',
          PYTHONIOENCODING: 'utf-8',
          PYTHONUTF8: '1',
        },
        windowsHide: true,
      });

      processHandle.stdout?.on('data', (data) => {
        process.stdout.write(`[backend] ${data}`);
      });

      processHandle.stderr?.on('data', (data) => {
        process.stderr.write(`[backend] ${data}`);
      });

      const apiPort = await waitForApiPortFromProcess(processHandle, portFile, 60000);
      backendProcess = processHandle;
      return apiPort;
    } catch (err) {
      lastError = err;
      console.error(`[desktop] Backend launch failed using "${commandText}": ${String(err)}`);
      if (processHandle && !processHandle.killed) {
        try {
          processHandle.kill();
          await delay(150);
        } catch (killErr) {
          console.error(`[desktop] Failed to terminate failed backend process: ${String(killErr)}`);
        }
      }
    }
  }

  const details = lastError ? `Last error: ${String(lastError)}` : 'No detailed error available.';
  throw new Error(
    [
      'Could not start backend service.',
      'For no-Python packaging, ensure backend/bin/api_server.exe exists in app resources.',
      'For source/dev mode, install Python 3 and required dependencies or place a project .venv in backend.',
      `Tried commands: ${triedCommands.join(' | ')}`,
      details,
    ].join('\n')
  );
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    console.log('[desktop] Stopping backend process');
    backendProcess.kill();
  }
  backendProcess = null;
}

async function createWindow(apiPort) {
  mainWindow = new BrowserWindow({
    width: 1520,
    height: 920,
    minWidth: 1200,
    minHeight: 760,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  const query = `apiPort=${apiPort}&desktop=1`;
  if (isDev) {
    await mainWindow.loadURL(`http://localhost:3000/?${query}`);
  } else {
    await mainWindow.loadFile(path.join(uiRoot, 'build', 'index.html'), {
      query: { apiPort: String(apiPort), desktop: '1' },
    });
  }
}

app.whenReady().then(async () => {
  try {
    const apiPort = await startBackend();
    await createWindow(apiPort);
  } catch (e) {
    dialog.showErrorBox('Desktop Startup Failed', String(e));
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

process.on('exit', () => {
  stopBackend();
});
