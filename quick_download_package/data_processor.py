"""
Data Processing Module
Handles data cleaning, validation, and transformation.
"""

import pandas as pd


class DataProcessor:
    """Processes and validates scraped data."""
    
    def __init__(self):
        """Initialize the data processor."""
        pass
    
    def clean_and_validate(self, data, destination):
        """
        Clean and validate scraped data.
        
        Args:
            data: Dictionary with 'headers', 'data', and 'totalCount'
            destination: Name of the destination being processed
            
        Returns:
            pandas.DataFrame: Cleaned and validated DataFrame
        """
        if not data['data']:
            print("   [WARNING] No data to process!")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data['data'])
        
        # Clean Rate column
        df = self._clean_rate_column(df)
        
        # Clean Weight Range column
        df = self._clean_weight_range_column(df)
        
        # Add destination column at the start
        df.insert(0, 'Destination', destination)
        
        # Add metadata columns
        df = self._add_metadata_columns(df, destination, data.get('totalCount', 0))
        
        # Validate row count
        self._validate_row_count(df, data.get('totalCount', 0), destination)
        
        return df
    
    def _clean_rate_column(self, df):
        """
        Clean and convert Rate column to numeric.
        
        Args:
            df: DataFrame to process
            
        Returns:
            pandas.DataFrame: DataFrame with cleaned Rate column
        """
        if 'Rate' in df.columns:
            # Remove common currency symbols and convert to numeric
            df['Rate'] = (df['Rate'].astype(str)
                          .str.replace(',', '')
                          .str.replace('$', '')
                          .str.replace('€', '')
                          .str.replace('£', '')
                          .str.strip())
            df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')
            print(f"   [Cleaning] Converted Rate column to numeric")
        
        return df
    
    def _clean_weight_range_column(self, df):
        """
        Clean Weight Range column (ensure string consistency).
        
        Args:
            df: DataFrame to process
            
        Returns:
            pandas.DataFrame: DataFrame with cleaned Weight Range column
        """
        if 'Weight Range' in df.columns:
            df['Weight Range'] = df['Weight Range'].astype(str)
        
        return df
    
    def _add_metadata_columns(self, df, destination, total_count):
        """
        Add metadata columns (City Name, Total Count, Validation).
        
        Args:
            df: DataFrame to process
            destination: Destination name
            total_count: Expected total count from page
            
        Returns:
            pandas.DataFrame: DataFrame with metadata columns
        """
        actual_rows = len(df)
        
        # Self-checking validation: compare expected total vs actual rows scraped
        rows_match = (actual_rows == total_count)
        validation_result = 'TRUE' if rows_match else f'FALSE (Expected: {total_count}, Got: {actual_rows})'
        
        # Add 2 empty spacer columns and the metadata columns
        df[''] = ''
        df[' '] = ''  # Second spacer (space char to make unique)
        df['City Name'] = ''
        df['Total Count'] = ''
        df['Validation'] = ''
        
        # Set values only for the first row of this destination
        if len(df) > 0:
            df.at[0, 'City Name'] = destination
            df.at[0, 'Total Count'] = total_count
            df.at[0, 'Validation'] = validation_result
        
        print(f"   [Info] Added metadata: {destination} - Total: {total_count} results")
        
        return df
    
    def _validate_row_count(self, df, expected_count, destination):
        """
        Validate that scraped rows match expected count.
        
        Args:
            df: DataFrame to validate
            expected_count: Expected row count
            destination: Destination name for logging
        """
        actual_rows = len(df)
        rows_match = (actual_rows == expected_count)
        validation_status = 'PASS' if rows_match else 'FAIL'
        
        print(f"   [VALIDATION] {destination}: Rows scraped: {actual_rows}, "
              f"Expected: {expected_count} -> {validation_status}")
        
        if not rows_match:
            print(f"   [WARNING] Row count mismatch for {destination}!")
    
    def combine_dataframes(self, existing_df, new_df):
        """
        Combine existing and new DataFrames.
        
        Args:
            existing_df: Existing DataFrame (can be None)
            new_df: New DataFrame to append
            
        Returns:
            pandas.DataFrame: Combined DataFrame
        """
        if existing_df is None:
            return new_df
        
        # Ensure Rate column in existing data is also numeric
        if 'Rate' in existing_df.columns:
            existing_df['Rate'] = pd.to_numeric(existing_df['Rate'], errors='coerce')
        
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        print(f"   [Info] Existing rows: {len(existing_df)}, "
              f"New rows: {len(new_df)}, Total: {len(combined_df)}")
        
        return combined_df
