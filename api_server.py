"""
Flask API server to serve processed Excel data to the React frontend.
"""
import os
import glob
import socket
import subprocess
import threading
import time
import uuid
import sys
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd

load_dotenv()  # Load .env from project root

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Cache for loaded data to avoid re-reading Excel files on every request
_data_cache = {
    'one': None,
    'hapag': None,
    'one_file': None,
    'hapag_file': None,
    'hapag_route_cache': {}
}

_JOB_SCRIPT_MAP = {
    'url_checker': 'url_checker_refactored.py',
    'quick_download': 'quick_download_refactored.py',
    'one_processor': 'ONE_processor.py',
    'hapag_checker': 'hapag_checker.py',
    'one_pipeline': 'one_pipeline.py',
    'hapag_pipeline': 'hapag_pipeline.py',
}

_job_state = {
    'lock': threading.Lock(),
    'process': None,
    'jobId': None,
    'jobType': None,
    'status': 'idle',
    'startedAt': None,
    'endedAt': None,
    'exitCode': None,
    'command': None,
    'logs': deque(maxlen=10000),
    'nextLogIndex': 0,
}


def _now_iso():
    return datetime.now().isoformat(timespec='seconds')


def _append_job_log(message):
    """Append a log line for the current/last job."""
    if message is None:
        return

    message = str(message).rstrip('\n')
    if not message:
        return

    with _job_state['lock']:
        index = _job_state['nextLogIndex']
        _job_state['logs'].append({
            'index': index,
            'timestamp': _now_iso(),
            'message': message
        })
        _job_state['nextLogIndex'] = index + 1


def _serialize_job_status():
    """Build a JSON-safe snapshot of current job status."""
    with _job_state['lock']:
        proc = _job_state['process']
        is_running = bool(proc and proc.poll() is None)
        return {
            'jobId': _job_state['jobId'],
            'jobType': _job_state['jobType'],
            'status': _job_state['status'],
            'isRunning': is_running,
            'startedAt': _job_state['startedAt'],
            'endedAt': _job_state['endedAt'],
            'exitCode': _job_state['exitCode'],
            'command': _job_state['command'],
            'nextLogIndex': _job_state['nextLogIndex'],
        }


def _get_job_logs(from_index=0, limit=500):
    """Return logs from a given index."""
    with _job_state['lock']:
        logs = [entry for entry in _job_state['logs'] if entry['index'] >= from_index]
        if limit > 0:
            logs = logs[:limit]
        next_index = _job_state['nextLogIndex']
    return logs, next_index


def _stream_job_output(process, job_id):
    """Background reader for subprocess stdout."""
    try:
        if process.stdout is None:
            return
        for line in process.stdout:
            _append_job_log(line)
    except Exception as e:
        _append_job_log(f"[runner] log stream error: {e}")
    finally:
        try:
            if process.stdout:
                process.stdout.close()
        except Exception:
            pass


def _watch_job_process(process, job_id):
    """Background watcher that marks job completion/failure."""
    exit_code = process.wait()
    with _job_state['lock']:
        if _job_state['jobId'] != job_id:
            return
        _job_state['exitCode'] = exit_code
        _job_state['endedAt'] = _now_iso()
        _job_state['status'] = 'completed' if exit_code == 0 else 'failed'
        _job_state['process'] = None

    _append_job_log(f"[runner] job finished with exit code {exit_code}")


def _is_frozen_executable():
    """Return True when running from a frozen executable (PyInstaller)."""
    return bool(getattr(sys, 'frozen', False))


def _resolve_job_command(job_type, args):
    """
    Resolve subprocess command for a job.

    In source mode:
      python <job_script.py> [args]

    In frozen mode:
      <api_server.exe> --run-job <job_type> [args]
    """
    if job_type not in _JOB_SCRIPT_MAP:
        raise ValueError(f"Unsupported jobType: {job_type}")

    if _is_frozen_executable():
        return [sys.executable, '--run-job', job_type] + args

    script_path = os.path.join(os.getcwd(), _JOB_SCRIPT_MAP[job_type])
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    return [sys.executable, script_path] + args


