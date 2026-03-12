"""
Load and cache all data sources into queryable DataFrames.
Reuses the same loading logic from api_server.py.
"""
import pandas as pd
import json
import glob
import os


class FreightDataLoader:
    def __init__(self):
        self.one_data: pd.DataFrame = None
        self.hapag_data: pd.DataFrame = None
        self.destinations: dict = {}
        self.load_all()

    def load_all(self):
        """Load all data sources."""
        self._load_one_data()
        self._load_hapag_data()
        self._load_destinations()

    def _load_one_data(self):
        pattern = 'downloads/ONE_Inland_Rate_Processed_*.xlsx'
        files = glob.glob(pattern)
        files = [f for f in files if not os.path.basename(f).startswith('~$')]
        if files:
            latest = max(files, key=os.path.getmtime)
            self.one_data = pd.read_excel(latest)

    def _load_hapag_data(self):
        pattern1 = 'downloads/hapag_surcharges.xlsx'
        pattern2 = 'downloads/hapag_surcharges_*.xlsx'
        files = glob.glob(pattern1) + glob.glob(pattern2)
        files = [f for f in files if not os.path.basename(f).startswith('~$')]
        if files:
            latest = max(files, key=os.path.getmtime)
            df = pd.read_excel(latest, header=None, skiprows=4)
            df.columns = ['From', 'To', 'Via', 'Description', 'Curr.', '20STD', '40STD', '40HC', 'Transport Remarks']
            self.hapag_data = df

    def _load_destinations(self):
        config_path = 'destination_configs.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.destinations = json.load(f)

    def get_routes(self, destination: str, container_type: str = None) -> pd.DataFrame:
        """Filter ONE data by destination and optional container type."""
        if self.one_data is None:
            return pd.DataFrame()
        df = self.one_data
        mask = df['Destination'].str.upper() == destination.upper()
        if container_type:
            mask &= df['Container Type & Size'].str.upper() == container_type.upper()
        return df[mask].sort_values('Total Rate', ascending=True)

    def get_hapag_charges(self, destination: str) -> pd.DataFrame:
        """Filter HAPAG data by destination."""
        if self.hapag_data is None:
            return pd.DataFrame()
        mask = self.hapag_data['To'].str.upper() == destination.upper()
        return self.hapag_data[mask]

    def get_cheapest_route(self, destination: str, container_type: str) -> dict:
        """Return the cheapest route for given destination + container."""
        routes = self.get_routes(destination, container_type)
        if routes.empty:
            return {}
        best = routes.iloc[0]
        return {
            'destination': best['Destination'],
            'container_type': best['Container Type & Size'],
            'pod': best['POD'],
            'mode': best['Transport Mode'],
            'total_rate': float(best['Total Rate']),
            'ocean_rate': float(best['Ocean Rate']),
            'inland_rate': float(best['Rate']),
            'currency': best['Currency'],
        }

    def compare_carriers(self, destination: str, container_type: str = None) -> dict:
        """Side-by-side ONE vs HAPAG comparison data."""
        one_routes = self.get_routes(destination, container_type)
        hapag_charges = self.get_hapag_charges(destination)

        result = {'destination': destination}

        if not one_routes.empty:
            rows = []
            for _, row in one_routes.head(5).iterrows():
                rows.append({
                    'pod': row['POD'],
                    'mode': row['Transport Mode'],
                    'total_rate': float(row['Total Rate']),
                    'ocean_rate': float(row['Ocean Rate']),
                    'inland_rate': float(row['Rate']),
                    'currency': row['Currency'],
                })
            result['one'] = rows

        if not hapag_charges.empty:
            charges = []
            for _, row in hapag_charges.iterrows():
                charges.append({
                    'description': str(row['Description']),
                    'currency': str(row['Curr.']) if pd.notna(row['Curr.']) else '',
                    '20STD': str(row['20STD']) if pd.notna(row['20STD']) else '',
                    '40STD': str(row['40STD']) if pd.notna(row['40STD']) else '',
                    '40HC': str(row['40HC']) if pd.notna(row['40HC']) else '',
                })
            result['hapag'] = charges

        return result

    def get_all_destinations(self) -> list:
        """Return all available destination names."""
        dests = set()
        if self.one_data is not None:
            dests.update(self.one_data['Destination'].unique())
        if self.hapag_data is not None:
            dests.update(self.hapag_data['To'].unique())
        return sorted(dests)

    def get_container_types(self) -> list:
        """Return all available container types."""
        if self.one_data is not None:
            return sorted(self.one_data['Container Type & Size'].unique().tolist())
        return []

    def summarize_data(self) -> str:
        """Return a text summary of available data."""
        lines = []
        if self.one_data is not None:
            lines.append(f"ONE Line data: {len(self.one_data)} rows, "
                         f"{self.one_data['Destination'].nunique()} destinations, "
                         f"container types: {', '.join(self.get_container_types())}")
        else:
            lines.append("ONE Line data: not available")

        if self.hapag_data is not None:
            lines.append(f"HAPAG data: {len(self.hapag_data)} rows, "
                         f"{self.hapag_data['To'].nunique()} destinations")
        else:
            lines.append("HAPAG data: not available")

        lines.append(f"Configured destinations: {len(self.destinations)}")
        return "\n".join(lines)
