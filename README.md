# Freight Route Optimizer

A multi-carrier freight route analysis and visualization system that compares inland transportation rates from **ONE Line** and **HAPAG-Lloyd** through various PODs (Ports of Discharge) to European destinations. It automates data collection, processing, and presents results in an interactive React dashboard.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Setup & Installation](#setup--installation)
- [System Architecture](#system-architecture)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)
- [Documentation](#documentation)

---

## Quick Start

### macOS / Linux
```bash
./start.sh
```

### Windows
```bash
start.bat
```

Both scripts will:
1. Start the Flask API server (dynamic port starting from 4000 on macOS/Linux, port 5000 on Windows)
2. Start the React frontend (port 3000)
3. Open your browser to the multi-carrier dashboard

---

## Features

### Multi-Carrier Support
- **ONE Line** — Processed inland rates with ocean freight integration
- **HAPAG-Lloyd** — Surcharge data with landfreight sub-options (Combined Rail, Between modes)

### Three Dashboard Views
| View | Description |
|------|-------------|
| **ONE Dashboard** | Top-ranked routes by total cost, map comparison grid, transport mode & remarks |
| **HAPAG Dashboard** | Landfreight surcharges with sub-option selector, container type filtering |
| **Summary** | Side-by-side carrier comparison with unified container types and city name normalization |
| **Chat Assistant** | Natural-language Q&A panel powered by OpenAI / Gemini with fuzzy destination matching |

### AI Chatbot Assistant
- Natural-language Q&A over freight rate data (e.g., "What's the cheapest route to Valence for a 40HC?")
- RAG-style context injection — Python does precise data lookups, LLM formats the answer
- Fuzzy destination matching (handles typos, partial names, hyphenated variants)
- Supports multi-turn conversation with history
- Powered by OpenAI / Gemini API (configurable)

### Internationalization
- English and Korean language support (toggle in the UI)

### Intelligent Data Processing
- Automatic transport mode extraction from Remarks column
- City name normalization (e.g., `ARQUES-LA-BATAILLE` ↔ `ARQUES LA BATAILLE`)
- Container type synchronization across carriers (e.g., `20 FT` ↔ `20STD`)
- Dense ranking (1, 2, 3, 4 — no gaps) for route cost comparison

### Google Maps Integration
- Embedded iframe maps (no API key required)
- Grid view with 3 maps for top routes comparison
- Fallback "View in Google Maps" button if embed is blocked

---

## Setup & Installation

> For detailed step-by-step instructions on a fresh machine, see [INITIAL_SETUP.md](INITIAL_SETUP.md).

### Prerequisites

- Python 3.10+
- Node.js 18+
- Chrome / Chromium browser (for data scraping)
- HAPAG-Lloyd account credentials (for HAPAG data extraction)

### 1. Python Environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install pandas openpyxl playwright playwright-stealth python-dotenv flask flask-cors requests selenium openai google-generativeai
playwright install chromium
```

### 2. Frontend Dependencies

```bash
cd freight-ui && npm install && cd ..
```

### 3. Environment Variables

Create a `.env` file in the project root:

```
HAPAG_EMAIL=your_email@example.com
HAPAG_PASSWORD=your_password_here

# Chatbot (pick one provider)
LLM_PROVIDER=openai              # or "gemini"
OPENAI_API_KEY=sk-...            # if using OpenAI
GEMINI_API_KEY=...               # if using Gemini
```

### 4. Data Files

- Place ocean freight rates in `source/ocean_freight.xlsx` (columns: POD, Currency, 20 FT, 40 FT)
- Configure target destinations in `destinations.txt` (one per line)

---

## System Architecture

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  Data Collection                                                │
 │  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
 │  │ quick_download_refactored│  │ hapag_checker.py             │ │
 │  │ .py (Selenium)           │  │ + hapag_module/ (Playwright) │ │
 │  │ ONE Line inland rates    │  │ HAPAG-Lloyd surcharges       │ │
 │  └────────────┬─────────────┘  └──────────────┬───────────────┘ │
 │               ▼                               ▼                 │
 │  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
 │  │ ONE_processor.py         │  │ downloads/                   │ │
 │  │ Merge ocean freight,     │  │ hapag_surcharges_*.xlsx      │ │
 │  │ rank routes              │  │                              │ │
 │  └────────────┬─────────────┘  └──────────────┬───────────────┘ │
 │               ▼                               ▼                 │
 │            downloads/ONE_Inland_Rate_Processed_*.xlsx           │
 └─────────────────────────┬───────────────────────────────────────┘
                           ▼
              ┌─────────────────────────┐
              │ api_server.py (Flask)   │
              │ REST API + data caching │
              └────────────┬────────────┘
                           ▼
              ┌─────────────────────────┐
              │ freight-ui/ (React/TS)  │
              │ ONE | HAPAG | Summary   │
              └─────────────────────────┘
```

### Backend API (`api_server.py`)

Flask REST API that serves processed data to the frontend.

| Endpoint | Description |
|----------|-------------|
| `GET /api/destinations` | List all ONE Line destinations |
| `GET /api/container-types` | List container types |
| `GET /api/routes/<dest>/<type>` | Ranked ONE routes |
| `GET /api/hapag/destinations` | List HAPAG destinations |
| `GET /api/hapag/route/<dest>/<type>` | HAPAG rates with sub-options |
| `GET /api/health` | Health check |
| `POST /api/chat` | AI chatbot — natural-language freight Q&A |

- Auto-detects the latest data files in `downloads/`
- Caches data in memory for fast responses
- Port: dynamic from 4000 (macOS/Linux) or 5000 (Windows), written to `.api_port`

### Frontend (`freight-ui/`)

- React 18 + TypeScript
- Components: `RouteDashboard`, `HapagDashboard`, `SummaryDashboard`, `ChatPanel`
- English / Korean language toggle (`i18n.tsx`)
- CSS custom properties for theming
- Reads API port from `REACT_APP_API_PORT` env var (falls back to `localhost:4000`)

---

## Usage

### Data Collection & Processing

```bash
# 1. Collect ONE Line inland rates
python quick_download_refactored.py
#    → downloads/ONE_Inland_Rate_YYYYMMDD.xlsx

# 2. Process ONE data (merge ocean freight, rank routes)
python ONE_processor.py
#    → downloads/ONE_Inland_Rate_Processed_YYYYMMDD_HHMMSS.xlsx

# 3. Extract HAPAG-Lloyd surcharges (requires .env credentials)
python hapag_checker.py
#    → downloads/hapag_surcharges_YYYYMMDD.xlsx
```

### Adding New Destinations

```bash
# 1. Extract location codes and POD mappings
python url_checker_refactored.py "ROTTERDAM, NETHERLANDS"
#    → updates destination_configs.json

# 2. Add the destination to destinations.txt
echo "ROTTERDAM, NETHERLANDS" >> destinations.txt

# 3. Collect and process data
python quick_download_refactored.py   # ONE Line
python hapag_checker.py               # HAPAG-Lloyd
python ONE_processor.py               # Process ONE data

# 4. Launch dashboard
./start.sh   # or start.bat on Windows
```

### Weekly Data Refresh

1. Run both scrapers: `quick_download_refactored.py` and `hapag_checker.py`
2. Process ONE data: `python ONE_processor.py`
3. Restart the servers (or re-run the start script)

---

## Configuration

### `destinations.txt`

One destination per line:

```
VALENCE, DROME, FRANCE
LEUTKIRCH IM ALLGAEU, BW, GERMANY
MUENSTER, NW, GERMANY
```

### `destination_configs.json`

Auto-generated by `url_checker_refactored.py`. Maps each destination to its location code and available PODs:

```json
{
  "ANCONA, ITALY": {
    "locationCode": "ITAOI",
    "pods": "ITAOI,ITGOA,ITSPE,..."
  }
}
```

### `source/ocean_freight.xlsx`

Ocean freight rates from Busan to various PODs. Columns: `POD`, `Currency`, `20 FT`, `40 FT`. Update manually with current market rates.

### `.env`

```
HAPAG_EMAIL=your_email@example.com
HAPAG_PASSWORD=your_password_here
LLM_PROVIDER=openai              # or "gemini"
OPENAI_API_KEY=sk-...            # if using OpenAI
GEMINI_API_KEY=...               # if using Gemini
```

---

## Project Structure

```
ocean-freight-optimizer/
├── start.sh                         # Launcher (macOS/Linux)
├── start.bat                        # Launcher (Windows)
├── api_server.py                    # Flask REST API
├── .api_port                        # Dynamic API port (auto-generated)
├── ONE_processor.py                 # ONE data processing pipeline
├── hapag_checker.py                 # HAPAG data extraction entry point
├── quick_download_refactored.py     # ONE data collection (Selenium)
├── url_checker_refactored.py        # Destination config extractor
├── debug_extraction.py              # HAPAG table extraction debugger
├── destinations.txt                 # Target destinations list
├── destination_configs.json         # Location codes & POD mappings
├── .env                             # HAPAG credentials (create manually)
│
├── hapag_module/                    # HAPAG extraction package
│   ├── auth_manager.py              #   Login & authentication
│   ├── browser_manager.py           #   Playwright browser lifecycle
│   ├── config_loader.py             #   Configuration loading
│   ├── data_extractor.py            #   Table data extraction
│   ├── excel_exporter.py            #   Excel output
│   ├── main_runner.py               #   Orchestrator
│   └── quote_scraper.py             #   Quote search & port selection
│
├── quick_download_package/          # ONE scraper package
│   ├── browser_manager.py           #   Selenium browser lifecycle
│   ├── config_loader.py             #   Configuration loading
│   ├── data_processor.py            #   Data transformation
│   ├── destination_processor.py     #   Per-destination processing
│   ├── excel_manager.py             #   Excel output
│   └── table_scraper.py             #   Table data extraction
│
├── chatbot/                         # AI chatbot package
│   ├── data_loader.py               #   Load & cache freight DataFrames
│   ├── context_builder.py           #   Intent detection & context assembly
│   └── llm_client.py                #   LLM API client (OpenAI / Gemini)
│
├── url_checker_package/             # Destination config extractor package
│   ├── browser.py
│   ├── config.py
│   ├── config_manager.py
│   ├── destination_selector.py
│   ├── error_summary.py
│   ├── form_handler.py
│   ├── processor.py
│   └── url_extractor.py
│
├── downloads/                       # Scraped & processed data output
│   ├── ONE_Inland_Rate_*.xlsx
│   ├── ONE_Inland_Rate_Processed_*.xlsx
│   └── hapag_surcharges_*.xlsx
│
├── source/
│   └── ocean_freight.xlsx           # Ocean freight rates (manual)
│
├── freight-ui/                      # React frontend
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── App.tsx                   # Main app with tab navigation
│       ├── config.ts                 # API URL configuration
│       ├── types.ts                  # TypeScript type definitions
│       ├── components/
│       │   ├── RouteDashboard.tsx    # ONE Line dashboard
│       │   ├── HapagDashboard.tsx    # HAPAG-Lloyd dashboard
│       │   ├── SummaryDashboard.tsx  # Carrier comparison view
│       │   ├── ChatPanel.tsx         # AI chatbot panel
│       │   ├── RouteTable.tsx        # Route data table
│       │   ├── RouteTableTabs.tsx    # Tabbed table view
│       │   ├── RouteMap.tsx          # Google Maps embed
│       │   └── FiltersPanel.tsx      # Destination & container filters
│       ├── styles/
│       │   ├── app.css
│       │   ├── global.css
│       │   └── hapag-dashboard.css
│       └── utils/
│           └── googleMapsHelper.ts
│
├── chatbot.md                       # Chatbot architecture & implementation plan
├── dataflow.md                      # Full data pipeline & file schema reference
│
└── docs/                            # Documentation
    └── QUICK_DOWNLOAD_*.md          # Quick download package docs
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **HAPAG authentication fails** | Verify `HAPAG_EMAIL` and `HAPAG_PASSWORD` in `.env`. Ensure Playwright browsers are installed: `playwright install chromium` |
| **API not loading HAPAG data** | Run `python hapag_checker.py` to generate data. Check `hapag_surcharges_*.xlsx` exists in `downloads/` |
| **API not loading ONE data** | Verify `ONE_Inland_Rate_Processed_*.xlsx` exists in `downloads/`. Run health check at `/api/health` |
| **Sub-options not showing** | Data must be in raw format. Sub-options are detected when the `Curr.` column is empty |
| **Container type mismatch** | ONE uses `20 FT / 40 FT / 40 FT High Cube`; HAPAG uses `20STD / 40STD / 40HC`. The Summary dashboard auto-converts |
| **City name not matching** | Normalization removes hyphens and special characters. Matching is case-insensitive |
| **Duplicate ranks (1,2,2,3)** | Reprocess data with `python ONE_processor.py` — uses dense ranking method |
| **Frontend build errors** | Run `npm install` in `freight-ui/`. Check that `tsconfig.json` has `"incremental": true` |
| **Maps not loading** | Uses public Google Maps embed (no API key). Check browser console for CORS/iframe errors |
| **Browser opens twice** | Ensure `BROWSER=none` is set in the start script before `npm start` |

---

## Documentation

| Document | Description |
|----------|-------------|
| [chatbot.md](chatbot.md) | Chatbot architecture, RAG approach, fuzzy matching strategy, and implementation plan |
| [dataflow.md](dataflow.md) | Full data pipeline diagram, file-by-file reference, and column schemas |
| [INITIAL_SETUP.md](INITIAL_SETUP.md) | Step-by-step setup guide for a fresh machine |
| [docs/](docs/) | Quick download package architecture & refactoring docs |

---

## Notes

- Internet connection required for data scraping and map display
- Chrome/Chromium launches automatically during scraping — don't close it
- Typical processing time: ~30s per destination (ONE), ~1 min per destination (HAPAG)
- Map routes are for visualization only
- PODs with unavailable freight costs show estimation notes (marked with `*`)
- First launch is slower; subsequent starts benefit from incremental TypeScript compilation