def _run_job_entrypoint(job_type, args):
    """
    Run a job directly in this process.

    Used by frozen mode child processes:
      api_server.exe --run-job <job_type> [args]
    """
    original_argv = list(sys.argv)
    sys.argv = [original_argv[0]] + list(args)

    try:
        if job_type == 'url_checker':
            import url_checker_refactored
            destinations_override = args if args else None
            return 0 if url_checker_refactored.main(destinations_override=destinations_override) else 1

        if job_type == 'quick_download':
            import quick_download_refactored
            result = quick_download_refactored.quick_download()
            return 0 if result and result.get('success') else 1

        if job_type == 'one_processor':
            import ONE_processor

            inland_file = ONE_processor.get_latest_inland_rate_file('downloads')
            ocean_file = os.path.join('source', 'ocean_freight.xlsx')
            ONE_processor.process_inland_rates(
                inland_file=inland_file,
                ocean_file=ocean_file,
                output_dir='downloads',
            )
            return 0

        if job_type == 'hapag_checker':
            import hapag_checker
            return int(hapag_checker.main())

        if job_type == 'one_pipeline':
            import one_pipeline
            destinations_override = args if args else None
            return int(one_pipeline.main(destinations_override=destinations_override))

        if job_type == 'hapag_pipeline':
            import hapag_pipeline
            return int(hapag_pipeline.main())

        print(f"[runner] Unsupported jobType: {job_type}")
        return 1
    except Exception as exc:
        print(f"[runner] Fatal job error ({job_type}): {exc}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        sys.argv = original_argv


def _start_job(job_type, args=None):
    """Start a background script job."""
    args = args or []

    if job_type not in _JOB_SCRIPT_MAP:
        raise ValueError(f"Unsupported jobType: {job_type}")

    with _job_state['lock']:
        running = _job_state['process']
        if running is not None and running.poll() is None:
            raise RuntimeError("Another job is already running")

        command = _resolve_job_command(job_type, args)
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        # Force UTF-8 stdio so Unicode log characters from automation scripts
        # do not crash on Windows cp1252 consoles.
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'

        process = subprocess.Popen(
            command,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            env=env,
        )

        job_id = uuid.uuid4().hex[:12]
        _job_state['process'] = process
        _job_state['jobId'] = job_id
        _job_state['jobType'] = job_type
        _job_state['status'] = 'running'
        _job_state['startedAt'] = _now_iso()
        _job_state['endedAt'] = None
        _job_state['exitCode'] = None
        _job_state['command'] = command
        _job_state['logs'].clear()
        _job_state['nextLogIndex'] = 0

    _append_job_log(f"[runner] started job '{job_type}'")
    _append_job_log(f"[runner] command: {' '.join(command)}")

    threading.Thread(target=_stream_job_output, args=(process, job_id), daemon=True).start()
    threading.Thread(target=_watch_job_process, args=(process, job_id), daemon=True).start()
    return job_id


def _stop_job():
    """Stop currently running job if any."""
    with _job_state['lock']:
        proc = _job_state['process']
        if proc is None or proc.poll() is not None:
            return False

    proc.terminate()
    _append_job_log("[runner] stop requested")
    return True

def get_latest_processed_file():
    """Get the most recently processed Excel file."""
    pattern = 'downloads/ONE_Inland_Rate_Processed_*.xlsx'
    files = glob.glob(pattern)
    # Filter out temp files
    files = [f for f in files if not os.path.basename(f).startswith('~$')]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def get_latest_hapag_file():
    """Get the most recently modified HAPAG surcharges file (raw format)."""
    # Look for raw HAPAG files
    pattern1 = 'downloads/hapag_surcharges.xlsx'
    pattern2 = 'downloads/hapag_surcharges_*.xlsx'
    
    files = glob.glob(pattern1) + glob.glob(pattern2)
    # Filter out temp files
    files = [f for f in files if not os.path.basename(f).startswith('~$')]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def load_data():
    """Load the processed Excel data with caching."""
    file_path = get_latest_processed_file()
    if not file_path:
        return None
    
    # Check if we already have this file cached
    if _data_cache['one_file'] == file_path and _data_cache['one'] is not None:
        return _data_cache['one']
    
    # Load and cache the data
    print(f"Loading ONE data from: {file_path}")
    df = pd.read_excel(file_path)
    _data_cache['one'] = df
    _data_cache['one_file'] = file_path
    return df

def load_hapag_data():
    """Load the raw HAPAG surcharges Excel data with caching."""
    file_path = get_latest_hapag_file()
    if not file_path:
        return None
    
    # Check if we already have this file cached
    if _data_cache['hapag_file'] == file_path and _data_cache['hapag'] is not None:
        return _data_cache['hapag']
    
    # Load and cache the data
    print(f"Loading HAPAG data from: {file_path}")
    # Read raw format with skiprows=4
    df = pd.read_excel(file_path, header=None, skiprows=4)
    # Set column names manually
    df.columns = ['From', 'To', 'Via', 'Description', 'Curr.', '20STD', '40STD', '40HC', 'Transport Remarks']
    _data_cache['hapag_route_cache'] = {}
    _data_cache['hapag'] = df
    _data_cache['hapag_file'] = file_path
    return df

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    """Get list of unique destinations."""
    df = load_data()
    if df is None:
        return jsonify({'error': 'No data file found'}), 404
    destinations = sorted(df['Destination'].unique().tolist())
    return jsonify(destinations)

@app.route('/api/container-types', methods=['GET'])
def get_container_types():
    """Get list of unique container types."""
    df = load_data()
    if df is None:
        return jsonify({'error': 'No data file found'}), 404
    container_types = sorted(df['Container Type & Size'].unique().tolist())
    return jsonify(container_types)

@app.route('/api/routes/<destination>/<container_type>', methods=['GET'])

def get_routes(destination, container_type):
    """Get ranked routes for a specific destination and container type."""
    df = load_data()
    if df is None:
        return jsonify({'error': 'No data file found'}), 404
    
    # Filter by destination and container type
    filtered = df[
        (df['Destination'] == destination) & 
        (df['Container Type & Size'] == container_type)
    ].copy()
    
    if filtered.empty:
        return jsonify({'error': 'No routes found for criteria'}), 404
    
    # Sort by Total Rate (primary) to ensure correct order, then by Cost Rank (secondary)
    filtered = filtered.sort_values(['Total Rate', 'Cost Rank'], ascending=[True, True])
    
    # Get currency (should be the same for all routes in a lane)
    currency = filtered['Currency'].iloc[0]
    
    # Get the best (lowest cost) route for each rank
    # This ensures we show exactly one route per rank, with no duplicates
    best_per_rank = filtered.sort_values('Total Rate').drop_duplicates(subset=['Cost Rank'], keep='first')
    best_per_rank = best_per_rank.sort_values('Cost Rank')
    
    # Build routes list
    routes = []
    for _, row in best_per_rank.iterrows():
        routes.append({
            'rank': int(row['Cost Rank']),
            'pod': row['POD'],
            'mode': row['Transport Mode'],
            'remarks': row['Remarks'] if 'Remarks' in row and pd.notna(row['Remarks']) else '',
            'totalRate': float(row['Total Rate']),
            'oceanRate': float(row['Ocean Rate']),
            'inlandRate': float(row['Rate']),
        })
    
    return jsonify({
        'destination': destination,
        'containerType': container_type,
        'currency': currency,
        'routes': routes,
        'totalRoutes': len(routes)
    })

@app.route('/api/hapag/destinations', methods=['GET'])
def get_hapag_destinations():
    """Get list of unique destinations from HAPAG data."""
    df = load_hapag_data()
    if df is None:
        return jsonify({'error': 'No HAPAG data file found'}), 404
    destinations = sorted(df['To'].unique().tolist())
    return jsonify(destinations)

@app.route('/api/hapag/route/<path:destination>', methods=['GET'])
def get_hapag_route(destination):
    """Get route and charges for a specific HAPAG destination (serving raw structure with sub-options)."""
    df = load_hapag_data()
    if df is None:
        return jsonify({'error': 'No HAPAG data file found'}), 404

    cache_key = (str(_data_cache.get('hapag_file')), destination)
    cached = _data_cache['hapag_route_cache'].get(cache_key)
    if cached is not None:
        return jsonify(cached)
    
    # Filter by destination
    filtered = df[df['To'] == destination].copy()
    
    if filtered.empty:
        return jsonify({'error': 'No routes found for destination'}), 404
    
    # Get route info (should be same for all rows)
    first_row = filtered.iloc[0]
    route_from = first_row['From']
    route_to = first_row['To']
    route_via = first_row['Via'] if pd.notna(first_row['Via']) and first_row['Via'] != '' else ''
    
    # Determine available containers (convert to Python bool for JSON serialization)
    available_containers = {
        '20STD': bool(not filtered['20STD'].isna().all() and (filtered['20STD'] != '').any() and (filtered['20STD'] != '-').any()),
        '40STD': bool(not filtered['40STD'].isna().all() and (filtered['40STD'] != '').any() and (filtered['40STD'] != '-').any()),
        '40HC': bool(not filtered['40HC'].isna().all() and (filtered['40HC'] != '').any() and (filtered['40HC'] != '-').any()),
    }
    
    # Process charges
    ocean_freight = None
    destination_landfreight = None
    other_charges = []
    
    # Track rows for sub-options
    i = 0
    while i < len(filtered):
        row = filtered.iloc[i]
        desc = str(row['Description'])
        curr = str(row['Curr.']) if pd.notna(row['Curr.']) and row['Curr.'] != '' else ''
        
        # Check if this is Ocean Freight
        if 'ocean freight' in desc.lower():
            ocean_freight = {
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) and row['20STD'] != '' else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) and row['40STD'] != '' else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) and row['40HC'] != '' else '',
            }
            i += 1
            continue
        
        # Check if this is Destination Landfreight (has sub-options when Curr. is empty)
        if 'destination landfreight' in desc.lower() or 'landfreight' in desc.lower():
            landfreight_item = {
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) and row['20STD'] != '' else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) and row['40STD'] != '' else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) and row['40HC'] != '' else '',
            }
            
            # Check if empty curr (signals sub-options exist below)
            if curr == '' or pd.isna(row['Curr.']):
                sub_options = []
                i += 1
                
                # Look for sub-option rows (usually start with "Combined", "Between", etc.)
                # Continue while we find rows with currency values (sub-options)
                while i < len(filtered):
                    next_row = filtered.iloc[i]
                    next_desc = str(next_row['Description'])
                    next_curr = str(next_row['Curr.']) if pd.notna(next_row['Curr.']) and next_row['Curr.'] != '' else ''
                    
                    # If we hit another main category (empty curr or different pattern), stop
                    if next_curr == '' or pd.isna(next_row['Curr.']):
                        break
                    
                    # Check if it looks like a sub-option (starts with Combined, Between, etc.)
                    first_word = next_desc.split()[0].lower() if next_desc.split() else ''
                    if first_word in ['combined', 'between', 'from', '<', '>'] or ';' in next_desc:
                        sub_options.append({
                            'description': next_desc,
                            'value20': str(next_row['20STD']) if pd.notna(next_row['20STD']) and next_row['20STD'] != '' else '-',
                            'value40': str(next_row['40STD']) if pd.notna(next_row['40STD']) and next_row['40STD'] != '' else '-',
                            'value40HC': str(next_row['40HC']) if pd.notna(next_row['40HC']) and next_row['40HC'] != '' else '-',
                        })
                        i += 1
                    else:
                        break
                
                if sub_options:
                    landfreight_item['subOptions'] = sub_options
                    # Set currency from first sub-option
                    if i > 0 and i <= len(filtered):
                        prev_row = filtered.iloc[i-1]
                        if pd.notna(prev_row['Curr.']) and prev_row['Curr.'] != '':
                            landfreight_item['curr'] = str(prev_row['Curr.'])
            else:
                i += 1
            
            destination_landfreight = landfreight_item
            continue
        
        # Other charges (skip rows with empty currency as they're usually category headers)
        if curr != '' and not pd.isna(row['Curr.']):
            other_charges.append({
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) and row['20STD'] != '' else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) and row['40STD'] != '' else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) and row['40HC'] != '' else '',
            })
        
        i += 1
    
    response = {
        'destination': destination,
        'route': {
            'from': route_from,
            'to': route_to,
            'via': route_via,
            'oceanFreight': ocean_freight,
            'destinationLandfreight': destination_landfreight,
            'otherCharges': other_charges,
            'availableContainers': available_containers,
        }
    }
    _data_cache['hapag_route_cache'][cache_key] = response
    return jsonify(response)


