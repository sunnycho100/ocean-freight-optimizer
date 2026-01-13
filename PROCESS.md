# Automation Development Process - ONE Line Inland Tariff Scraper

## Project Goal
Automate downloading inland rate data from ONE Line shipping website for multiple European destinations.

---

## Development Timeline

### Phase 1: Initial Modal Download Attempts
**Goal:** Click download button in modal popup  
**Issue:** Modal download button unclickable despite 5 different clicking methods (direct click, JavaScript click, ActionChains, coordinate click, iframe switching)  
**Resolution:** Abandoned modal approach entirely → Pivoted to direct web scraping strategy

---

### Phase 2: Web Scraping Implementation
**Goal:** Extract table data directly from webpage instead of downloading files  
**Initial Success:** JavaScript-based table extraction working  
**Issue:** Extracting wrong data - getting Arbitrary Tariff (CY) instead of Inland Tariff (DOOR)  
**Debug Method:** Analyzed page structure, found multiple tariff sections on same page  
**Resolution:** Modified JavaScript selector to target section containing "Inland Tariff" and "DOOR" keywords while explicitly excluding "Arbitrary Tariff"

---

### Phase 3: Multi-Destination Processing
**Goal:** Process multiple cities from destinations.txt file  
**Implementation:** Added file reading, loop through destinations, append all to single Excel file  
**Initial Issue:** Each destination needed unique URL parameters (location codes, port lists)  
**Debug Method:** Inspected URL patterns, identified `destinationLocationCode`, `pols`, `pods` parameters  
**Resolution:** Hardcoded configs for initial destinations (Netherlands NLGSG, Italy ITAOI) with specific port lists

---

### Phase 4: Data Type Cleaning
**Goal:** Ensure Rate column is numeric for Excel calculations  
**Issue:** Rate values stored as text strings with currency symbols (€, $), causing Excel warnings  
**Debug Method:** Checked pandas DataFrame dtypes, found object type instead of numeric  
**Resolution:** Added `pd.to_numeric()` conversion with regex to strip currency symbols and commas before saving

---

### Phase 5: Configuration Externalization
**Goal:** Move destination-specific configs out of hardcoded script  
**Implementation:** Created `destination_configs.json` with structure:
```json
{
  "CITY, COUNTRY": {
    "locationCode": "XXXXX",
    "pols": "PORT1,PORT2",
    "pods": "PORT1,PORT2"
  }
}
```
**Resolution:** Script now loads configs dynamically, making it scalable for new destinations

---

### Phase 6: Automated Config Discovery Tool
**Goal:** Automatically extract location codes instead of manual URL parsing  
**Initial Approach:** Created url_parser.py for manual URL analysis  
**User Feedback:** "Delete the URL parser I'm not doing that process myself"  
**New Strategy:** Build url_checker.py to automate form filling and URL parameter extraction

**Critical Challenges:**
1. **Page Load Failures:** Form elements not found, TimeoutException on Destination label
   - **Debug:** Compared with working crawler.py which had proven form automation
   - **Root Cause:** Different timing patterns and missing fallback logic
   
2. **Destination Input Format Issues:** 
   - **Problem:** Typing "PARIS, FRANCE" didn't show dropdown options
   - **Debug:** Examined crawler.py parameters - found it uses `DESTINATION_PARTIAL = "PARIS, PARIS"` and `DESTINATION_VERIFY = "FRANCE"`
   - **Key Insight:** ONE Line search expects city repeated twice in input field, then searches for country in dropdown
   - **Resolution:** Modified to type "CITY, CITY" and search for "COUNTRY"

3. **JavaScript Syntax Errors in Dropdown Selection:**
   - **Issue:** Browser crashing with "Unexpected token '{'" error
   - **Debug:** Found double braces `{{block: 'center'}}` in JavaScript string
   - **Resolution:** Changed to single braces `{block: 'center'}`

4. **Destination Name Variations:**
   - **Problem:** Cities like "FOS-SUR-MER" or "ANCONA" had different search patterns
   - **User Input:** "Try ANCONA first instead of ANCONA, ANCONA"
   - **Resolution:** Implemented variation testing in priority order:
     1. Original city name (e.g., "ANCONA")
     2. City without hyphens (e.g., "FOS SUR MER")  
     3. City repeated format (e.g., "ANCONA, ANCONA")
     4. No-hyphen repeated (e.g., "FOS SUR MER, FOS SUR MER")

