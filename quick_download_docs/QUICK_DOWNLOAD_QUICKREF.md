# Quick Download Package - Developer Quick Reference

## Quick Start

### Running the Refactored Version
```bash
python quick_download_refactored.py
```

### Switching Between Import/Export
```python
# In quick_download_refactored.py
USE_IMPORT = True   # For import searches
USE_IMPORT = False  # For export searches
```

## Component Quick Reference

### 1. ConfigLoader - Configuration Management
```python
from quick_download_package import ConfigLoader

# Initialize
config = ConfigLoader()

# Load configs
config.load_destination_configs()

# Get destinations
destinations = config.get_destinations()

# Get params for a destination
params = config.get_params_for_destination("ANCONA, ITALY", use_import=True)

# Build URL
url = config.build_search_url(params)

# Generate filename
filename = config.generate_filename()  # ONE_Inland_Rate_20260108.xlsx
```

### 2. BrowserManager - Browser Control
```python
from quick_download_package import BrowserManager

# Initialize
browser = BrowserManager(download_dir="./downloads")

# Setup browser
driver = browser.setup_browser()

# Use driver...
# ...

# Close browser
browser.close_browser()

# Or use context manager
with BrowserManager() as driver:
    # Use driver here
    pass
# Automatically closes

# Restart on crash
driver = browser.restart_browser()
```

### 3. TableScraper - Data Extraction
```python
from quick_download_package import TableScraper

# Initialize (needs driver)
scraper = TableScraper(driver, error_folder="./scraping_errors")

# Scrape table
data = scraper.scrape_inland_tariff_table()

# Returns:
{
    'headers': ['Container Type', 'Weight Range', 'Rate', ...],
    'data': [
        {'Container Type': 'D2', 'Weight Range': '0-21000', 'Rate': '150', ...},
        {'Container Type': 'D4', 'Weight Range': '0-21000', 'Rate': '180', ...},
        ...
    ],
    'totalCount': 25  # For validation
}
```

### 4. DataProcessor - Data Cleaning
```python
from quick_download_package import DataProcessor

# Initialize
processor = DataProcessor()

# Clean and validate data
df = processor.clean_and_validate(
    data={'headers': [...], 'data': [...], 'totalCount': 25},
    destination="ANCONA, ITALY"
)

# Result: pandas.DataFrame with:
# - Destination column added
# - Rate column cleaned (numeric)
# - Metadata columns (City Name, Total Count, Validation)
```

### 5. ExcelManager - File Operations
```python
from quick_download_package import ExcelManager

# Initialize
excel = ExcelManager(
    output_dir="./downloads",
    error_folder="./scraping_errors"
)

# Save DataFrame
success = excel.save_to_excel(
    df=cleaned_dataframe,
    filename="ONE_Inland_Rate_20260108.xlsx",
    destination="ANCONA, ITALY"
)

# First save: Creates new file (or versioned if exists)
# Subsequent saves: Appends to same file

# Save error log
excel.save_exception_log(
    destination="ANCONA, ITALY",
    error=exception_object,
    driver=driver  # Optional, for screenshot
)

# Reset for new run
excel.reset_for_new_run()
```

### 6. DestinationProcessor - Workflow Orchestration
```python
from quick_download_package import DestinationProcessor

# Initialize (needs driver, config_loader, table_scraper)
processor = DestinationProcessor(
    driver=driver,
    config_loader=config_loader,
    table_scraper=table_scraper
)

# Process a destination
result = processor.process_destination(
    destination="ANCONA, ITALY",
    use_import=True
)

# Returns:
{
    'success': True,
    'destination': 'ANCONA, ITALY',
    'data': {...},  # Scraped table data
    'params': {...}  # URL parameters used
}
# Or on error:
{
    'success': False,
    'destination': 'ANCONA, ITALY',
    'error': 'Error message'
}
```

## Common Tasks

### Task: Process One Destination
```python
from quick_download_package import *

# Setup
config = ConfigLoader()
config.load_destination_configs()

browser = BrowserManager()
driver = browser.setup_browser()

scraper = TableScraper(driver)
processor = DestinationProcessor(driver, config, scraper)

# Process
result = processor.process_destination("ANCONA, ITALY", use_import=True)

if result['success']:
    # Clean data
    data_proc = DataProcessor()
    df = data_proc.clean_and_validate(result['data'], result['destination'])
    
    # Save
    excel = ExcelManager()
    excel.save_to_excel(df, "output.xlsx", result['destination'])

# Cleanup
browser.close_browser()
```

### Task: Custom Scraping Logic
```python
from quick_download_package import TableScraper

class MyCustomScraper(TableScraper):
    def scrape_inland_tariff_table(self):
        # Override with custom logic
        # Or call super() and post-process
        data = super().scrape_inland_tariff_table()
        # Custom processing...
        return data
```

### Task: Different Output Format
```python
from quick_download_package import DataProcessor
import json

processor = DataProcessor()
df = processor.clean_and_validate(data, destination)

# Save as JSON instead
df.to_json('output.json', orient='records')

# Save as CSV
df.to_csv('output.csv', index=False)
```

