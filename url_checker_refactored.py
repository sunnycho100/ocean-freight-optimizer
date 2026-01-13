"""
Main entry point for URL Checker

Usage:
    python url_checker_refactored.py "PARIS, FRANCE" "ROME, ITALY"
    or
    python url_checker_refactored.py (reads from destinations.txt)
"""

import os
import sys
import time

# --- CONFIG: IGNORE SSL ERRORS ---
os.environ["WDM_SSL_VERIFY"] = "0"
os.environ["WDM_LOCAL"] = "1"

from url_checker_package.config import CONFIG_FILE_NAME, DESTINATIONS_FILE_NAME
from url_checker_package.browser import setup_browser
from url_checker_package.config_manager import (
    get_config_file_path,
    load_configs,
    save_configs,
    load_destinations_from_file
)
from url_checker_package.processor import process_destination


def generate_error_summary():
    """Generate a summary of all errors from error_checks folder"""
    error_dir = os.path.join(os.getcwd(), 'error_checks')
    
    if not os.path.exists(error_dir):
        return
    
    # Find all .txt error files
    error_files = [f for f in os.listdir(error_dir) if f.endswith('.txt')]
    
    if not error_files:
        print("\n[INFO] No error files found in error_checks folder")
        return
    
    print("\n" + "=" * 60)
    print("ERROR SUMMARY")
    print("=" * 60)
    
    errors_by_type = {
        'SELECTION_FAILED': [],
        'NO_RESULTS': [],
        'MISMATCH': [],
        'OTHER': []
    }
    
    for error_file in error_files:
        file_path = os.path.join(error_dir, error_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract destination name from filename
            if 'SELECTION_FAILED' in error_file:
                errors_by_type['SELECTION_FAILED'].append(error_file)
            elif 'NO_RESULTS' in error_file or 'ZERO_RESULTS' in error_file:
                errors_by_type['NO_RESULTS'].append(error_file)
            elif 'MISMATCH' in error_file:
                errors_by_type['MISMATCH'].append(error_file)
            else:
                errors_by_type['OTHER'].append(error_file)
        except Exception as e:
            print(f"[WARNING] Could not read {error_file}: {e}")
    
    # Print summary
    total_errors = sum(len(v) for v in errors_by_type.values())
    print(f"\nTotal error files: {total_errors}\n")
    
    if errors_by_type['SELECTION_FAILED']:
        print(f"❌ SELECTION FAILED ({len(errors_by_type['SELECTION_FAILED'])}):")
        print("   - Destination could not be selected from dropdown")
        for f in errors_by_type['SELECTION_FAILED'][:5]:  # Show first 5
            print(f"     • {f}")
        if len(errors_by_type['SELECTION_FAILED']) > 5:
            print(f"     ... and {len(errors_by_type['SELECTION_FAILED']) - 5} more")
    
    if errors_by_type['NO_RESULTS']:
        print(f"\n⚠ ZERO RESULTS ({len(errors_by_type['NO_RESULTS'])}):")
        print("   - Search completed but returned 0 results")
        for f in errors_by_type['NO_RESULTS'][:5]:
            print(f"     • {f}")
        if len(errors_by_type['NO_RESULTS']) > 5:
            print(f"     ... and {len(errors_by_type['NO_RESULTS']) - 5} more")
    
    if errors_by_type['MISMATCH']:
        print(f"\n⚠ CITY MISMATCH ({len(errors_by_type['MISMATCH'])}):")
        print("   - Selected city doesn't match input (typo/alternate name)")
        for f in errors_by_type['MISMATCH'][:5]:
            print(f"     • {f}")
        if len(errors_by_type['MISMATCH']) > 5:
            print(f"     ... and {len(errors_by_type['MISMATCH']) - 5} more")
    
    if errors_by_type['OTHER']:
        print(f"\n❓ OTHER ERRORS ({len(errors_by_type['OTHER'])}):")
        for f in errors_by_type['OTHER'][:5]:
            print(f"     • {f}")
        if len(errors_by_type['OTHER']) > 5:
            print(f"     ... and {len(errors_by_type['OTHER']) - 5} more")
    
    print(f"\n📁 All error files are in: {error_dir}")
    print("=" * 60)


def main():
    """Main function - orchestrates the entire workflow"""
    print("=" * 60)
    print("ONE Line URL Checker - Location Code Extractor")
    print("=" * 60)
    
    # Determine destination sources
    destinations = []
    
    if len(sys.argv) > 1:
        # Command line arguments
        destinations = sys.argv[1:]
        print(f"\n[INFO] Using {len(destinations)} destination(s) from command line")
    else:
        # Read from destinations.txt file
        destinations_file = get_config_file_path(DESTINATIONS_FILE_NAME)
        destinations = load_destinations_from_file(destinations_file)
        
        if not destinations:
            print("\nUsage:")
            print("  1. Create destinations.txt with one city per line")
            print("  2. Or run: python url_checker_refactored.py \"PARIS, FRANCE\" \"ROME, ITALY\"")
            return
    
    if not destinations:
        print("\n[ERROR] No destinations provided!")
        print("\nUsage:")
        print("  python url_checker_refactored.py \"PARIS, FRANCE\" \"ROME, ITALY\"")
        print("  or create destinations.txt file with one city per line")
        return
    
    print(f"\n[INFO] Processing {len(destinations)} destination(s)")
    
    # Load existing configs (will initialize from destinations.txt if doesn't exist)
    config_file = get_config_file_path(CONFIG_FILE_NAME)
    destinations_file = get_config_file_path(DESTINATIONS_FILE_NAME)
    configs = load_configs(config_file, destinations_file)
    print(f"[INFO] Loaded {len(configs)} existing configurations")
    
    # Setup browser
    driver = setup_browser()
    
    try:
        # Process each destination
        new_configs = {}
        warnings = []
        
        for destination in destinations:
            config = process_destination(driver, destination)
            
            if config:
                # Check for zero results warning
                has_results = config.get('has_results', True)
                
                # Remove has_results before saving (not part of config schema)
                if 'has_results' in config:
                    del config['has_results']
                
                new_configs[destination] = config
                configs[destination] = config
                print(f"\n[SUCCESS] Configuration saved for: {destination}")
                print(f"   Location Code: {config.get('locationCode', 'NOT FOUND')}")
                print(f"   PODs: {config.get('pods', 'NOT FOUND')}")
                
                if not has_results:
                    warning_msg = f"{destination}: ZERO RESULTS (check error_checks folder)"
                    warnings.append(warning_msg)
                    print(f"   ⚠ WARNING: {warning_msg}")
            else:
                print(f"\n[FAILED] ❌ Could not extract configuration for: {destination}")
                print(f"   ERROR: Location code NOT FOUND")
                print(f"   Please verify the city name format or try manually")
            
            # Small delay between destinations
            time.sleep(2)
        
        # Save updated configs
        if new_configs:
            if save_configs(configs, config_file):
                print(f"\n[SUMMARY] Successfully added {len(new_configs)} destination(s)")
                for dest, conf in new_configs.items():
                    print(f"  • {dest}: {conf['locationCode']}")
                
                # Show warnings summary
                if warnings:
                    print(f"\n[WARNINGS] {len(warnings)} destination(s) with issues:")
                    for warning in warnings:
                        print(f"  ⚠ {warning}")
        else:
            print("\n[SUMMARY] No new configurations to save")
    
    finally:
        print("\n[CLEANUP] Closing browser...")
        driver.quit()
        
        # Generate error summary from all .txt files in error_checks
        generate_error_summary()
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
