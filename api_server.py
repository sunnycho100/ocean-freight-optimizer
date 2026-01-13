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

def load_data():
    """Load the processed Excel data."""
    file_path = get_latest_processed_file()
    if not file_path:
        return None
    return pd.read_excel(file_path)

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