# --- Automation Job Runner ---
@app.route('/api/jobs/status', methods=['GET'])
def job_status():
    """Get the current background job status."""
    return jsonify(_serialize_job_status())


@app.route('/api/jobs/logs', methods=['GET'])
def job_logs():
    """Get background job logs incrementally."""
    try:
        from_index = int(request.args.get('from', 0))
        limit = int(request.args.get('limit', 500))
    except ValueError:
        return jsonify({'error': 'Invalid from/limit value'}), 400

    logs, next_index = _get_job_logs(from_index=from_index, limit=limit)
    return jsonify({'logs': logs, 'nextLogIndex': next_index})


@app.route('/api/jobs/run', methods=['POST'])
def run_job():
    """Run one of the supported automation scripts."""
    data = request.get_json(silent=True) or {}
    job_type = data.get('jobType')
    destinations = data.get('destinations', [])

    if not job_type:
        return jsonify({'error': 'Missing jobType'}), 400

    args = []
    if job_type in ('url_checker', 'one_pipeline'):
        if destinations and not isinstance(destinations, list):
            return jsonify({'error': 'destinations must be a list of strings'}), 400
        args = [str(dest).strip() for dest in destinations if str(dest).strip()]

    try:
        job_id = _start_job(job_type, args=args)
        return jsonify({'jobId': job_id, 'status': _serialize_job_status()}), 202
    except RuntimeError as e:
        return jsonify({'error': str(e), 'status': _serialize_job_status()}), 409
    except (ValueError, FileNotFoundError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/stop', methods=['POST'])
def stop_job():
    """Stop currently running automation job."""
    if _stop_job():
        return jsonify({'ok': True, 'status': _serialize_job_status()})
    return jsonify({'ok': False, 'status': _serialize_job_status(), 'message': 'No running job'}), 409

# --- Chatbot ---
_chatbot = {'context_builder': None, 'llm_client': None}

def _init_chatbot():
    """Lazy-initialize chatbot components."""
    if _chatbot['context_builder'] is None:
        from chatbot.data_loader import FreightDataLoader
        from chatbot.context_builder import ContextBuilder
        from chatbot.llm_client import LLMClient
        loader = FreightDataLoader()
        _chatbot['context_builder'] = ContextBuilder(loader)
        _chatbot['llm_client'] = LLMClient()

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for the freight assistant."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing message field'}), 400

    user_message = data['message']
    history = data.get('history', [])

    try:
        _init_chatbot()
        messages = _chatbot['context_builder'].build_context(user_message, history)
        reply = _chatbot['llm_client'].chat(messages)
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    df = load_data()
    if df is None:
        return jsonify({'status': 'error', 'message': 'No data file found'}), 500
    return jsonify({
        'status': 'ok',
        'totalRows': len(df),
        'destinations': df['Destination'].nunique(),
        'file': get_latest_processed_file()
    })

def find_available_port(start_port=4000, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts}")


def resolve_server_port():
    """Resolve server port from env or dynamic fallback."""
    forced = os.environ.get('FREIGHT_API_PORT') or os.environ.get('API_PORT')
    if forced:
        try:
            return int(forced)
        except ValueError as e:
            raise RuntimeError(f"Invalid port value: {forced}") from e
    return find_available_port(4000)


def resolve_debug_mode():
    """Resolve Flask debug mode from env."""
    raw = os.environ.get('API_DEBUG', '1').strip().lower()
    return raw in ('1', 'true', 'yes', 'on')


if __name__ == '__main__':
    # Frozen child-process mode for automation jobs:
    #   api_server.exe --run-job <job_type> [args...]
    if len(sys.argv) >= 3 and sys.argv[1] == '--run-job':
        sys.exit(_run_job_entrypoint(sys.argv[2], sys.argv[3:]))

    port = resolve_server_port()
    debug_mode = resolve_debug_mode()
    print(f"Starting API server on http://localhost:{port}")
    print(f"Data file: {get_latest_processed_file()}")
    print(f"Debug mode: {debug_mode}")
    # Write port to file so start.sh can read it
    # Only write on the main process, not the debug reloader child
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        with open('.api_port', 'w') as f:
            f.write(str(port))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