### Task: Batch Process with Custom Filter
```python
from quick_download_package import ConfigLoader

config = ConfigLoader()
config.load_destination_configs()

# Filter destinations by country
italian_destinations = [
    dest for dest in config.get_destinations()
    if 'ITALY' in dest
]

# Process only Italian destinations
for dest in italian_destinations:
    # ... process ...
```

## Debugging Tips

### Enable Verbose Logging
```python
# Add to top of quick_download_refactored.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Isolate Component Testing
```python
# Test just config loading
from quick_download_package import ConfigLoader
config = ConfigLoader()
print(config.load_destination_configs())

# Test just data processing (no browser needed!)
from quick_download_package import DataProcessor
processor = DataProcessor()
test_data = {...}  # Mock data
df = processor.clean_and_validate(test_data, "TEST")
print(df.head())
```

### Save Intermediate Results
```python
# In DestinationProcessor, add after scraping:
import json

result = processor.process_destination(...)
if result['success']:
    # Save raw data for inspection
    with open('raw_data.json', 'w') as f:
        json.dump(result['data'], f, indent=2)
```

### Check Error Files
```bash
# Check error screenshots
ls scraping_errors/*.png

# Check error logs
cat scraping_errors/EXCEPTION_*.txt
```

## Configuration Files

### destination_configs.json
```json
{
  "CITY, COUNTRY": {
    "locationCode": "XXXXX",
    "pols": "PORT1,PORT2",
    "pods": "PORT1,PORT2"
  }
}
```

Generate this by running:
```bash
python url_checker_refactored.py
```

## File Locations

```
automation/
├── quick_download_refactored.py  ← Run this
├── destination_configs.json      ← Required config
│
├── quick_download_package/       ← Package directory
│   ├── __init__.py
│   ├── config_loader.py
│   ├── browser_manager.py
│   ├── table_scraper.py
│   ├── data_processor.py
│   ├── excel_manager.py
│   └── destination_processor.py
│
├── downloads/                     ← Output files
│   └── ONE_Inland_Rate_YYYYMMDD.xlsx
│
└── scraping_errors/               ← Error logs
    ├── SCRAPE_FAILED_*.png
    ├── EXCEPTION_*.png
    └── EXCEPTION_*.txt
```

## Troubleshooting

### Problem: ModuleNotFoundError: No module named 'quick_download_package'
**Solution**: Make sure you're running from the automation directory:
```bash
cd c:\Users\PNS\Desktop\automation
python quick_download_refactored.py
```

### Problem: No destinations found
**Solution**: Run url_checker_refactored.py first to generate destination_configs.json

### Problem: Browser doesn't start
**Solution**: Check ChromeDriver installation:
```python
from selenium import webdriver
driver = webdriver.Chrome()  # Should open browser
```

### Problem: Permission error when saving Excel
**Solution**: Close the Excel file if it's open in another program

### Problem: Table scraping fails
**Solution**: 
1. Check error screenshot in scraping_errors/
2. Verify website structure hasn't changed
3. Add time.sleep() if page loads slowly

### Problem: Data validation fails
**Solution**: Check if "Total: X results" text is on page:
```python
# Add to table_scraper.py for debugging
print(driver.page_source)  # See full page HTML
```

## Performance Tips

### Parallelize Processing (Future Enhancement)
```python
from concurrent.futures import ThreadPoolExecutor

# Process multiple destinations concurrently
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(process_destination, dest)
        for dest in destinations
    ]
```

### Reuse Browser Instance
```python
# Already optimized - browser stays open across destinations
# No need to restart browser for each destination
```

### Cache Configs
```python
# Configs are loaded once at startup
# Already optimized
```

## Testing Examples

### Unit Test Example
```python
import unittest
from quick_download_package import DataProcessor
import pandas as pd

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor()
    
    def test_clean_rate_column(self):
        df = pd.DataFrame({'Rate': ['$100', '€200', '£300']})
        result = self.processor._clean_rate_column(df)
        self.assertEqual(result['Rate'].dtype, 'float64')
        self.assertEqual(result['Rate'][0], 100.0)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test Example
```python
# test_integration.py
from quick_download_package import *

def test_full_workflow():
    config = ConfigLoader()
    config.load_destination_configs()
    
    # Mock browser for testing
    from unittest.mock import Mock
    driver = Mock()
    
    # Test workflow...
    assert len(config.get_destinations()) > 0
    print("✅ Integration test passed")

test_full_workflow()
```

## Quick Reference: Common Errors

| Error | Component | Solution |
|-------|-----------|----------|
| Table not found | TableScraper | Website changed, update selectors |
| Rate conversion fails | DataProcessor | Check currency symbols in _clean_rate_column |
| File permission denied | ExcelManager | Close Excel file |
| Browser crash | BrowserManager | Already auto-restarts |
| Config not found | ConfigLoader | Run url_checker_refactored.py |
| No data scraped | TableScraper | Check error screenshots |

## Getting Help

1. Check error screenshots in `scraping_errors/`
2. Read error logs in `scraping_errors/*.txt`
3. Review architecture diagram in `QUICK_DOWNLOAD_ARCHITECTURE.md`
4. Compare with working example in `url_checker_package`
5. Check if destination_configs.json is up to date

---

**Last Updated**: January 8, 2026  
**Version**: 1.0.0
