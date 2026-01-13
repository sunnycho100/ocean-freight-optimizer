"""
Destination Processing Module
Orchestrates the workflow for processing individual destinations.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DestinationProcessor:
    """Handles the complete workflow for processing a single destination."""
    
    def __init__(self, driver, config_loader, table_scraper):
        """
        Initialize destination processor.
        
        Args:
            driver: Selenium WebDriver instance
            config_loader: ConfigLoader instance
            table_scraper: TableScraper instance
        """
        self.driver = driver
        self.config_loader = config_loader
        self.table_scraper = table_scraper
    
    def process_destination(self, destination, use_import=True):
        """
        Process a single destination: build URL, navigate, scrape data.
        
        Args:
            destination: Destination name to process
            use_import: If True, use import params; otherwise export params
            
        Returns:
            dict: Result dictionary with success status, data, and error info
        """
        print("\n" + "=" * 60)
        print(f"PROCESSING: {destination}")
        print("=" * 60)
        
        # Get destination configuration
        config = self.config_loader.get_config_for_destination(destination)
        
        if not config:
            print(f"   [ERROR] Destination '{destination}' not found in destination_configs.json!")
            print(f"   [ERROR] Please run url_checker_refactored.py first to generate configs")
            print(f"   [ERROR] Skipping this destination...")
            return {
                'success': False,
                'destination': destination,
                'error': 'No configuration found in destination_configs.json'
            }
        
        # Display configuration info
        self._log_config_info(destination, config, use_import)
        
        try:
            # Get params for this destination
            params = self.config_loader.get_params_for_destination(destination, use_import)
            
            # Build and navigate to URL
            search_url = self.config_loader.build_search_url(params)
            print(f">>> Navigating to search page...")
            print(f">>> FULL URL: {search_url}")
            self.driver.get(search_url)
            
            # Handle initial page setup
            self._handle_initial_page_setup()
            
            # Execute search
            self._execute_search()
            
            # Wait for results
            self._wait_for_results()
            
            # Scrape data
            scraped_data = self.table_scraper.scrape_inland_tariff_table()
            
            return {
                'success': True,
                'destination': destination,
                'data': scraped_data,
                'params': params
            }
            
        except Exception as e:
            print(f">>> [ERROR] Failed to process {destination}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'destination': destination,
                'error': str(e)
            }
    
    def _log_config_info(self, destination, config, use_import):
        """
        Log configuration information for the destination.
        
        Args:
            destination: Destination name
            config: Configuration dictionary
            use_import: Whether using import or export
        """
        print(f"   [JSON Config] Reading from destination_configs.json for: {destination}")
        print(f"   [JSON Config] Location Code: {config['locationCode']}")
        
        if use_import:
            pols_msg = config['pols'] if config['pols'] else '(empty - normal for import)'
            print(f"   [JSON Config] POLs: {pols_msg}")
        else:
            print(f"   [JSON Config] POLs: {config['pols']}")
        
        print(f"   [JSON Config] PODs: {config['pods']}")
        print(f"   [URL Build] Using locationCode={config['locationCode']} from JSON")
    
    def _handle_initial_page_setup(self):
        """Handle initial page setup (cookies, page load)."""
        # Handle cookie popup (only needed first time)
        try:
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
            print("   [Info] Cookie popup accepted")
        except:
            pass  # Cookie popup may not appear
        
        # Wait for page ready
        WebDriverWait(self.driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("   [Info] Page loaded successfully")
    
    def _execute_search(self):
        """Click the search button to execute the search."""
        print(f">>> Executing search...")
        search_btn = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[.//span[contains(.,'Search')] or contains(.,'Search')]"
            ))
        )
        self.driver.execute_script("arguments[0].click();", search_btn)
        print("   [Info] Search button clicked")
    
    def _wait_for_results(self):
        """Wait for search results to appear."""
        print(f">>> Waiting for results...")
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH, 
                "//table | //div[@role='table']"
            ))
        )
        
        # Wait longer for ALL rows to load
        time.sleep(3)
        print("   [Info] Results loaded")
