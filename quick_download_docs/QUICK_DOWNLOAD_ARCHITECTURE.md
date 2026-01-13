# Quick Download Package - Architecture Diagram

## Component Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                  quick_download_refactored.py                    │
│                      (Main Entry Point)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ orchestrates
                         ▼
        ┌────────────────────────────────────────────┐
        │       quick_download_package/              │
        │                                             │
        │  ┌──────────────────────────────────────┐  │
        │  │      ConfigLoader                    │  │
        │  │  • Load destination configs          │  │
        │  │  • Build search URLs                 │  │
        │  │  • Generate filenames                │  │
        │  └──────────────┬───────────────────────┘  │
        │                 │                           │
        │  ┌──────────────▼───────────────────────┐  │
        │  │      BrowserManager                  │  │
        │  │  • Setup Chrome driver               │  │
        │  │  • Handle SSL settings               │  │
        │  │  • Restart on crash                  │  │
        │  └──────────────┬───────────────────────┘  │
        │                 │                           │
        │                 │ provides driver           │
        │                 ▼                           │
        │  ┌──────────────────────────────────────┐  │
        │  │      DestinationProcessor            │  │
        │  │  • Navigate to search page           │◄─┼─── uses ConfigLoader
        │  │  • Handle cookies & popups           │  │
        │  │  • Execute search                    │  │
        │  │  • Coordinate workflow               │  │
        │  └──────────────┬───────────────────────┘  │
        │                 │                           │
        │                 │ triggers                  │
        │                 ▼                           │
        │  ┌──────────────────────────────────────┐  │
        │  │      TableScraper                    │  │
        │  │  • Extract table data via JS         │  │
        │  │  • Target Inland Tariff (DOOR)       │  │
        │  │  • Get total count for validation    │  │
        │  │  • Save error screenshots            │  │
        │  └──────────────┬───────────────────────┘  │
        │                 │                           │
        │                 │ raw data                  │
        │                 ▼                           │
        │  ┌──────────────────────────────────────┐  │
        │  │      DataProcessor                   │  │
        │  │  • Clean Rate column                 │  │
        │  │  • Add destination column            │  │
        │  │  • Add validation metadata           │  │
        │  │  • Validate row counts               │  │
        │  └──────────────┬───────────────────────┘  │
        │                 │                           │
        │                 │ cleaned DataFrame         │
        │                 ▼                           │
        │  ┌──────────────────────────────────────┐  │
        │  │      ExcelManager                    │  │
        │  │  • Save to Excel                     │  │
        │  │  • Version files (_2, _3)            │  │
        │  │  • Append within same run            │  │
        │  │  • Log errors                        │  │
        │  └──────────────────────────────────────┘  │
        │                                             │
        └─────────────────────────────────────────────┘
```

## Data Flow

```
Start
  │
  ▼
[Load Configs] ──────► ConfigLoader
  │                      ├─ Read destination_configs.json
  │                      ├─ Load destination list
  │                      └─ Prepare URL parameters
  ▼
[Setup Browser] ─────► BrowserManager
  │                      ├─ Configure Chrome options
  │                      ├─ Set download directory
  │                      └─ Initialize WebDriver
  ▼
[For Each Destination]
  │
  ▼
[Build URL] ─────────► ConfigLoader
  │                      └─ build_search_url()
  ▼
[Process Destination]─► DestinationProcessor
  │                      ├─ Navigate to URL
  │                      ├─ Handle cookies
  │                      ├─ Click search
  │                      └─ Wait for results
  ▼
[Scrape Table] ──────► TableScraper
  │                      ├─ Find Inland Tariff section
  │                      ├─ Execute JavaScript extraction
  │                      ├─ Get total count
  │                      └─ Return raw data
  ▼
[Clean Data] ────────► DataProcessor
  │                      ├─ Clean Rate column (remove $, €, etc.)
  │                      ├─ Add Destination column
  │                      ├─ Add metadata (City, Count, Validation)
  │                      └─ Return cleaned DataFrame
  ▼
[Save to Excel] ─────► ExcelManager
  │                      ├─ First save: Create file (or version)
  │                      ├─ Subsequent saves: Append to same file
  │                      └─ Write to Excel
  ▼
[Next Destination] ───┐
  │                    │
  └────────────────────┘
  │
  ▼
[All Done]
  │
  ▼
[Close Browser] ─────► BrowserManager
  │
  ▼
[Display Summary]
  │
  ▼
End
```

## Error Handling Flow

```
┌─────────────────────────┐
│  Exception Detected     │
└──────────┬──────────────┘
           │
           ├──► Browser Crash? ────► BrowserManager.restart_browser()
           │                          │
           │                          └──► Reinitialize components
           │
           ├──► Scraping Failed? ──► TableScraper._save_error_screenshot()
           │                          │
           │                          └──► Fallback text extraction
           │
           ├──► No Data? ─────────► DataProcessor → None
           │                          │
           │                          └──► ExcelManager._log_no_data_error()
           │
           └──► Other Exception? ──► ExcelManager.save_exception_log()
                                      ├─ Save screenshot
                                      └─ Save error text
```

## Module Dependencies

```
quick_download_refactored.py
    ├─ imports ─► ConfigLoader
    ├─ imports ─► BrowserManager
    ├─ imports ─► TableScraper
    ├─ imports ─► DataProcessor
    ├─ imports ─► ExcelManager
    └─ imports ─► DestinationProcessor

DestinationProcessor
    ├─ uses ─► ConfigLoader (get params, build URL)
    └─ uses ─► TableScraper (scrape data)

TableScraper
    └─ uses ─► WebDriver (from BrowserManager)

DataProcessor
    └─ uses ─► pandas

ExcelManager
    └─ uses ─► pandas
```

## File System Interactions

```
Reads:
  ├─ destination_configs.json ──► ConfigLoader
  └─ (existing Excel file) ───────► ExcelManager (for appending)

Writes:
  ├─ downloads/
  │   └─ ONE_Inland_Rate_YYYYMMDD.xlsx ──► ExcelManager
  │       └─ (or _2, _3 if exists)
  │
  └─ scraping_errors/
      ├─ SCRAPE_FAILED_*.png ────────► TableScraper
      ├─ NO_DATA_*.txt ──────────────► ExcelManager
      └─ EXCEPTION_*.png/.txt ───────► ExcelManager
```

## Key Architectural Decisions

### 1. **Separation of Concerns**
Each module has ONE primary responsibility:
- Config → Configuration
- Browser → WebDriver lifecycle
- Scraper → Data extraction
- Processor → Data transformation
- Excel → File I/O
- DestinationProcessor → Workflow orchestration

### 2. **Dependency Injection**
Components receive dependencies (driver, config_loader) rather than creating them:
```python
TableScraper(driver, error_folder)  # Receives driver
DestinationProcessor(driver, config_loader, table_scraper)  # Receives all deps
```

### 3. **Single Source of Truth**
- Configurations: ConfigLoader only
- Browser: BrowserManager only
- Excel state: ExcelManager only

### 4. **Error Isolation**
Each component handles its own errors:
- TableScraper → screenshots
- ExcelManager → file errors
- BrowserManager → browser crashes

### 5. **Stateful Where Needed**
- ExcelManager tracks: `current_run_filepath`, `first_save_done`
- Allows: Same file across destinations, versioning across runs

---

This architecture makes debugging fast because:
1. **Clear boundaries** - Know which module to check
2. **Isolated testing** - Test each component separately
3. **Obvious data flow** - Follow the data through components
4. **Explicit errors** - Errors tell you exactly which component failed
