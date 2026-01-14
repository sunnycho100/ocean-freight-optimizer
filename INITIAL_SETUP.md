# Initial Setup Guide - Freight Route Optimizer

This guide will help you set up the complete project on a new computer from scratch.

## Prerequisites

Before starting, you need to install the following software:

### 1. Python (3.10 or higher)
Download and install from: https://www.python.org/downloads/

**Important during installation:**
- ✅ Check "Add Python to PATH"
- ✅ Check "Install pip"

Verify installation:
```powershell
python --version
pip --version
```

### 2. Node.js (18.x or higher)
Download and install from: https://nodejs.org/

Verify installation:
```powershell
node --version
npm --version
```

### 3. Git (Optional but recommended)
Download and install from: https://git-scm.com/downloads

---

## Project Setup

### Step 1: Clone/Download the Project

If you have Git:
```powershell
cd C:\Users\<YourUsername>\Desktop
git clone <your-repo-url> automation
cd automation
```

Or simply extract the project folder to your desired location.

### Step 2: Python Environment Setup

Navigate to the project directory:
```powershell
cd C:\Users\<YourUsername>\Desktop\automation
```

#### Create Virtual Environment
```powershell
python -m venv .venv
```

#### Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

**Note:** If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Install Python Dependencies
```powershell
pip install pandas openpyxl playwright playwright-stealth python-dotenv flask flask-cors requests selenium
```

#### Install Playwright Browsers
```powershell
playwright install chromium
```

This will download the Chromium browser needed for automation (~200MB).

### Step 3: Frontend Setup (React)

Navigate to the frontend directory:
```powershell
cd freight-ui
```

#### Install Node Dependencies
```powershell
npm install
```

This will install React and all required packages.

#### Return to Project Root
```powershell
cd ..
```

---

## Configuration Files

### 1. Create Environment File (for HAPAG credentials)

Create a file named `.env` in the project root:
```powershell
New-Item -Path ".env" -ItemType File
```

Edit `.env` and add:
```
HAPAG_USERNAME=your_username_here
HAPAG_PASSWORD=your_password_here
```

### 2. Verify Required Files Exist

Make sure these files exist in the project:
- `destinations.txt` - List of destination cities
- `destination_configs.json` - Configuration for destinations
- `source/ocean_freight.xlsx` - Ocean freight rates

---

## Running the Application

### Backend: API Server

Open a terminal in the project root:
```powershell
cd C:\Users\<YourUsername>\Desktop\automation
.\.venv\Scripts\Activate.ps1
python api_server.py
```

The API will start on: http://localhost:5000

### Frontend: React App

Open a **new** terminal window:
```powershell
cd C:\Users\<YourUsername>\Desktop\automation\freight-ui
npm start
```

The React app will open automatically at: http://localhost:3001

---

## Data Extraction Scripts

These scripts fetch fresh data. Run them in the project root with virtual environment activated:

### Extract ONE Inland Rates
```powershell
.\.venv\Scripts\Activate.ps1
python quick_download_refactored.py
```

This will:
- Open browser and navigate to ONE website
- Extract inland rates for all destinations
- Save to `downloads/ONE_Inland_Rate_YYYYMMDD.xlsx`

### Process ONE Data
```powershell
python ONE_processor.py
```

This will:
- Load the raw ONE data
- Merge with ocean freight rates
- Calculate total rates and rankings
- Save to `downloads/ONE_Inland_Rate_Processed_YYYYMMDD_HHMMSS.xlsx`

### Extract HAPAG Surcharges
```powershell
python hapag_extractor.py
```

**Note:** Requires `.env` file with HAPAG credentials

This will:
- Login to HAPAG-Lloyd
- Extract surcharges for all destinations
- Save to `downloads/hapag_surcharges_YYYYMMDD.xlsx`

---

## Full Dependency List

### Python Packages
```
pandas>=2.0.0
openpyxl>=3.1.0
playwright>=1.40.0
playwright-stealth>=1.0.0
python-dotenv>=1.0.0
flask>=3.0.0
flask-cors>=4.0.0
requests>=2.31.0
selenium>=4.15.0
```

### Node Packages (installed via npm)
```
react@^18.2.0
react-dom@^18.2.0
react-scripts@5.0.1
typescript@^4.9.5
@types/react@^19.2.7
@types/react-dom@^19.2.3
```

---

## Directory Structure

```
automation/
├── .venv/                          # Python virtual environment
├── .env                            # HAPAG credentials (create this)
├── api_server.py                   # Flask API server
├── ONE_processor.py                # ONE data processor
├── hapag_extractor.py              # HAPAG data extractor
├── quick_download_refactored.py    # ONE data extractor
├── destinations.txt                # List of destinations
├── destination_configs.json        # Destination configurations
├── downloads/                      # Downloaded & processed data
│   ├── ONE_Inland_Rate_*.xlsx
│   ├── ONE_Inland_Rate_Processed_*.xlsx
│   └── hapag_surcharges_*.xlsx
├── source/
│   └── ocean_freight.xlsx         # Ocean freight rates
├── freight-ui/                     # React frontend
│   ├── node_modules/              # Node dependencies
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── OneDashboard.tsx
│       │   ├── HapagDashboard.tsx
│       │   └── SummaryDashboard.tsx
│       └── App.tsx
└── [other Python packages and helpers]
```

---

## Troubleshooting

### Python virtual environment not activating
**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Playwright browser not found
**Error:** "Executable doesn't exist at ..."

**Solution:**
```powershell
.\.venv\Scripts\Activate.ps1
playwright install chromium
```

### React app won't start
**Error:** "npm not found" or package errors

**Solution:**
```powershell
cd freight-ui
rm -r node_modules
npm install
```

### API can't find Excel files
**Error:** "No data file found"

**Solution:**
Run the data extraction scripts first:
```powershell
python quick_download_refactored.py
python ONE_processor.py
python hapag_extractor.py
```

### Port already in use
**Error:** "Address already in use" on port 5000 or 3001

**Solution:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000
# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

---

## Quick Start Commands (Summary)

After initial setup, use these commands to run the application:

### Terminal 1 - Backend API
```powershell
cd C:\Users\<YourUsername>\Desktop\automation
.\.venv\Scripts\Activate.ps1
python api_server.py
```

### Terminal 2 - Frontend
```powershell
cd C:\Users\<YourUsername>\Desktop\automation\freight-ui
npm start
```

### Extract Fresh Data (when needed)
```powershell
cd C:\Users\<YourUsername>\Desktop\automation
.\.venv\Scripts\Activate.ps1

# Get ONE data
python quick_download_refactored.py
python ONE_processor.py

# Get HAPAG data
python hapag_extractor.py
```

---

## Tech Stack Summary

- **Backend:** Python 3.10+, Flask
- **Frontend:** React 18, TypeScript
- **Browser Automation:** Playwright (Chromium)
- **Data Processing:** Pandas, OpenPyXL
- **Web Scraping:** Selenium (for ONE), Playwright (for HAPAG)

---

**Setup Time:** Approximately 15-30 minutes depending on internet speed

**First Time Setup Only:** Yes, once configured you only need to run the Quick Start commands

**Support:** Check error logs in terminal for detailed error messages
