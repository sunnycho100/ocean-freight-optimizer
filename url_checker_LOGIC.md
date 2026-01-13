# URL Checker - Technical Stack & Extraction Logic

## 📚 Technical Stack Overview

### Core Technologies

#### **1. Selenium WebDriver**
- **Purpose**: Browser automation and web scraping
- **Package**: `selenium`
- **Components Used**:
  - `webdriver.Chrome`: Chrome browser automation
  - `webdriver.ChromeOptions`: Browser configuration
  - `WebDriverWait`: Explicit waits for elements
  - `expected_conditions (EC)`: Element state checks
  - `ActionChains`: Complex user interactions (clicks, keyboard)
  - `By`: Element locator strategies (XPATH, ID, CSS)

#### **2. WebDriver Manager**
- **Purpose**: Automatic ChromeDriver version management
- **Package**: `webdriver_manager.chrome.ChromeDriverManager`
- **Benefit**: Automatically downloads and manages compatible ChromeDriver versions

#### **3. Standard Python Libraries**
- `os`: File system operations, path management
- `sys`: Command line argument handling
- `time`: Delays and timing control
- `json`: Configuration file management
- `urllib.parse`: URL parsing and query parameter extraction
- `datetime`: Timestamp generation for error logs
- `traceback`: Error debugging and stack traces

---

## 🔄 Website Extraction Workflow

### Step-by-Step Process

#### **STEP 1: Initialization & Setup**

**Module**: [`browser.py`](browser.py)

```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
```

**Process**:
1. Configure Chrome options:
   - `--start-maximized`: Full screen for better element visibility
   - `--ignore-certificate-errors`: Bypass SSL warnings
2. Install ChromeDriver automatically via WebDriver Manager
3. Initialize Chrome WebDriver instance
4. Set page load timeout (30 seconds)

---

#### **STEP 2: Navigate to ONE Line Website**

**Module**: [`processor.py`](processor.py)

**URL**: `https://ecomm.one-line.com/one-ecom/prices/rate-tariff/inland-search`

**Process**:
1. `driver.get(BASE_URL)` - Navigate to search page
2. Wait for page to fully load: `document.readyState == "complete"`
3. Handle cookie consent popup (if present)

---

#### **STEP 3: Form Interaction - Import Mode Selection**

**Module**: [`form_handler.py`](form_handler.py)

**Technology**: Selenium element locators with XPATH

```python
WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Import')]"))
).click()
```

**Process**:
1. Locate "Import" radio button using XPATH text matching
2. Click to select Import mode (vs Export)

---

#### **STEP 4: Smart Destination Selection**

**Module**: [`destination_selector.py`](destination_selector.py) - **MOST COMPLEX LOGIC**

**Technologies**:
- Selenium `ActionChains` for keyboard input
- XPATH for element location
- Custom fuzzy matching algorithm

**Process**:

1. **Parse Input Destination**:
   ```
   Input: "PARIS, FRANCE"
   Parsed: city="PARIS", country="FRANCE"
   ```

2. **Smart Search Strategy**:
   - **Hyphenated cities** (e.g., "ARQUES-LA-BATAILLE"): Type first part only
   - **Single-word cities** (e.g., "PARIS"): Type full name for exact match
   - **Multi-word cities** (e.g., "LE HAVRE"): Type meaningful tokens, skip stopwords

3. **Type into Destination Field**:
   ```python
   dest_input = driver.find_element(By.XPATH, "//label[contains(text(), 'Destination')]/following::input[1]")
   dest_input.send_keys(partial_search)
   ```

4. **Wait for Dropdown Options**:
   ```python
   WebDriverWait(driver, DROPDOWN_TIMEOUT).until(
       EC.presence_of_element_located((By.XPATH, "//div[@role='option']"))
   )
   ```

5. **Fuzzy Matching Algorithm**:
   
   **Scoring System**:
   - **Exact Match**: 1000 points
   - **Normalized Match** (ignoring hyphens/accents): 900 points
   - **All Parts Match**: 800 points
   - **Partial Match**: 600 points
   - **First Word Match**: 400 points
   - **Country Match Bonus**: +50 points
   
   **Example**:
   ```
   Input: "MUENSTER, NW, GERMANY"
   Options in dropdown:
     - "MUENSTER, NW, GERMANY" → 1000 (exact)
     - "MUNSTER, GERMANY" → 650 (partial + country)
     - "MUENSTER, USA" → 400 (first word only)
   
   Best match selected: "MUENSTER, NW, GERMANY" (1000 score)
   ```

6. **Selection & Verification**:
   - Click best match using JavaScript or ActionChains
   - Verify selected value matches input
   - Log warnings for mismatches (different country)

---

#### **STEP 5: Select POD (Port of Discharge)**

**Module**: [`form_handler.py`](form_handler.py)

