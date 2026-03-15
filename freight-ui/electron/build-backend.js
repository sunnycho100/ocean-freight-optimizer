const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const projectRoot = path.resolve(__dirname, '..', '..');
const buildScript = path.join(projectRoot, 'build_backend_executable.py');

function getCandidates() {
  const candidates = [];
  const venvWinPython = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');
  const venvUnixPython = path.join(projectRoot, '.venv', 'bin', 'python');

  if (fs.existsSync(venvWinPython)) {
    candidates.push({ command: venvWinPython, args: [buildScript] });
  }
  if (fs.existsSync(venvUnixPython)) {
    candidates.push({ command: venvUnixPython, args: [buildScript] });
  }

  if (process.platform === 'win32') {
    candidates.push({ command: 'py', args: ['-3', buildScript] });
    candidates.push({ command: 'python', args: [buildScript] });
  } else {
    candidates.push({ command: 'python3', args: [buildScript] });
    candidates.push({ command: 'python', args: [buildScript] });
  }

  return candidates;
}

function formatCommand(candidate) {
  return `${candidate.command} ${candidate.args.join(' ')}`;
}

function run() {
  if (!fs.existsSync(buildScript)) {
    console.error(`[backend-build] Missing script: ${buildScript}`);
    process.exit(1);
  }

  const candidates = getCandidates();
  const errors = [];

  for (const candidate of candidates) {
    const display = formatCommand(candidate);
    console.log(`[backend-build] Running: ${display}`);

    const result = spawnSync(candidate.command, candidate.args, {
      cwd: projectRoot,
      stdio: 'inherit',
      windowsHide: true,
    });

    if (result.status === 0) {
      console.log('[backend-build] Backend executable build succeeded.');
      process.exit(0);
    }

    if (result.error) {
      errors.push(`${display} -> ${String(result.error)}`);
      continue;
    }

    errors.push(`${display} -> exited with code ${result.status}`);
  }

  console.error('[backend-build] All backend build command candidates failed:');
  for (const err of errors) {
    console.error(`  - ${err}`);
  }
  process.exit(1);
}

run();
