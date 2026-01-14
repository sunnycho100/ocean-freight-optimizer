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
    """Get the most recently processed HAPAG Excel file."""
    # Look for both patterns in downloads folder
    pattern1 = 'downloads/hapag_surcharges.xlsx'
    pattern2 = 'downloads/hapag_surcharges_*.xlsx'
    
    files = glob.glob(pattern1) + glob.glob(pattern2)
    # Filter out temp files
    files = [f for f in files if not os.path.basename(f).startswith('~$')]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def load_data():
    """Load the processed Excel data."""
    file_path = get_latest_processed_file()
    if not file_path:
        return None
    return pd.read_excel(file_path)

def load_hapag_data():
    """Load the HAPAG surcharges Excel data."""
    file_path = get_latest_hapag_file()
    if not file_path:
        return None
    # Read with header at row 3 (0-indexed: row 2 has the column headers, row 3 is first data row)
    # Skip the first 4 rows (2 info rows + 1 blank + 1 header row)
    df = pd.read_excel(file_path, header=None, skiprows=4)
    # Set column names manually
    df.columns = ['From', 'To', 'Via', 'Description', 'Curr.', '20STD', '40STD', '40HC', 'Transport Remarks']
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
    """Get route and charges for a specific HAPAG destination."""
    df = load_hapag_data()
    if df is None:
        return jsonify({'error': 'No HAPAG data file found'}), 404
    
    # Filter by destination
    filtered = df[df['To'] == destination].copy()
    
    if filtered.empty:
        return jsonify({'error': 'No routes found for destination'}), 404
    
    # Get route info (should be same for all rows)
    first_row = filtered.iloc[0]
    route_from = first_row['From']
    route_to = first_row['To']
    route_via = first_row['Via']
    
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
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) else '',
            }
            i += 1
            continue
        
        # Check if this is Destination Landfreight
        if 'destination landfreight' in desc.lower() or 'landfreight' in desc.lower():
            landfreight_item = {
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) else '',
            }
            
            # Check if empty curr (has sub-options)
            if curr == '' or pd.isna(row['Curr.']):
                sub_options = []
                i += 1
                
                # Look for sub-option rows (same pattern in first word)
                first_word = desc.split()[0].lower() if desc.split() else ''
                
                while i < len(filtered):
                    next_row = filtered.iloc[i]
                    next_desc = str(next_row['Description'])
                    next_first_word = next_desc.split()[0].lower() if next_desc.split() else ''
                    
                    # Check if it's a sub-option (starts with similar pattern like "Between", "Combined")
                    if (next_first_word in ['between', 'combined', 'from'] or 
                        (first_word and next_first_word == first_word)):
                        sub_options.append({
                            'description': next_desc,
                            'value20': str(next_row['20STD']) if pd.notna(next_row['20STD']) else '',
                            'value40': str(next_row['40STD']) if pd.notna(next_row['40STD']) else '',
                            'value40HC': str(next_row['40HC']) if pd.notna(next_row['40HC']) else '',
                        })
                        i += 1
                    else:
                        break
                
                if sub_options:
                    landfreight_item['subOptions'] = sub_options
                    # Get currency from first sub-option row if available
                    if i > 0 and i <= len(filtered):
                        prev_row = filtered.iloc[i-1]
                        if pd.notna(prev_row['Curr.']) and prev_row['Curr.'] != '':
                            landfreight_item['curr'] = str(prev_row['Curr.'])
            else:
                i += 1
            
            destination_landfreight = landfreight_item
            continue
        
        # Other charges
        if curr != '' and not pd.isna(row['Curr.']):
            other_charges.append({
                'description': desc,
                'curr': curr,
                'value20STD': str(row['20STD']) if pd.notna(row['20STD']) else '',
                'value40STD': str(row['40STD']) if pd.notna(row['40STD']) else '',
                'value40HC': str(row['40HC']) if pd.notna(row['40HC']) else '',
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