**Process**:
1. Locate POD dropdown: `//label[contains(text(), 'POD')]/following::div[1]`
2. Click to open dropdown
3. Click "Select All" option
4. Close dropdown with ESC key

---

#### **STEP 6: Select Container Types**

**Module**: [`form_handler.py`](form_handler.py)

**Process**:
1. Locate Container Type dropdown
2. Click "Select All"
3. Close dropdown

---

#### **STEP 7: Click Search Button**

**Module**: [`form_handler.py`](form_handler.py)

**Technologies**:
- Selenium `ActionChains` for user-like clicks
- JavaScript execution as fallback for stubborn elements

**Process**:
1. Close any open dropdowns (ESC key)
2. Locate Search button: `//button[.//span[contains(.,'Search')]]`
3. Scroll button into view
4. Wait for button to be enabled
5. Try ActionChains click first
6. Fallback to JavaScript click if intercepted: `driver.execute_script("arguments[0].click();", button)`

---

#### **STEP 8: Wait for Search Results**

**Module**: [`url_extractor.py`](url_extractor.py)

**Technologies**:
- Selenium explicit waits
- XPATH element detection

**Process**:
1. Wait 5 seconds for page transition
2. Wait for "Download All" button to appear (indicates results loaded):
   ```python
   WebDriverWait(driver, 30).until(
       EC.visibility_of_element_located((
           By.XPATH, "//button[contains(., 'Download All')]"
       ))
   )
   ```
3. If timeout, continue anyway (may still have URL parameters)

---

#### **STEP 9: Extract URL Parameters** ⭐

**Module**: [`url_extractor.py`](url_extractor.py)

**Technologies**:
- `urllib.parse`: URL parsing
- `urlparse()`: Parse URL structure
- `parse_qs()`: Extract query string parameters

**Process**:

1. **Get Current URL**:
   ```python
   current_url = driver.current_url
   # Example: https://ecomm.one-line.com/...?destinationLocationCode=FRPAR&pods=ALL&pols=ALL
   ```

2. **Parse URL**:
   ```python
   from urllib.parse import urlparse, parse_qs
   
   parsed = urlparse(current_url)
   params = parse_qs(parsed.query)
   ```

3. **Extract Key Parameters**:
   ```python
   location_code = params.get('destinationLocationCode', [None])[0]  # "FRPAR"
   pols = params.get('pols', [None])[0]  # "ALL"
   pods = params.get('pods', [None])[0]  # "ALL"
   ```

4. **Build Configuration Object**:
   ```python
   config = {
       'locationCode': 'FRPAR',
       'pols': 'ALL',
       'pods': 'ALL'
   }
   ```

---

#### **STEP 10: Results Validation**

**Module**: [`url_extractor.py`](url_extractor.py)

**Technologies**:
- Selenium element searching
- DOM text content analysis

**Process**:

1. **Check for Zero Results**:
   - **Strategy 1**: Look for "Total: 0" text indicator
   - **Strategy 2**: Look for "No data" or "no result" messages
   - **Strategy 3**: Count table rows (`//table//tbody//tr`)

2. **If Zero Results Found**:
   - Set `has_results = False`
   - Save warning screenshot to `error_checks/`
   - Create log file: `ZERO_RESULTS_{destination}_{timestamp}.txt`
   - Flag for user review

---

#### **STEP 11: Save Configuration**

**Module**: [`config_manager.py`](config_manager.py)

**Technologies**:
- `json` module for file I/O
- UTF-8 encoding for international characters

**Process**:

1. **Load Existing Configs**:
   ```python
   configs = load_configs('destination_configs.json')
   ```

2. **Add New Entry**:
   ```python
   configs["PARIS, FRANCE"] = {
       "locationCode": "FRPAR",
       "pols": "ALL",
       "pods": "ALL"
   }
   ```

3. **Save to JSON**:
   ```python
   with open(config_file, 'w', encoding='utf-8') as f:
       json.dump(configs, f, indent=2, ensure_ascii=False)
   ```

**Output Format**:
```json
{
  "PARIS, FRANCE": {
    "locationCode": "FRPAR",
    "pols": "ALL",
    "pods": "ALL"
  }
}
```

---

## 🛡️ Error Handling & Logging

### Error Detection Modules

#### **1. Selection Failures**

**Module**: [`processor.py`](processor.py)

**Triggers**:
- Destination not found in dropdown
- City name doesn't exist in ONE Line system
- Network timeout during selection

**Actions**:
- Screenshot: `SELECTION_FAILED_{city}_{timestamp}.png`
- Log file: `SELECTION_FAILED_{city}_{timestamp}.txt`
- Append to error summary

---

#### **2. Zero Results Warnings**

**Module**: [`url_extractor.py`](url_extractor.py)

**Triggers**:
- Search completes but returns 0 tariff records
- No service available to destination
- Invalid POD/POL configuration

