"""
Configuration Loading and URL Building Module
Handles loading destination configs, setting up parameters, and building search URLs.
"""

import os
import json
from datetime import datetime


class ConfigLoader:
    """Manages configuration loading and URL building for quick download."""
    
    def __init__(self, base_dir=None):
        """
        Initialize the configuration loader.
        
        Args:
            base_dir: Base directory for config files (defaults to current working directory)
        """
        self.base_dir = base_dir or os.getcwd()
        self.destination_configs_file = os.path.join(self.base_dir, "destination_configs.json")
        self.destination_configs = {}
        
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Default URL parameters for EXPORT
        self.export_params = {
            "applicationDate": today,  # Automatically uses today's date
            "boundCode": "E",  # E = Export, I = Import
            "cargoType": "DR",  # DR = Dry/General
            "originLocationName": "",
            "originLocationCode": "",
            "pols": "",  # Ports of Loading (comma-separated)
            "pods": "",  # Ports of Discharge (leave empty or specify)
            "transportMode": "",
            "weightUnit": "KGS",
            "weightValue": "21000",
            "containerTypeSizeValue": "D2,D4,D5,R2,R5",  # Container types (comma-separated)
            "tariffCode": "ONEY-313",
            "routeTypeCode": ""
        }
        
        # Default URL parameters for IMPORT
        self.import_params = {
            "applicationDate": today,  # Automatically uses today's date
            "boundCode": "I",  # I = Import
            "cargoType": "DR",
            "destinationLocationName": "",  # Will be filled from destinations
            "destinationLocationCode": "",  # Will be filled from configs
            "originLocationName": "",  # Will be filled from destinations
            "originLocationCode": "",  # Will be filled from configs
            "pols": "",  # Will be filled from configs
            "pods": "",  # Will be filled from configs
            "transportMode": "B,U,R,A,T",
            "weightUnit": "KGS",
            "weightValue": "21000",
            "containerTypeSizeValue": "D2,D4,D5,R2,R5",
            "tariffCode": "ONEY-414",
            "routeTypeCode": ""
        }
    
    def load_destination_configs(self):
        """
        Load destination-specific configurations from JSON file.
        Returns dict of configs or creates sample file if not found.
        """
        try:
            if os.path.exists(self.destination_configs_file):
                with open(self.destination_configs_file, 'r', encoding='utf-8') as f:
                    self.destination_configs = json.load(f)
                print(f">>> Loaded {len(self.destination_configs)} destination configurations")
                return self.destination_configs
            else:
                print(f">>> [WARNING] Config file not found: {self.destination_configs_file}")
                self._create_sample_config()
                return self.destination_configs
        except Exception as e:
            print(f">>> [ERROR] Could not load destination configs: {e}")
            return {}
    
    def _create_sample_config(self):
        """Create a sample destination_configs.json file."""
        print(">>> Creating sample destination_configs.json file...")
        sample_config = {
            "OEGSTGEEST, NETHERLANDS": {
                "locationCode": "NLGSG",
                "pols": "BEANR,NLRTM",
                "pods": "BEANR,NLRTM"
            },
            "ANCONA, ITALY": {
                "locationCode": "ITAOI",
                "pols": "ITAOI,ITGOA,ITSPE,ITLIV,ITNAP,GRPIR,ITRAN,ITSAL,ITVCE",
                "pods": "ITAOI,ITGOA,ITSPE,ITLIV,ITNAP,GRPIR,ITRAN,ITSAL,ITVCE"
            }
        }
        try:
            with open(self.destination_configs_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2)
            print(">>> Please add your destinations to destination_configs.json")
            self.destination_configs = sample_config
        except Exception as e:
            print(f">>> [ERROR] Could not create sample config: {e}")
    
    def get_destinations(self):
        """Get list of destination names from loaded configs."""
        return list(self.destination_configs.keys())
    
    def get_params_for_destination(self, destination, use_import=True):
        """
        Get URL parameters for a specific destination.
        
        Args:
            destination: Destination name (must exist in configs)
            use_import: If True, use import params; otherwise export params
            
        Returns:
            dict: Parameters ready for URL building
        """
        if destination not in self.destination_configs:
            raise ValueError(f"Destination '{destination}' not found in configs")
        
        config = self.destination_configs[destination]
        
        # Start with base params
        params = self.import_params.copy() if use_import else self.export_params.copy()
        
        # Update with destination-specific values
        if use_import:
            params["destinationLocationName"] = destination
            params["destinationLocationCode"] = config["locationCode"]
            params["originLocationName"] = destination
            params["originLocationCode"] = config["locationCode"]
            params["pols"] = config["pols"]
            params["pods"] = config["pods"]
        else:  # Export
            params["originLocationName"] = destination
            params["originLocationCode"] = config["locationCode"]
            params["pols"] = config["pols"]
        
        return params
    
    def build_search_url(self, params):
        """
        Build the ONE Line search URL with parameters.
        
        Args:
            params: Dictionary of URL parameters
            
        Returns:
            str: Complete search URL
        """
        base = "https://ecomm.one-line.com/one-ecom/prices/rate-tariff/inland-search"
        
        # Convert params dict to URL query string
        query_parts = []
        for key, value in params.items():
            # Skip internal tracking flags (starting with _)
            if key.startswith('_'):
                continue
            if value and isinstance(value, str):  # Only include non-empty string values
                # URL encode special characters
                encoded_value = value.replace(" ", "%20").replace(",", "%2C").replace("+", "%2B")
                query_parts.append(f"{key}={encoded_value}")
        
        return base + "?" + "&".join(query_parts)
    
    def generate_filename(self):
        """
        Generate Excel filename based on current date.
        Format: ONE_Inland_Rate_YYYYMMDD.xlsx
        """
        today = datetime.now().strftime("%Y%m%d")
        return f"ONE_Inland_Rate_{today}.xlsx"
    
    def get_config_for_destination(self, destination):
        """Get the configuration dict for a specific destination."""
        return self.destination_configs.get(destination)
