# Freight Route Optimizer

A comprehensive freight route analysis and visualization system for comparing inland transportation rates from multiple shipping carriers (ONE Line & HAPAG-Lloyd) through various PODs (Ports of Discharge) to European destinations.

## Quick Start

### One-Click Launch (Windows)
```bash
start.bat
```
This will:
- Start the Flask API server (port 5000)
- Start the React frontend (port 3001)
- Automatically open your browser to the multi-carrier dashboard

Server windows are minimized to the taskbar for a clean user experience.

---

## System Architecture

### 1. **Data Collection** (`quick_download_refactored.py`)
Automatically scrapes inland freight rates from ONE Line website for multiple destinations using a modular package structure for better organization and debugging.

**Usage:**
```bash
python quick_download_refactored.py
```

**Output:** 
- `downloads/ONE_Inland_Rate_YYYYMMDD.xlsx` - Raw scraped data

---

### 2. **Data Processing**

#### ONE Processor (`ONE_processor.py`)
Combines inland rates with ocean freight costs and calculates total rates with proper ranking.

**Usage:**
```bash
python ONE_processor.py
```

**Features:**
- Merges inland rates with ocean freight costs from `source/ocean_freight.xlsx`
- Extracts Transport Mode from Remarks column (text before semicolon)
- Calculates total rates (inland + ocean)
- Ranks routes by cost for each destination-container combination using `dense` ranking (1,2,3,4... no gaps)
- Removes validation columns for clean output

**Output:**
- `downloads/ONE_Inland_Rate_Processed_YYYYMMDD_HHMMSS.xlsx` - Processed data with rankings

#### HAPAG Extractor (`hapag_extractor.py`)
Automated web scraping tool for HAPAG-Lloyd landfreight surcharges.

**Usage:**
```bash
python hapag_extractor.py
```

**Features:**
- Playwright-based automation with stealth mode
- Automated login using credentials from `.env` file
- Extracts landfreight surcharges with sub-options (Combined Rail, Between modes)
- Preserves complete rate structures including alternative transport options

**Output:**
- `downloads/hapag_surcharges_YYYYMMDD.xlsx` - Raw HAPAG data with sub-options

---

### 3. **Backend API** (`api_server.py`)
Flask REST API that serves processed data from multiple carriers to the frontend.

**Endpoints:**

**ONE Line:**
- `GET /api/destinations` - List of all destinations
- `GET /api/container-types` - List of container types
- `GET /api/routes/<destination>/<container_type>` - Ranked routes for specific criteria

**HAPAG-Lloyd:**
- `GET /api/hapag/destinations` - List of HAPAG destinations
- `GET /api/hapag/route/<destination>/<container_type>` - HAPAG rates with sub-options

**System:**
- `GET /api/health` - Health check endpoint

**Auto-starts on:** `http://localhost:5000`

**Key Features:**
- Data caching for improved performance
- Runtime parsing of HAPAG sub-options (preserves Combined Rail, Between transport modes)
- Automatic detection of latest data files in downloads folder

---

### 4. **Frontend Dashboard** (`freight-ui/`)
React/TypeScript multi-carrier comparison platform with three specialized views.

**Three Dashboard Views:**

1. **ONE Dashboard** - ONE Line inland rates visualization
   - Top 3 routes ranked by total cost
   - Map comparison grid with embedded Google Maps
   - Transport Mode and Remarks columns
   - Worst route comparison

2. **HAPAG Dashboard** - HAPAG-Lloyd surcharges with sub-options
   - Landfreight surcharge display
   - Sub-option selector for alternative transport modes (Combined Rail, Between)
   - Container type filtering (20STD, 40STD, 40HC)
   - Dynamic rate updates based on selection

3. **Summary Comparison** - Side-by-side carrier comparison
   - Unified container type selector (auto-converts: 20 FT ↔ 20STD, 40 FT ↔ 40STD, etc.)
   - City name normalization (handles hyphens: ARQUES-LA-BATAILLE vs ARQUES LA BATAILLE)
   - Synchronized filtering across both carriers
   - Direct rate comparison table

**Technology Stack:**
- React 18 with TypeScript
- Component-based architecture (OneDashboard, HapagDashboard, SummaryDashboard)
- CSS custom properties for theming
- Google Maps iframe embed (no API key required)
- Incremental TypeScript compilation for faster builds

**Auto-starts on:** `http://localhost:3001`

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Chrome browser (for data scraping)
- Windows OS (for `start.bat` automation)
- HAPAG-Lloyd account credentials (for HAPAG data extraction)

### Initial Setup

**For detailed step-by-step setup instructions for new computers, see [INITIAL_SETUP.md](INITIAL_SETUP.md)**

