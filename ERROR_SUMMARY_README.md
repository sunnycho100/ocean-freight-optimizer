# Error Summary Feature

## Overview
The URL Checker now maintains a central [error_summary.txt](error_checks/error_summary.txt) file that tracks all errors encountered during processing. This provides a quick overview of all issues without needing to check individual error files.

## Error Summary Location
- **File Path:** `error_checks/error_summary.txt`
- **Auto-created:** The file is automatically created when the first error occurs

## Error Types Tracked

### 1. No Rates Available (Not an Error)
These are destinations where the system works correctly but no shipping rates are available.

**Format:**
```
============================================================
No rates available
============================================================
Bucharest, Romania
Istanbul, Turkiye
Moscow, Russia
```

### 2. SELECTION_FAILED
The destination could not be selected from the dropdown menu.

**Format:**
```
------------------------------------------------------------
ERROR: SELECTION_FAILED
------------------------------------------------------------
Destination: Athens, Greece
Error: Could not find destination in dropdown
Timestamp: 2026-01-12 17:23:16
```

### 3. WRONG_COUNTRY
The best matching option was from a different country than expected.

**Format:**
```
------------------------------------------------------------
ERROR: WRONG_COUNTRY
------------------------------------------------------------
Destination: Napoli, Italy
Error: Best available option doesn't match expected country Italy. Found: Napoli, IN, USA
Timestamp: 2026-01-12 17:38:23
```

## Individual Error Files
In addition to the summary, each error still generates:
1. **Screenshot:** Visual capture of the error state (`.png` file)
2. **Detailed Log:** Full error details (`.txt` file)

These files are saved in the `error_checks/` folder with timestamps for reference.

## Example File Structure
```
error_checks/
├── error_summary.txt                              ← Central summary
├── NO_RATES_BUCHAREST_ROMANIA_20260112_172656.txt
├── NO_RATES_BUCHAREST_ROMANIA_20260112_172656.png
├── SELECTION_FAILED_ATHENS_GREECE_20260112_172316.txt
├── SELECTION_FAILED_ATHENS_GREECE_20260112_172316.png
├── WRONG_COUNTRY_NAPOLI_ITALY_20260112_173823.txt
└── WRONG_COUNTRY_NAPOLI_ITALY_20260112_173823.png
```

## Usage
The error summary is automatically updated as errors occur. No manual intervention required. Simply check `error_checks/error_summary.txt` for a quick overview of all issues.
