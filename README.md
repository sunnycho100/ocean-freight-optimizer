# Freight Route Optimizer

A comprehensive freight route analysis and visualization system for inland transportation from one destination through various PODs (Ports of Discharge) to European destinations.

## Quick Start

### One-Click Launch (Windows)
```bash
start.bat
```
This will:
- Start the Flask API server (port 5000)
- Start the React frontend (port 3000)
- Automatically open your browser to the dashboard

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

### 2. **Data Processing** (`ONE_processor.py`)
Combines inland rates with ocean freight costs and calculates total rates with proper ranking.

**Usage:**
```bash
python ONE_processor.py
```

**Features:**
- Merges inland rates with ocean freight costs from `source/ocean_freight.xlsx`
- Calculates total rates (inland + ocean)
- Ranks routes by cost for each destination-container combination using `dense` ranking (1,2,3,4... no gaps)
- Removes validation columns for clean output

**Output:**
- `downloads/ONE_Inland_Rate_Processed_YYYYMMDD_HHMMSS.xlsx` - Processed data with rankings

---

### 3. **Backend API** (`api_server.py`)
Flask REST API that serves processed data to the frontend.

**Endpoints:**
- `GET /api/destinations` - List of all destinations
- `GET /api/container-types` - List of container types
- `GET /api/routes/<destination>/<container_type>` - Ranked routes for specific criteria
- `GET /api/health` - Health check endpoint

**Auto-starts on:** `http://localhost:5000`

---

### 4. **Frontend Dashboard** (`freight-ui/`)
React/TypeScript web application for visualizing routes and comparing options.

**Features:**
- Smart Filters: Select destination and container type
- Top 3 Routes Table: Best routes ranked by total cost
- Map Comparison Grid: Side-by-side embedded Google Maps for top 3 routes
- Tab Switcher: Toggle between Transport Mode and Remarks columns
- Estimation Notes: Footnotes for ports with unavailable freight costs
- Worst Route Display: Highest cost option for comparison

**Technology Stack:**
- React 18 with TypeScript
- CSS custom properties for theming
- Google Maps iframe embed (no API key required)
- Incremental TypeScript compilation for faster builds

**Auto-starts on:** `http://localhost:3000`

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Chrome browser (for data scraping)
- Windows OS (for `start.bat` automation)

### Initial Setup

1. **Install Python dependencies:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install frontend dependencies:**
```bash
cd freight-ui
npm install
cd ..
```

3. **Prepare data files:**
   - Place ocean freight rates in `source/ocean_freight.xlsx`
   - Configure destinations in `destinations.txt`
   - Run data collection and processing

---

## Detailed Workflow

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
python quick_download_refactored.py
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
├── api_server.py                    # Flask REST API
├── ONE_processor.py                 # Data processing pipeline
├── quick_download_refactored.py     # Main data collection script
├── url_checker_refactored.py        # Destination config extractor
├── destinations.txt                 # Target destinations list
├── destination_configs.json         # Location codes & POD mappings
├── downloads/                       # Scraped & processed data
├── source/
│   └── ocean_freight.xlsx          # Ocean freight rates
├── quick_download_package/          # Modular scraper components
│   ├── browser_manager.py
│   ├── config_loader.py
│   ├── ONE_processor.py
│   ├── destination_processor.py
│   ├── excel_manager.py
│   ├── table_scraper.py
│   └── __init__.py
├── url_checker_package/             # Modular URL checker components
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
    │   │   ├── RouteDashboard.tsx
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

- Faster Startup: First run is slower; subsequent starts benefit from incremental compilation
- Server Logs: Minimized windows remain in taskbar - click to view logs if needed
- Data Refresh: Rerun `ONE_processor.py` after new scrapes, then restart API server
- Multiple Container Types: Switch between 20 FT, 40 FT, 40 FT High Cube in the dashboard
- Remarks Column: Toggle tab to see additional route information

---

## Notes

- Internet connection required for scraping and maps
- Chrome browser launches automatically during data collection (don't close it)
- Processing time: ~30 seconds per destination
- Map routes are for visualization purposes only
- PODs with unavailable freight costs show estimation notes (marked with *)

---

## Regular Workflow

### Weekly Data Update
1. Run scraper: `python quick_download_refactored.py`
2. Process data: `python ONE_processor.py`
3. Restart servers or use `start.bat`

### Dashboard Usage
1. Launch: `start.bat`
2. Select destination and container type
3. Review top 3 recommended routes
4. Compare routes on map grid
5. Check worst route for reference

---

## Support

For technical issues:
- Check server logs in minimized windows
- Verify data files in `downloads/` folder
- Review browser console for frontend errors
- Ensure all dependencies are installed
