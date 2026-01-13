"""Configuration file management"""

import os
import json


def get_config_file_path(filename):
    """Get full path to config file in current working directory"""
    return os.path.join(os.getcwd(), filename)


def load_configs(config_file, destinations_file=None):
    """
    Load existing destination configs from JSON file.
    If config doesn't exist, initialize from destinations.txt
    
    Args:
        config_file: Path to JSON config file
        destinations_file: Path to destinations.txt file (optional)
        
    Returns:
        dict: Destination configurations
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Config doesn't exist - initialize from destinations.txt
            print(f"\n[INFO] {config_file} not found. Initializing from destinations.txt...")
            if destinations_file and os.path.exists(destinations_file):
                destinations = load_destinations_from_file(destinations_file)
                # Create initial config with empty values to be filled
                initial_config = {}
                for dest in destinations:
                    initial_config[dest] = {
                        "locationCode": "",
                        "pols": "",
                        "pods": ""
                    }
                # Save the initialized config
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_config, f, indent=2, ensure_ascii=False)
                print(f"[SUCCESS] Created {config_file} with {len(destinations)} destinations")
                return initial_config
            return {}
    except Exception as e:
        print(f"[ERROR] Could not load config file: {e}")
        return {}


def save_configs(configs, config_file):
    """
    Save destination configs to JSON file
    
    Args:
        configs: Dictionary of destination configurations
        config_file: Path to JSON config file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, indent=2, ensure_ascii=False)
        print(f"\n[SUCCESS] Saved configurations to {config_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Could not save config file: {e}")
        return False


def load_destinations_from_file(destinations_file):
    """
    Load destination list from text file
    
    Args:
        destinations_file: Path to destinations text file
        
    Returns:
        list: List of destination strings
    """
    destinations = []
    
    if os.path.exists(destinations_file):
        print(f"\n[INFO] Reading destinations from: {destinations_file}")
        with open(destinations_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    destinations.append(line)
        print(f"[INFO] Loaded {len(destinations)} destination(s) from file")
    else:
        print(f"\n[ERROR] destinations.txt not found at: {destinations_file}")
    
    return destinations
