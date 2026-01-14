"""
Flask API server to serve processed Excel data to the React frontend.
"""
import os
import glob
from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Cache for loaded data to avoid re-reading Excel files on every request
_data_cache = {'one': None, 'hapag': None, 'one_file': None, 'hapag_file': None}

def get_latest_processed_file():
    """Get the most recently processed Excel file."""
    pattern = 'downloads/ONE_Inland_Rate_Processed_*.xlsx'
    files = glob.glob(pattern)
    # Filter out temp files
    files = [f for f in files if not os.path.basename(f).startswith('~$')]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def get_latest_hapag_file():
    """Get the most recently modified HAPAG surcharges file (raw format)."""
    # Look for raw HAPAG files
    pattern1 = 'downloads/hapag_surcharges.xlsx'
    pattern2 = 'downloads/hapag_surcharges_*.xlsx'
    
    files = glob.glob(pattern1) + glob.glob(pattern2)
    # Filter out temp files
    files = [f for f in files if not os.path.basename(f).startswith('~$')]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def load_data():
    """Load the processed Excel data with caching."""
    file_path = get_latest_processed_file()
    if not file_path:
        return None
    
    # Check if we already have this file cached
    if _data_cache['one_file'] == file_path and _data_cache['one'] is not None:
        return _data_cache['one']
    
    # Load and cache the data
    print(f"Loading ONE data from: {file_path}")
    df = pd.read_excel(file_path)
    _data_cache['one'] = df
    _data_cache['one_file'] = file_path
    return df

def load_hapag_data():
    """Load the raw HAPAG surcharges Excel data with caching."""
    file_path = get_latest_hapag_file()
    if not file_path:
        return None
    
    # Check if we already have this file cached
    if _data_cache['hapag_file'] == file_path and _data_cache['hapag'] is not None:
        return _data_cache['hapag']
    
    # Load and cache the data
    print(f"Loading HAPAG data from: {file_path}")
    # Read raw format with skiprows=4
    df = pd.read_excel(file_path, header=None, skiprows=4)
    # Set column names manually
    df.columns = ['From', 'To', 'Via', 'Description', 'Curr.', '20STD', '40STD', '40HC', 'Transport Remarks']
    _data_cache['hapag'] = df
    _data_cache['hapag_file'] = file_path
    return df

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    """Get list of unique destinations."""
    df = load_data()
    if df is None:
        return jsonify({'error': 'No data file found'}), 404
    destinations = sorted(df['Destination'].unique().tolist())
    return jsonify(destinations)

@app.route('/api/container-types', methods=['GET'])
def get_container_types():
    """Get list of unique container types."""
    df = load_data()
    if df is None:
        return jsonify({'error': 'No data file found'}), 404
    container_types = sorted(df['Container Type & Size'].unique().tolist())
    return jsonify(container_types)

@app.route('/api/routes/<destination>/<container_type>', methods=['GET'])

def get_routes(destination, container_type):
    """Get ranked routes for a specific destination and container type."""
    df = load_data()
    if df is None:
        return jsonify({'error': 'No data file found'}), 404
    
    # Filter by destination and container type
    filtered = df[
        (df['Destination'] == destination) & 
        (df['Container Type & Size'] == container_type)
    ].copy()
    
    if filtered.empty:
        return jsonify({'error': 'No routes found for criteria'}), 404
    
    # Sort by Total Rate (primary) to ensure correct order, then by Cost Rank (secondary)
    filtered = filtered.sort_values(['Total Rate', 'Cost Rank'], ascending=[True, True])
    
    # Get currency (should be the same for all routes in a lane)
    currency = filtered['Currency'].iloc[0]
    
    # Get the best (lowest cost) route for each rank
    # This ensures we show exactly one route per rank, with no duplicates
    best_per_rank = filtered.sort_values('Total Rate').drop_duplicates(subset=['Cost Rank'], keep='first')
    best_per_rank = best_per_rank.sort_values('Cost Rank')
    
    # Build routes list
    routes = []
    for _, row in best_per_rank.iterrows():
        routes.append({
            'rank': int(row['Cost Rank']),
            'pod': row['POD'],
            'mode': row['Transport Mode'],
            'remarks': row['Remarks'] if 'Remarks' in row and pd.notna(row['Remarks']) else '',
            'totalRate': float(row['Total Rate']),
            'oceanRate': float(row['Ocean Rate']),
            'inlandRate': float(row['Rate']),
        })
    
    return jsonify({
        'destination': destination,
        'containerType': container_type,
        'currency': currency,
        'routes': routes,
        'totalRoutes': len(routes)
    })

@app.route('/api/hapag/destinations', methods=['GET'])
def get_hapag_destinations():
    """Get list of unique destinations from HAPAG data."""
    df = load_hapag_data()
    if df is None:
        return jsonify({'error': 'No HAPAG data file found'}), 404
    destinations = sorted(df['To'].unique().tolist())
    return jsonify(destinations)

