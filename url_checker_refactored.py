"""
Main entry point for URL Checker.

Usage:
    python url_checker_refactored.py "PARIS, FRANCE" "ROME, ITALY"
    python url_checker_refactored.py --workers 3
"""

import os
import sys
import time
import traceback
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIG: IGNORE SSL ERRORS ---
os.environ["WDM_SSL_VERIFY"] = "0"
os.environ.pop("WDM_LOCAL", None)

try:
    from urllib3.exceptions import InsecureRequestWarning
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
except Exception:
    pass

from url_checker_package.config import CONFIG_FILE_NAME, DESTINATIONS_FILE_NAME
from url_checker_package.browser import setup_browser
from url_checker_package.config_manager import (
    get_config_file_path,
    load_configs,
    save_configs,
    load_destinations_from_file,
)
from url_checker_package.processor import process_destination


MAX_PARALLEL_WORKERS = 4
DEFAULT_PARALLEL_WORKERS = 3
INTER_DESTINATION_DELAY_SECONDS = 0.2


def _parse_cli_args(raw_args):
    """
    Parse CLI args.

    Supports:
      - positional destination args
      - --workers N or --workers=N
    """
    destinations = []
    workers = None

    idx = 0
    while idx < len(raw_args):
        arg = raw_args[idx]

        if arg in ("--workers", "-w"):
            if idx + 1 >= len(raw_args):
                raise ValueError("--workers requires a numeric value")
            workers = int(raw_args[idx + 1])
            idx += 2
            continue

        if arg.startswith("--workers="):
            workers = int(arg.split("=", 1)[1])
            idx += 1
            continue

        destinations.append(arg)
        idx += 1

    return destinations, workers


def _resolve_worker_count(destination_count, requested_workers=None):
    """Resolve and clamp worker count."""
    if destination_count <= 1:
        return 1

    if requested_workers is not None:
        base_workers = requested_workers
    else:
        env_workers = os.environ.get("URL_CHECKER_WORKERS", str(DEFAULT_PARALLEL_WORKERS))
        try:
            base_workers = int(env_workers)
        except ValueError:
            base_workers = DEFAULT_PARALLEL_WORKERS

    base_workers = max(1, min(base_workers, MAX_PARALLEL_WORKERS))
    return min(base_workers, destination_count)


def _split_round_robin(items, bucket_count):
    """Split a list into N round-robin buckets."""
    buckets = [[] for _ in range(bucket_count)]
    for index, item in enumerate(items):
        buckets[index % bucket_count].append(item)
    return [bucket for bucket in buckets if bucket]


def _process_destinations_chunk(worker_id, destinations):
    """
    Process a chunk of destinations using one browser per worker.

    Returns:
      {
        "new_configs": dict,
        "warnings": list[str],
        "failed": list[str],
      }
    """
    print(f"\n[WORKER {worker_id}] Starting browser for {len(destinations)} destination(s)")
    try:
        driver = setup_browser()
    except Exception as exc:
        print(f"[WORKER {worker_id}] [ERROR] Browser setup failed: {exc}")
        traceback.print_exc()
        return {
            "new_configs": {},
            "warnings": [],
            "failed": list(destinations),
        }

    new_configs = {}
    warnings = []
    failed = []

    try:
        for index, destination in enumerate(destinations, start=1):
            print(f"\n[WORKER {worker_id}] [{index}/{len(destinations)}] {destination}")
            config = process_destination(driver, destination)

            if config:
                has_results = bool(config.get("has_results", True))
                config_to_save = dict(config)
                config_to_save.pop("has_results", None)

                new_configs[destination] = config_to_save
                print(f"[WORKER {worker_id}] [SUCCESS] {destination}")
                print(f"[WORKER {worker_id}]    Location Code: {config_to_save.get('locationCode', 'NOT FOUND')}")
                print(f"[WORKER {worker_id}]    PODs: {config_to_save.get('pods', 'NOT FOUND')}")

                if not has_results:
                    warning_msg = f"{destination}: ZERO RESULTS (check error_checks folder)"
                    warnings.append(warning_msg)
                    print(f"[WORKER {worker_id}] [WARNING] {warning_msg}")
            else:
                failed.append(destination)
                print(f"[WORKER {worker_id}] [FAILED] Could not extract configuration for: {destination}")
                print(f"[WORKER {worker_id}] ERROR: Location code NOT FOUND")

            if INTER_DESTINATION_DELAY_SECONDS > 0:
                time.sleep(INTER_DESTINATION_DELAY_SECONDS)

    except Exception as exc:
        print(f"[WORKER {worker_id}] [ERROR] Worker crashed: {exc}")
        traceback.print_exc()
        failed.extend([d for d in destinations if d not in new_configs and d not in failed])
    finally:
        print(f"\n[WORKER {worker_id}] Closing browser...")
        try:
            driver.quit()
        except Exception as exc:
            print(f"[WORKER {worker_id}] [WARNING] Browser close failed: {exc}")

    return {
        "new_configs": new_configs,
        "warnings": warnings,
        "failed": failed,
    }