**Final Implementation:** url_checker.py successfully extracts all 13+ destination configs by:
- Using exact crawler.py form automation flow (Import → Destination → POD → Container Type → Date/Weight → Search)
- Trying multiple name variations automatically
- Extracting URL parameters (locationCode, pols, pods) from search results
- Saving to destination_configs.json

---

### Phase 7: Excel Metadata Enhancement
**Goal:** Add city name and total result count to Excel output  
**Requirements:** 
- 3 columns to the right of table data
- City name and total count on first row of each destination's data block
- Total count extracted from "Total: X results" text on webpage

**Implementation:**
1. Modified JavaScript scraper to find and extract "Total: X results" text from Inland Tariff section
2. Added 2 empty spacer columns + "City Name" + "Total Count" columns
3. Set values only on first row of each destination's data
4. Subsequent destinations append with their own first-row metadata

---

## Key Debugging Lessons

### 1. **Copy Working Patterns Exactly**
When url_checker.py failed, the breakthrough was copying crawler.py's exact logic (timing, XPaths, fallbacks) rather than reimplementing from scratch.

### 2. **Inspect Actual Website Behavior**
The "PARIS, PARIS" input format was non-intuitive but discovered by examining working code's actual parameters, not documentation.

### 3. **Use Progressive Fallbacks**
Destination name variations showed importance of trying multiple approaches in order of likelihood rather than failing immediately.

### 4. **JavaScript String Escaping**
Python f-strings with JavaScript code require careful handling of braces - `{` not `{{` inside JS objects.

### 5. **Section-Based Targeting**
When multiple similar sections exist on a page (Inland vs Arbitrary tariff), targeting by section text content before finding tables prevents data extraction errors.

---

## Final Architecture

### Files:
- **quick_download.py** (732 lines): Production scraper for multi-destination rate extraction
- **destination_configs.json**: External config mapping cities to location codes and ports
- **destinations.txt**: Simple list of cities to process
- **url_checker.py** (502 lines): Automated tool to extract new destination configs
- **crawler.py** (450 lines): Reference implementation with proven form automation patterns

### Workflow:
1. Add new city to destinations.txt
2. Run `python url_checker.py "CITY, COUNTRY"` to auto-extract config → saves to JSON
3. Run `python quick_download.py` to scrape all cities in destinations.txt
4. Output: Single Excel file with all destinations, metadata columns, numeric Rate values

### Success Metrics:
- ✅ 13 cities processed automatically
- ✅ All location codes extracted successfully
- ✅ Single consolidated Excel output per run
- ✅ Numeric data types for calculations
- ✅ Metadata tracking (city name, result counts)

---

## Efficiency Improvements for AI Agent Workflow

### What Worked Well:
1. **Incremental testing** - Testing with 1-4 cities before scaling to all 13
2. **Clear error descriptions** - User providing exact error messages and screenshots helped debugging
3. **Reference code** - Having crawler.py as working reference accelerated url_checker.py fixes
4. **Explicit requirements** - "3 columns to the right" and "city name on first row" were precise

### What Could Be More Efficient:
1. **Earlier pattern recognition** - Could have analyzed crawler.py's destination logic sooner
2. **Consolidated testing** - Some fixes required multiple test runs; batch testing variations might save time
3. **Proactive validation** - Could have checked for JavaScript escaping issues before first run
4. **User workflow questions** - Earlier clarification that manual URL parsing was undesirable would have avoided url_parser.py creation

### Best Practices Identified:
- ✅ Always compare with known-working code when debugging similar functionality
- ✅ Test edge cases (hyphens, special characters) early in development
- ✅ Validate data types immediately after extraction
- ✅ Use external config files from the start for scalability
- ✅ Implement retry/fallback logic for user input variations

---

**Total Development Time:** Multiple iterations across form automation, web scraping, data cleaning, and config management  
**Final Result:** Fully automated, scalable system requiring only city name input to extract complete inland tariff datasets
