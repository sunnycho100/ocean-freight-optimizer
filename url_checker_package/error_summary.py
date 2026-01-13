"""Error summary management - tracks all errors in a central summary file"""

import os
from datetime import datetime
from typing import Literal


def get_error_summary_path():
    """Get the path to the error summary file"""
    return os.path.join(os.getcwd(), 'error_checks', 'error_summary.txt')


def initialize_error_summary():
    """Initialize the error summary file if it doesn't exist"""
    summary_path = get_error_summary_path()
    error_dir = os.path.dirname(summary_path)
    os.makedirs(error_dir, exist_ok=True)
    
    if not os.path.exists(summary_path):
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ERROR SUMMARY - URL Checker\n")
            f.write("=" * 60 + "\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")


def append_no_rates(destination_name: str, city: str, country: str):
    """
    Append a 'No rates available' entry to the summary.
    These are not errors, just information about unavailable routes.
    
    Args:
        destination_name: Full destination string (e.g., "BUCHAREST, ROMANIA")
        city: City name
        country: Country name
    """
    initialize_error_summary()
    summary_path = get_error_summary_path()
    
    try:
        # Check if we need to add the "No rates available" header
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            needs_header = "No rates available" not in content
        
        with open(summary_path, 'a', encoding='utf-8') as f:
            if needs_header:
                f.write("\n" + "=" * 60 + "\n")
                f.write("No rates available\n")
                f.write("=" * 60 + "\n")
            
            f.write(f"{city}, {country}\n")
        
        print(f"[INFO] Added to error summary: No rates for {city}, {country}")
    except Exception as e:
        print(f"[WARNING] Could not update error summary: {e}")


def append_error(
    error_type: Literal["SELECTION_FAILED", "WRONG_COUNTRY", "ZERO_RESULTS", "MISMATCH"],
    destination_name: str,
    error_message: str,
    timestamp: str = None
):
    """
    Append an error to the summary file.
    
    Args:
        error_type: Type of error (SELECTION_FAILED, WRONG_COUNTRY, ZERO_RESULTS, MISMATCH)
        destination_name: Full destination string (e.g., "PARIS, FRANCE")
        error_message: Description of the error
        timestamp: Optional timestamp string
    """
    initialize_error_summary()
    summary_path = get_error_summary_path()
    
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        with open(summary_path, 'a', encoding='utf-8') as f:
            f.write("\n" + "-" * 60 + "\n")
            f.write(f"ERROR: {error_type}\n")
            f.write("-" * 60 + "\n")
            f.write(f"Destination: {destination_name}\n")
            f.write(f"Error: {error_message}\n")
            f.write(f"Timestamp: {timestamp}\n")
        
        print(f"[INFO] Added to error summary: {error_type} for {destination_name}")
    except Exception as e:
        print(f"[WARNING] Could not update error summary: {e}")