def generate_error_summary():
    """Generate a summary of all errors from error_checks folder."""
    error_dir = os.path.join(os.getcwd(), "error_checks")

    if not os.path.exists(error_dir):
        return

    error_files = [f for f in os.listdir(error_dir) if f.endswith(".txt")]
    if not error_files:
        print("\n[INFO] No error files found in error_checks folder")
        return

    print("\n" + "=" * 60)
    print("ERROR SUMMARY")
    print("=" * 60)

    errors_by_type = {
        "SELECTION_FAILED": [],
        "NO_RESULTS": [],
        "MISMATCH": [],
        "OTHER": [],
    }

    for error_file in error_files:
        if "SELECTION_FAILED" in error_file:
            errors_by_type["SELECTION_FAILED"].append(error_file)
        elif "NO_RESULTS" in error_file or "ZERO_RESULTS" in error_file:
            errors_by_type["NO_RESULTS"].append(error_file)
        elif "MISMATCH" in error_file:
            errors_by_type["MISMATCH"].append(error_file)
        else:
            errors_by_type["OTHER"].append(error_file)

    total_errors = sum(len(v) for v in errors_by_type.values())
    print(f"\nTotal error files: {total_errors}\n")

    if errors_by_type["SELECTION_FAILED"]:
        print(f"[ERROR] SELECTION FAILED ({len(errors_by_type['SELECTION_FAILED'])}):")
        print("   - Destination could not be selected from dropdown")
        for file_name in errors_by_type["SELECTION_FAILED"][:5]:
            print(f"     - {file_name}")
        if len(errors_by_type["SELECTION_FAILED"]) > 5:
            print(f"     ... and {len(errors_by_type['SELECTION_FAILED']) - 5} more")

    if errors_by_type["NO_RESULTS"]:
        print(f"\n[WARN] ZERO RESULTS ({len(errors_by_type['NO_RESULTS'])}):")
        print("   - Search completed but returned 0 results")
        for file_name in errors_by_type["NO_RESULTS"][:5]:
            print(f"     - {file_name}")
        if len(errors_by_type["NO_RESULTS"]) > 5:
            print(f"     ... and {len(errors_by_type['NO_RESULTS']) - 5} more")

    if errors_by_type["MISMATCH"]:
        print(f"\n[WARN] CITY MISMATCH ({len(errors_by_type['MISMATCH'])}):")
        print("   - Selected city does not match input (typo/alternate name)")
        for file_name in errors_by_type["MISMATCH"][:5]:
            print(f"     - {file_name}")
        if len(errors_by_type["MISMATCH"]) > 5:
            print(f"     ... and {len(errors_by_type['MISMATCH']) - 5} more")

    if errors_by_type["OTHER"]:
        print(f"\n[INFO] OTHER ERRORS ({len(errors_by_type['OTHER'])}):")
        for file_name in errors_by_type["OTHER"][:5]:
            print(f"     - {file_name}")
        if len(errors_by_type["OTHER"]) > 5:
            print(f"     ... and {len(errors_by_type['OTHER']) - 5} more")

    print(f"\n[INFO] All error files are in: {error_dir}")
    print("=" * 60)