@app.route('/api/hapag/route/<path:destination>', methods=['GET'])
def get_hapag_route(destination):
    """Get route and charges for a specific HAPAG destination (serving raw structure with sub-options)."""
    df = load_hapag_data()
    if df is None:
        return jsonify({'error': 'No HAPAG data file found'}), 404
    
    print(f"HAPAG file: {get_latest_hapag_file()}")
    
    # Preload data into cache for faster first request
    print("Preloading data into cache...")
    load_data()
    load_hapag_data()
    print("Data preloaded successfully!")
    
    # Filter by destination
    filtered = df[df['To'] == destination].copy()
    
    if filtered.empty:
        return jsonify({'error': 'No routes found for destination'}), 404
    
    # Get route info (should be same for all rows)
    first_row = filtered.iloc[0]
    route_from = first_row['From']
    route_to = first_row['To']
    route_via = first_row['Via'] if pd.notna(first_row['Via']) and first_row['Via'] != '' else ''
    
    # Determine available containers (convert to Python bool for JSON serialization)
    available_containers = {
        '20STD': bool(not filtered['20STD'].isna().all() and (filtered['20STD'] != '').any() and (filtered['20STD'] != '-').any()),
        '40STD': bool(not filtered['40STD'].isna().all() and (filtered['40STD'] != '').any() and (filtered['40STD'] != '-').any()),
        '40HC': bool(not filtered['40HC'].isna().all() and (filtered['40HC'] != '').any() and (filtered['40HC'] != '-').any()),
    }
    
    # Process charges
    ocean_freight = None
    destination_landfreight = None
    other_charges = []
    
    # Track rows for sub-options
    i = 0
    while i < len(filtered):
        row = filtered.iloc[i]
        desc = str(row['Description'])
        curr = str(row['Curr.']) if pd.notna(row['Curr.']) and row['Curr.'] != '' else ''
        
        # Check if this is Ocean Freight
        if 'ocean freight' in desc.lower():
            ocean_freight = {
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) and row['20STD'] != '' else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) and row['40STD'] != '' else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) and row['40HC'] != '' else '',
            }
            i += 1
            continue
        
        # Check if this is Destination Landfreight (has sub-options when Curr. is empty)
        if 'destination landfreight' in desc.lower() or 'landfreight' in desc.lower():
            landfreight_item = {
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) and row['20STD'] != '' else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) and row['40STD'] != '' else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) and row['40HC'] != '' else '',
            }
            
            # Check if empty curr (signals sub-options exist below)
            if curr == '' or pd.isna(row['Curr.']):
                sub_options = []
                i += 1
                
                # Look for sub-option rows (usually start with "Combined", "Between", etc.)
                # Continue while we find rows with currency values (sub-options)
                while i < len(filtered):
                    next_row = filtered.iloc[i]
                    next_desc = str(next_row['Description'])
                    next_curr = str(next_row['Curr.']) if pd.notna(next_row['Curr.']) and next_row['Curr.'] != '' else ''
                    
                    # If we hit another main category (empty curr or different pattern), stop
                    if next_curr == '' or pd.isna(next_row['Curr.']):
                        break
                    
                    # Check if it looks like a sub-option (starts with Combined, Between, etc.)
                    first_word = next_desc.split()[0].lower() if next_desc.split() else ''
                    if first_word in ['combined', 'between', 'from', '<', '>'] or ';' in next_desc:
                        sub_options.append({
                            'description': next_desc,
                            'value20': str(next_row['20STD']) if pd.notna(next_row['20STD']) and next_row['20STD'] != '' else '-',
                            'value40': str(next_row['40STD']) if pd.notna(next_row['40STD']) and next_row['40STD'] != '' else '-',
                            'value40HC': str(next_row['40HC']) if pd.notna(next_row['40HC']) and next_row['40HC'] != '' else '-',
                        })
                        i += 1
                    else:
                        break
                
                if sub_options:
                    landfreight_item['subOptions'] = sub_options
                    # Set currency from first sub-option
                    if i > 0 and i <= len(filtered):
                        prev_row = filtered.iloc[i-1]
                        if pd.notna(prev_row['Curr.']) and prev_row['Curr.'] != '':
                            landfreight_item['curr'] = str(prev_row['Curr.'])
            else:
                i += 1
            
            destination_landfreight = landfreight_item
            continue
        
        # Other charges (skip rows with empty currency as they're usually category headers)
        if curr != '' and not pd.isna(row['Curr.']):
            other_charges.append({
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) and row['20STD'] != '' else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) and row['40STD'] != '' else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) and row['40HC'] != '' else '',
            })
        
        i += 1
    
    return jsonify({
        'destination': destination,
        'route': {
            'from': route_from,
            'to': route_to,
            'via': route_via,
            'oceanFreight': ocean_freight,
            'destinationLandfreight': destination_landfreight,
            'otherCharges': other_charges,
            'availableContainers': available_containers,
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    df = load_data()
    if df is None:
        return jsonify({'status': 'error', 'message': 'No data file found'}), 500
    return jsonify({
        'status': 'ok',
        'totalRows': len(df),
        'destinations': df['Destination'].nunique(),
        'file': get_latest_processed_file()
    })

if __name__ == '__main__':
    print("Starting API server on http://localhost:5000")
    print(f"Data file: {get_latest_processed_file()}")
    app.run(host='0.0.0.0', port=5000, debug=True)