**Actions**:
- Screenshot: `ZERO_RESULTS_{city}_{timestamp}.png`
- Warning log: `ZERO_RESULTS_{city}_{timestamp}.txt`
- Continue processing (location code still extracted)

---

#### **3. City Mismatch Warnings**

**Module**: [`destination_selector.py`](destination_selector.py)

**Triggers**:
- Selected city in different country (e.g., wanted "VALENCE, FRANCE" but selected "VALENCIA, SPAIN")
- Fuzzy match score below confidence threshold

**Actions**:
- Log warning: `WRONG_COUNTRY_{city}_{timestamp}.txt`
- Continue processing with warning flag

---

## 📊 Data Flow Diagram

```
┌─────────────────┐
│ destinations.txt│
│ or CLI args     │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ main()              │
│ - Load configs      │
│ - Setup browser     │
└────────┬────────────┘
         │
         ▼ (for each destination)
┌──────────────────────────────────────────┐
│ process_destination()                    │
│ ┌─────────────────────────────────────┐  │
│ │ 1. Navigate to ONE Line             │  │
│ │ 2. Handle cookies                   │  │
│ │ 3. Select Import mode               │  │
│ │ 4. Smart destination selection      │  │
│ │ 5. Select POD (all)                 │  │
│ │ 6. Select Container Type (all)      │  │
│ │ 7. Click Search                     │  │
│ │ 8. Wait for results                 │  │
│ │ 9. Extract URL parameters           │  │
│ │ 10. Validate results                │  │
│ └─────────────────────────────────────┘  │
└────────┬─────────────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Config Object           │
│ {                       │
│   locationCode: "FRPAR",│
│   pols: "ALL",          │
│   pods: "ALL"           │
│ }                       │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│ destination_configs.json │
│ (persisted)              │
└──────────────────────────┘
```

---

## 🔧 Module Breakdown

| Module | Purpose | Key Technologies |
|--------|---------|------------------|
| [`url_checker_refactored.py`](url_checker_refactored.py) | Main entry point, orchestration | `sys`, `os`, `time` |
| [`browser.py`](browser.py) | Browser initialization | Selenium WebDriver, WebDriver Manager |
| [`processor.py`](processor.py) | Main workflow orchestration | Selenium WebDriverWait |
| [`destination_selector.py`](destination_selector.py) | Smart fuzzy matching & selection | XPATH, ActionChains, Custom scoring |
| [`form_handler.py`](form_handler.py) | Form interactions (clicks, inputs) | XPATH, ActionChains, JavaScript execution |
| [`url_extractor.py`](url_extractor.py) | URL parameter extraction | `urllib.parse`, XPATH, DOM analysis |
| [`config_manager.py`](config_manager.py) | JSON config persistence | `json`, file I/O |
| [`config.py`](config.py) | Constants and configuration | Python constants |
| [`error_summary.py`](error_summary.py) | Error aggregation & reporting | File I/O, text processing |

---

## 🎯 Key Design Patterns

### 1. **Separation of Concerns**
- Each module has a single responsibility
- Browser logic separate from business logic
- Configuration separate from execution

### 2. **Defensive Programming**
- Multiple fallback strategies (ActionChains → JavaScript click)
- Graceful degradation (continue on warnings)
- Comprehensive error logging

### 3. **Smart Automation**
- Fuzzy matching handles city name variations
- Adaptive search strategies (hyphenated vs single-word)
- Result validation prevents false positives

### 4. **Observability**
- Detailed console logging at each step
- Screenshot capture on errors
- Structured error logs with timestamps

---

## 📝 Configuration Files

### Input: `destinations.txt`
```
PARIS, FRANCE
ROME, ITALY
HAMBURG, GERMANY
```

### Output: `destination_configs.json`
```json
{
  "PARIS, FRANCE": {
    "locationCode": "FRPAR",
    "pols": "ALL",
    "pods": "ALL"
  },
  "ROME, ITALY": {
    "locationCode": "ITROM",
    "pols": "ALL",
    "pods": "ALL"
  }
}
```

---

## 🚀 Execution Flow Summary

1. **Initialize** → Setup Chrome browser with WebDriver Manager
2. **Navigate** → Load ONE Line inland search page
3. **Interact** → Fill form fields using Selenium element locators
4. **Match** → Smart fuzzy matching for destination selection
5. **Submit** → Click Search with retry logic
6. **Extract** → Parse URL query parameters using urllib
7. **Validate** → Check for zero results and mismatches
8. **Persist** → Save configurations to JSON
9. **Report** → Generate error summary from error_checks folder
10. **Cleanup** → Close browser and exit

---

**Generated**: January 13, 2026  
**Project**: ONE Line URL Checker - Location Code Extractor  
**Author**: Automation System Documentation