def main(destinations_override=None, worker_count=None):
    """Main function - orchestrates the entire workflow."""
    print("=" * 60)
    print("ONE Line URL Checker - Location Code Extractor")
    print("=" * 60)

    destinations = []
    cli_workers = None

    if destinations_override is not None:
        destinations = [d for d in destinations_override if str(d).strip()]
        print(f"\n[INFO] Using {len(destinations)} destination(s) from API payload")
    else:
        cli_destinations, cli_workers = _parse_cli_args(sys.argv[1:])
        if cli_destinations:
            destinations = cli_destinations
            print(f"\n[INFO] Using {len(destinations)} destination(s) from command line")
        else:
            destinations_file = get_config_file_path(DESTINATIONS_FILE_NAME)
            destinations = load_destinations_from_file(destinations_file)

    if not destinations:
        print("\n[ERROR] No destinations provided!")
        print("Usage:")
        print('  python url_checker_refactored.py "PARIS, FRANCE" "ROME, ITALY"')
        print("  python url_checker_refactored.py --workers 3")
        print("  or create destinations.txt with one city per line")
        return False

    print(f"\n[INFO] Processing {len(destinations)} destination(s)")

    # Load existing configs
    config_file = get_config_file_path(CONFIG_FILE_NAME)
    destinations_file = get_config_file_path(DESTINATIONS_FILE_NAME)
    configs = load_configs(config_file, destinations_file)
    print(f"[INFO] Loaded {len(configs)} existing configurations")

    resolved_workers = _resolve_worker_count(
        len(destinations),
        requested_workers=worker_count if worker_count is not None else cli_workers,
    )
    print(f"[INFO] Parallel workers: {resolved_workers}")

    new_configs = {}
    warnings = []
    failed_destinations = []

    if resolved_workers == 1:
        worker_result = _process_destinations_chunk(1, destinations)
        new_configs.update(worker_result["new_configs"])
        warnings.extend(worker_result["warnings"])
        failed_destinations.extend(worker_result["failed"])
    else:
        chunks = _split_round_robin(destinations, resolved_workers)
        with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            future_to_worker = {
                executor.submit(_process_destinations_chunk, idx + 1, chunk): idx + 1
                for idx, chunk in enumerate(chunks)
            }
            for future in as_completed(future_to_worker):
                worker_id = future_to_worker[future]
                try:
                    worker_result = future.result()
                    new_configs.update(worker_result["new_configs"])
                    warnings.extend(worker_result["warnings"])
                    failed_destinations.extend(worker_result["failed"])
                except Exception as exc:
                    print(f"[ERROR] Worker {worker_id} failed unexpectedly: {exc}")
                    traceback.print_exc()

    # Persist merged configs once.
    if new_configs:
        configs.update(new_configs)
        if save_configs(configs, config_file):
            print(f"\n[SUMMARY] Successfully added/updated {len(new_configs)} destination(s)")
            for destination, config in new_configs.items():
                print(f"  - {destination}: {config.get('locationCode', 'NOT FOUND')}")
    else:
        print("\n[SUMMARY] No new configurations to save")

    if warnings:
        print(f"\n[WARNINGS] {len(warnings)} destination(s) with issues:")
        for warning in warnings:
            print(f"  - {warning}")

    if failed_destinations:
        print(f"\n[FAILED] {len(failed_destinations)} destination(s) failed:")
        for destination in failed_destinations:
            print(f"  - {destination}")

    generate_error_summary()

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        is_ok = main()
        sys.exit(0 if is_ok else 1)
    except Exception as exc:
        print(f"[FATAL] URL checker crashed: {exc}")
        traceback.print_exc()
        sys.exit(1)