1. **Install Python dependencies:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install pandas openpyxl playwright playwright-stealth python-dotenv flask flask-cors selenium
playwright install chromium
```

2. **Install frontend dependencies:**
```bash
cd freight-ui
npm install
cd ..
```

3. **Create environment file (.env):**
```
HAPAG_USERNAME=your_username_here
HAPAG_PASSWORD=your_password_here
```

4. **Prepare data files:**
   - Place ocean freight rates in `source/ocean_freight.xlsx`
   - Configure destinations in `destinations.txt`
   - Run data collection and processing

---

## Detailed Workflow

### Data Collection from Multiple Carriers

#### ONE Line Data
1. **Collect inland rates:**
```bash
python quick_download_refactored.py
```

2. **Process data:**
```bash
python ONE_processor.py
```

#### HAPAG-Lloyd Data
1. **Extract surcharges:**
```bash
python hapag_extractor.py
```
(Requires `.env` file with HAPAG credentials)

### Adding New Destinations

1. **Extract destination configuration:**
```bash
python url_checker_refactored.py "ROTTERDAM, NETHERLANDS"
```
This updates `destination_configs.json` with location codes and POD information.

2. **Add to destinations list:**
Edit `destinations.txt`:
```
ANCONA, ITALY
ANTWERP, BELGIUM
ROTTERDAM, NETHERLANDS  ← New addition
```

3. **Collect data:**
```bash
python quick_download_refactored.py  # ONE Line
python hapag_extractor.py            # HAPAG-Lloyd
```

4. **Process data:**
```bash
python ONE_processor.py
```

5. **Launch dashboard:**
```bash
start.bat
```

---

## Google Maps Integration

### Embedded Maps
- Uses public Google Maps iframe embed (no API key needed)
- Displays route from POD to destination
- Customizable zoom levels for grid vs single view
- Falls back to "View in Google Maps" button if embed is blocked

### Map Features
- Grid View: Shows 3 maps side-by-side for top routes comparison
- Compact Info: Minimal route information above each map
- External Link: Button to open full directions in Google Maps
- Location Cleaning: Removes region codes for clearer map queries

---

## Project Structure

```
automation/
├── start.bat                        # One-click launcher
├── api_server.py                    # Flask REST API (multi-carrier)
├── ONE_processor.py                 # ONE data processing pipeline
├── hapag_extractor.py               # HAPAG data extraction (Playwright)
├── quick_download_refactored.py     # ONE data collection (Selenium)
├── url_checker_refactored.py        # Destination config extractor
├── destinations.txt                 # Target destinations list
├── destination_configs.json         # Location codes & POD mappings
├── .env                             # HAPAG credentials (create manually)
├── downloads/                       # Scraped & processed data
│   ├── ONE_Inland_Rate_*.xlsx
│   ├── ONE_Inland_Rate_Processed_*.xlsx
│   └── hapag_surcharges_*.xlsx
├── source/
│   └── ocean_freight.xlsx          # Ocean freight rates
├── hapag_module/                    # HAPAG extraction modules
│   ├── auth_manager.py
│   ├── browser_manager.py
│   ├── config_loader.py
│   ├── data_extractor.py
│   ├── excel_exporter.py
│   ├── main_runner.py
│   └── quote_scraper.py
├── quick_download_package/          # ONE scraper components
│   ├── browser_manager.py
│   ├── config_loader.py
│   ├── destination_processor.py
│   ├── excel_manager.py
│   ├── table_scraper.py
│   └── __init__.py
├── url_checker_package/             # URL checker components
│   ├── browser.py
│   ├── config.py
│   ├── config_manager.py
│   ├── destination_selector.py
│   ├── form_handler.py
│   ├── processor.py
│   ├── url_extractor.py
│   └── __init__.py
└── freight-ui/                      # React frontend
    ├── src/
    │   ├── components/              # React components
    │   │   ├── OneDashboard.tsx     # ONE Line view
    │   │   ├── HapagDashboard.tsx   # HAPAG-Lloyd view
    │   │   ├── SummaryDashboard.tsx # Comparison view
    │   │   ├── RouteTable.tsx
    │   │   ├── RouteMap.tsx
    │   │   ├── FiltersPanel.tsx
    │   │   └── RouteTableTabs.tsx
    │   ├── utils/
    │   │   └── googleMapsHelper.ts
    │   ├── styles/
    │   │   └── app.css
    │   └── types.ts
    └── package.json
```

---

## Configuration Files

### `destinations.txt`
One destination per line:
```
VALENCE, DROME, FRANCE
LEUTKIRCH IM ALLGAEU, BW, GERMANY
MUENSTER, NW, GERMANY
```

### `destination_configs.json`
Auto-generated by `url_checker.py`:
```json
{
  "ANCONA, ITALY": {
    "locationCode": "ITAOI",
    "pods": "ITAOI,ITGOA,ITSPE,..."
  }
}
```

### `source/ocean_freight.xlsx`
Ocean freight rates from Busan to various PODs:
- Columns: POD, Currency, 20 FT, 40 FT
- Updated manually with current market rates

---

## Troubleshooting

### HAPAG Authentication Issues
- Verify credentials in `.env` file
- Check HAPAG-Lloyd website is accessible
- Ensure Playwright browsers are installed: `playwright install chromium`

### API not loading HAPAG data
- Run `python hapag_extractor.py` to generate data file
- Check that `hapag_surcharges_*.xlsx` exists in `downloads/`
- Verify API endpoint: `http://localhost:5000/api/hapag/destinations`

