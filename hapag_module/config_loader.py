"""
Configuration and destination management for Hapag-Lloyd extraction.

This module handles loading destinations from text files and configuration
data from JSON files.
"""

import os
import json
from typing import List, Dict, Any


class ConfigLoader:
    """Handles loading configuration files and destination data."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize ConfigLoader.
        
        Args:
            base_dir: Base directory for config files. Defaults to current working directory.
        """
        self.base_dir = base_dir or os.getcwd()
    
    def load_destinations(self, filename: str = "destinations.txt") -> List[str]:
        """
        Load destinations from destinations.txt
        
        Args:
            filename: Name of the destinations file
            
        Returns:
            List of destination names
        """
        destinations = []
        file_path = os.path.join(self.base_dir, filename)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):  # Skip comments
                        destinations.append(line)
            
            print(f"✅ Loaded {len(destinations)} destinations from {filename}")
            return destinations
            
        except FileNotFoundError:
            print(f"❌ ERROR: {filename} not found in {self.base_dir}")
            return []
        except Exception as e:
            print(f"❌ ERROR loading destinations: {e}")
            return []
    
    def load_destination_configs(self, filename: str = "destination_configs.json") -> Dict[str, Any]:
        """
        Load destination configurations from destination_configs.json
        
        Args:
            filename: Name of the config file
            
        Returns:
            Dictionary of destination configurations
        """
        file_path = os.path.join(self.base_dir, filename)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                configs = json.load(f)
            
            print(f"✅ Loaded configurations for {len(configs)} destinations")
            return configs
            
        except FileNotFoundError:
            print(f"❌ ERROR: {filename} not found in {self.base_dir}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON in {filename}: {e}")
            return {}
        except Exception as e:
            print(f"❌ ERROR loading destination configs: {e}")
            return {}
    
    def get_location_code(self, destination: str, configs: Dict[str, Any]) -> str:
        """
        Get location code for a specific destination.
        
        Args:
            destination: Destination name
            configs: Configuration dictionary
            
        Returns:
            Location code string, or empty string if not found
        """
        if destination not in configs:
            print(f"❌ ERROR: '{destination}' not found in destination configs")
            return ""
        
        location_code = configs[destination].get("locationCode", "")
        if not location_code:
            print(f"❌ ERROR: No locationCode found for '{destination}'")
        
        return location_code
    
    def validate_config(self, destinations: List[str], configs: Dict[str, Any]) -> bool:
        """
        Validate that all destinations have corresponding configurations.
        
        Args:
            destinations: List of destination names
            configs: Configuration dictionary
            
        Returns:
            True if all destinations have valid configs, False otherwise
        """
        missing_configs = []
        invalid_configs = []
        
        for dest in destinations:
            if dest not in configs:
                missing_configs.append(dest)
            elif not configs[dest].get("locationCode"):
                invalid_configs.append(dest)
        
        if missing_configs:
            print(f"❌ Missing configurations: {missing_configs}")
        
        if invalid_configs:
            print(f"❌ Invalid configurations (missing locationCode): {invalid_configs}")
        
        is_valid = len(missing_configs) == 0 and len(invalid_configs) == 0
        
        if is_valid:
            print("✅ All destination configurations are valid")
        
        return is_valid