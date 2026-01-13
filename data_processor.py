"""
Data Processor for ONE Inland Rates
Combines inland rates with ocean freight rates and calculates total rates.
"""

import pandas as pd
import os
import glob
from datetime import datetime


def get_latest_inland_rate_file(download_dir='downloads'):
    """Find the most recent ONE_Inland_Rate_*.xlsx file in downloads folder."""
    pattern = os.path.join(download_dir, 'ONE_Inland_Rate_[0-9]*.xlsx')
    files = glob.glob(pattern)
    
    # Filter out processed files and temp files
    files = [f for f in files if not os.path.basename(f).startswith('~$') and 'Processed' not in f]
    
    if not files:
        raise FileNotFoundError(f"No ONE_Inland_Rate_*.xlsx files found in {download_dir}")
    
    # Sort by filename (date format YYYYMMDD) to get the most recent
    latest_file = max(files, key=lambda x: os.path.basename(x))
    
    print(f"Found latest inland rate file: {latest_file}")
    return latest_file


def load_data(inland_file, ocean_file):
    """Load inland rates and ocean freight data."""
    print(f"Loading inland rates from: {inland_file}")
    inland_df = pd.read_excel(inland_file)
    
    print(f"Loading ocean freight from: {ocean_file}")
    ocean_df = pd.read_excel(ocean_file)
    
    # Clean up any invalid rows in ocean freight (like the last row with Korean characters)
    ocean_df = ocean_df[ocean_df['POD'].notna() & (ocean_df['POD'] != '���հ�')]
    
    return inland_df, ocean_df


def clean_columns(df):
    """Remove extra validation columns (J, K, L, M, N, O)."""
    print("\nRemoving validation columns...")
    
    # Get column indices to drop
    # Columns are: 0-8 are data columns, 9-13 are validation columns to remove
    cols_to_keep = df.columns[:9]  # Keep only first 9 columns
    
    df_cleaned = df[cols_to_keep].copy()
    
    print(f"Columns after cleanup: {list(df_cleaned.columns)}")
    return df_cleaned


def add_ocean_rates(inland_df, ocean_df):
    """Add ocean rates based on POD and container size matching."""
    print("\nAdding ocean rates...")
    
    # Create a dictionary for quick lookup
    ocean_lookup = {}
    for _, row in ocean_df.iterrows():
        pod = row['POD']
        ocean_lookup[pod] = {
            '20': row['20 FT'],
            '40': row['40 FT']
        }
    
    # Function to get ocean rate for each row
    def get_ocean_rate(row):
        pod = row['POD']
        container_type = row['Container Type & Size']
        
        # Check if POD exists in ocean freight data
        if pod not in ocean_lookup:
            return None
        
        # Extract first 2 characters from container type (should be '20' or '40')
        if pd.isna(container_type):
            return None
        
        container_size = str(container_type)[:2]
        
        # Get the appropriate rate
        if container_size == '20':
            return ocean_lookup[pod]['20']
        elif container_size == '40':
            return ocean_lookup[pod]['40']
        else:
            return None
    
    # Add Ocean Rate column
    inland_df['Ocean Rate'] = inland_df.apply(get_ocean_rate, axis=1)
    
    # Check how many rows got matched
    matched = inland_df['Ocean Rate'].notna().sum()
    total = len(inland_df)
    print(f"Matched {matched}/{total} rows with ocean rates")
    
    return inland_df


def add_total_rates(df):
    """Add total rate column (Rate + Ocean Rate)."""
    print("\nCalculating total rates...")
    
    # Convert Rate column to numeric if it's not already
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')
    df['Ocean Rate'] = pd.to_numeric(df['Ocean Rate'], errors='coerce')
    
    # Calculate total rate
    df['Total Rate'] = df['Rate'] + df['Ocean Rate']
    
    return df


def add_cost_ranking(df):
    """Add cost ranking for each destination-container type combination."""
    print("\nAdding cost rankings...")
    
    # Sort by Total Rate first, then by POD name to ensure consistent tie-breaking
    df = df.sort_values(['Destination', 'Container Type & Size', 'Total Rate', 'POD'])
    
    # Create a ranking column (1 = cheapest, n = most expensive for each destination+container combination)
    # Use 'first' method to break ties by the sort order (POD name alphabetically)
    # This ensures routes with same cost get sequential ranks (1,2,3 instead of 1,1,3)
    df['Cost Rank'] = df.groupby(['Destination', 'Container Type & Size'])['Total Rate'].rank(method='first', ascending=True).astype(int)
    
    # Count total routes per destination-container combination
    df['Total Routes'] = df.groupby(['Destination', 'Container Type & Size'])['Total Rate'].transform('count')
    
    print(f"Added rankings for {df['Destination'].nunique()} destinations")
    
    return df


def save_processed_data(df, output_dir='downloads'):
    """Save the processed data to Excel."""
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f'ONE_Inland_Rate_Processed_{timestamp}.xlsx')
    
    print(f"\nSaving processed data to: {output_file}")
    df.to_excel(output_file, index=False)
    print(f"Saved successfully!")
    
    return output_file


def process_inland_rates(inland_file, ocean_file, output_dir='downloads'):
    """Main processing function."""
    print("="*60)
    print("ONE Inland Rates Data Processor")
    print("="*60)
    
    # Load data
    inland_df, ocean_df = load_data(inland_file, ocean_file)
    
    print(f"\nInitial inland data shape: {inland_df.shape}")
    print(f"Ocean freight data shape: {ocean_df.shape}")
    
    # Clean columns (remove J, K, L, M, N, O)
    inland_df = clean_columns(inland_df)
    
    # Add ocean rates
    inland_df = add_ocean_rates(inland_df, ocean_df)
    
    # Add total rates
    inland_df = add_total_rates(inland_df)
    
    # Add cost ranking
    inland_df = add_cost_ranking(inland_df)
    
    print(f"\nFinal data shape: {inland_df.shape}")
    print(f"Final columns: {list(inland_df.columns)}")
    
    # Save processed data
    output_file = save_processed_data(inland_df, output_dir)
    
    # Show sample results
    print("\n" + "="*60)
    print("Sample of processed data:")
    print("="*60)
    sample_cols = ['Destination', 'Container Type & Size', 'POD', 'Rate', 'Ocean Rate', 'Total Rate', 'Cost Rank']
    print(inland_df[sample_cols].head(15))
    
    # Show ranking examples
    print("\n" + "="*60)
    print("Top 3 cheapest routes for first destination:")
    print("="*60)
    first_dest = inland_df['Destination'].iloc[0]
    first_container = inland_df['Container Type & Size'].iloc[0]
    top_3 = inland_df[(inland_df['Destination'] == first_dest) & 
                      (inland_df['Container Type & Size'] == first_container)].nsmallest(3, 'Total Rate')
    print(top_3[['Destination', 'Container Type & Size', 'POD', 'Transport Mode', 'Total Rate', 'Cost Rank']])
    
    return inland_df, output_file


if __name__ == '__main__':
    # Find the latest inland rate file dynamically
    try:
        inland_file = get_latest_inland_rate_file('downloads')
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run quick_download_refactored.py first to generate the inland rate file.")
        exit(1)
    
    ocean_file = r'source\ocean_freight.xlsx'
    
    # Process the data
    df, output_file = process_inland_rates(inland_file, ocean_file)
    
    print("\n" + "="*60)
    print("Processing complete!")
    print(f"Output file: {output_file}")
    print("="*60)