### Sub-options not appearing in HAPAG view
- Data must be in raw format (not preprocessed)
- Sub-options are detected when Curr. column is empty
- Check that landfreight rows have proper sub-option structure

### Container type mismatch between carriers
- ONE uses: 20 FT, 40 FT, 40 FT High Cube
- HAPAG uses: 20STD, 40STD, 40HC
- Summary dashboard auto-converts between formats

### City name not matching in Summary view
- City normalization removes hyphens and special characters
- Check exact spelling in both data sources
- Matching is case-insensitive

### Browser opens twice
- Ensure `BROWSER=none` is set in `start.bat` before npm start
- Check `package.json` uses standard `react-scripts start` (no FAST_REFRESH)

### Duplicate ranks (e.g., 1,2,2,3)
- Fixed in `ONE_processor.py` using `method='dense'` for ranking
- Reprocess data to get sequential ranks (1,2,3,4)

### API not loading data
- Check that processed Excel file exists in `downloads/`
- Verify file name matches pattern: `ONE_Inland_Rate_Processed_*.xlsx`
- Run health check: `http://localhost:5000/api/health`

### Frontend build errors
- Ensure TypeScript types are installed: `npm install @types/react @types/react-dom`
- Check `tsconfig.json` has `"incremental": true` for faster builds

### Maps not loading
- Embedded maps use public Google Maps URL (no API key needed)
- If embed is blocked, use "View in Google Maps" button
- Check browser console for CORS or iframe errors

---

## Tips

- **Multi-Carrier Comparison:** Use Summary dashboard to compare ONE vs HAPAG rates side-by-side
- **Sub-Options Selection:** HAPAG dashboard allows choosing between Combined Rail and Between transport modes
- **Unified Container Selector:** Summary view synchronizes container types across both carriers automatically
- **City Name Matching:** Handles variations like "ARQUES-LA-BATAILLE" vs "ARQUES LA BATAILLE"
- **Faster Startup:** First run is slower; subsequent starts benefit from incremental compilation
- **Server Logs:** Minimized windows remain in taskbar - click to view logs if needed
- **Data Refresh:** Rerun extraction and processing scripts, then restart API server
- **Multiple Container Types:** Switch between container sizes in all dashboard views
- **Transport Mode Column:** Extracted from Remarks column (text before semicolon) for ONE data
- **Remarks Column:** Toggle tab to see additional route information in ONE view

---

## Notes

- Internet connection required for scraping and maps
- Chrome/Chromium browser launches automatically during data collection (don't close it)
- Processing time: ~30 seconds per destination (ONE), ~1 minute per destination (HAPAG)
- Map routes are for visualization purposes only
- PODs with unavailable freight costs show estimation notes (marked with *)
- HAPAG data preserves sub-options structure (Combined Rail, Between modes)
- City name matching handles hyphens and special characters automatically
- Container type conversion between carriers is automatic in Summary view

---

## Key Features Summary

### Multi-Carrier Support
- **ONE Line:** Processed inland rates with ocean freight integration
- **HAPAG-Lloyd:** Raw surcharge data with landfreight sub-options

### Intelligent Data Processing
- **Transport Mode Extraction:** Automatically parsed from Remarks column
- **City Name Normalization:** Handles variations and special characters
- **Container Type Synchronization:** Auto-converts between carrier formats
- **Sub-Options Preservation:** HAPAG data maintains alternative transport modes

### Professional UI
- **Three Dashboard Views:** Dedicated views for each carrier plus comparison
- **Unified Selectors:** Single container dropdown updates all views
- **Side-by-Side Comparison:** Direct rate comparison in Summary view
- **Sub-Option Selection:** Dropdown for HAPAG alternative transport modes
- **Google Maps Integration:** Embedded route visualization

---

## Regular Workflow

### Weekly Data Update
1. Run scrapers for both carriers:
   ```bash
   python quick_download_refactored.py  # ONE Line
   python hapag_extractor.py            # HAPAG-Lloyd
   ```
2. Process ONE data: `python ONE_processor.py`
3. Restart servers or use `start.bat`

### Dashboard Usage
1. Launch: `start.bat`
2. **ONE Dashboard:** View ONE Line rates with top 3 routes and map comparison
3. **HAPAG Dashboard:** View HAPAG-Lloyd surcharges with sub-option selection
4. **Summary Dashboard:** Compare both carriers side-by-side
5. Select destination and container type in any view
6. Compare rates, transport modes, and route options

---

## Support

For technical issues:
- Check server logs in minimized windows
- Verify data files in `downloads/` folder
- Review browser console for frontend errors
- Ensure all dependencies are installed
