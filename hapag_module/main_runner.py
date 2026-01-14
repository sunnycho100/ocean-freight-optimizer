"""
Main runner module for Hapag-Lloyd quote extraction automation.

This module orchestrates the complete automation workflow, coordinating
all other modules to perform end-to-end quote extraction.
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright, Page

from .config_loader import ConfigLoader
from .browser_manager import BrowserManager
from .auth_manager import AuthManager
from .quote_scraper import QuoteScraper
from .data_extractor import DataExtractor
from .excel_exporter import ExcelExporter


class MainRunner:
    """Main automation workflow orchestrator."""
    
    def __init__(self, headless: bool = False, base_dir: str = None):
        """
        Initialize MainRunner with all required components.
        
        Args:
            headless: Whether to run browser in headless mode
            base_dir: Base directory for configuration files
        """
        self.headless = headless
        self.base_dir = base_dir
        
        # Initialize all components
        self.config_loader = ConfigLoader(base_dir)
        self.browser_manager = BrowserManager(headless)
        self.auth_manager = AuthManager()
        self.quote_scraper = QuoteScraper()
        self.data_extractor = DataExtractor()
        self.excel_exporter = ExcelExporter(base_dir)
        
        # Runtime data
        self.destinations: List[str] = []
        self.configs: Dict[str, Any] = {}
        self.excel_filename: str = ""
    
    def _load_configuration(self) -> bool:
        """
        Load destinations and configurations.
        
        Returns:
            True if configuration loaded successfully, False otherwise
        """
        print("📋 Loading configuration...")
        
        # Load destinations
        self.destinations = self.config_loader.load_destinations()
        if not self.destinations:
            print("❌ ERROR: No destinations loaded")
            return False
        
        # Load destination configs
        self.configs = self.config_loader.load_destination_configs()
        if not self.configs:
            print("❌ ERROR: No destination configurations loaded")
            return False
        
        # Validate configuration
        if not self.config_loader.validate_config(self.destinations, self.configs):
            print("❌ ERROR: Configuration validation failed")
            return False
        
        return True
    
    def _prepare_excel_file(self) -> bool:
        """
        Determine Excel filename for this run.
        
        Returns:
            True if Excel file preparation successful, False otherwise
        """
        try:
            self.excel_filename = self.excel_exporter.determine_excel_filename()
            print(f"📁 Excel file for this run: {self.excel_filename}")
            return True
            
        except Exception as e:
            print(f"❌ ERROR preparing Excel file: {e}")
            return False
    
    def _save_error_screenshot(self, page: Page, destination: str, error_type: str) -> None:
        """
        Save screenshot and error report when destination processing fails.
        
        Args:
            page: Page instance for screenshot
            destination: Destination name that failed
            error_type: Type of error (e.g., DESTINATION_NOT_FOUND)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_dest = destination.replace(",", "").replace(" ", "_")
            
            # Create error_checks directory if it doesn't exist
            error_dir = Path("error_checks")
            error_dir.mkdir(exist_ok=True)
            
            # Save screenshot
            screenshot_path = error_dir / f"{error_type}_{safe_dest}_{timestamp}.png"
            page.screenshot(path=str(screenshot_path))
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Save error text file
            error_file = error_dir / f"{error_type}_{safe_dest}_{timestamp}.txt"
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(f"Error Type: {error_type}\\n")
                f.write(f"Destination: {destination}\\n")
                f.write(f"Timestamp: {timestamp}\\n")
                f.write(f"URL: {page.url}\\n")
            print(f"📝 Error report saved: {error_file}")
            
        except Exception as e:
            print(f"⚠️ WARNING: Could not save error screenshot/report: {e}")
    
    def _print_summary(self) -> None:
        """Print processing summary."""
        print(f"\\n{'='*60}")
        print(f"📋 Processing {len(self.destinations)} destinations from destinations.txt")
        print(f"{'='*60}")
        for dest in self.destinations:
            print(f"  • {dest}")
        print(f"{'='*60}\n")
    
    def _process_destination(self, destination: str, index: int, total: int) -> bool:
        """
        Process a single destination.
        
        Args:
            destination: Destination name to process
            index: Current destination index (1-based)
            total: Total number of destinations
            
        Returns:
            True if destination processed successfully, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"🎯 Processing {index}/{total}: {destination}")
        print(f"{'='*60}")
        
        # Get location code and alternate codes from config
        config_entry = self.configs.get(destination, {})
        location_code = config_entry.get("hapagLocationCode") or config_entry.get("locationCode")
        
        if not location_code:
            print(f"❌ ERROR: No location code found for {destination}")
            return False
        
        # Build list of alternate codes to try
        alternate_codes = []
        if config_entry.get("hapagLocationCode") and config_entry.get("locationCode"):
            # If we have both hapag-specific and general code, try both
            if config_entry.get("hapagLocationCode") != config_entry.get("locationCode"):
                alternate_codes.append(config_entry.get("locationCode"))
        
        print(f"📍 Primary Location Code: {location_code}")
        if alternate_codes:
            print(f"📍 Alternate Codes: {', '.join(alternate_codes)}")
        
        page = self.browser_manager.get_page()
        if not page:
            print("❌ ERROR: No page instance available")
            return False
        
        # Perform quote search with alternate codes
        is_first_search = (index == 1)
        if not self.quote_scraper.perform_full_search(page, location_code, is_first_search, alternate_codes):
            # Take screenshot and save error
            self._save_error_screenshot(page, destination, "DESTINATION_NOT_FOUND")
            return False
        
        # Extract route information
        route_info = self.quote_scraper.extract_route_info(page)
        
        # Extract surcharges table data
        print("📊 Extracting Import Surcharges table...")
        table_data = self.data_extractor.extract_import_surcharges_table(page)
        
        if not table_data:
            print(f"⚠️ WARNING: No data extracted for {destination}")
            self.quote_scraper.close_price_breakdown(page)
            return False
        
        # Validate extracted data
        if not self.data_extractor.validate_extracted_data(table_data):
            print(f"⚠️ WARNING: Data validation failed for {destination}")
            self.quote_scraper.close_price_breakdown(page)
            return False
        
        # Save to Excel
        print("💾 Saving to Excel...")
        try:
            excel_path = self.excel_exporter.save_to_excel(
                table_data, 
                destination=destination, 
                route_info=route_info, 
                filename=self.excel_filename
            )
            print(f"✅ Data saved to: {excel_path}")
            
        except Exception as e:
            print(f"❌ ERROR saving to Excel: {e}")
            self.quote_scraper.close_price_breakdown(page)
            return False
        
        # Close price breakdown dialog
        self.quote_scraper.close_price_breakdown(page)
        
        print(f"✅ Completed {destination}")
        return True
    
    def _print_final_summary(self, successful_count: int) -> None:
        """
        Print final processing summary.
        
        Args:
            successful_count: Number of successfully processed destinations
        """
        print(f"\n{'='*60}")
        print(f"🎉 Processing complete!")
        print(f"✅ Successfully processed: {successful_count}/{len(self.destinations)} destinations")
        
        if successful_count < len(self.destinations):
            failed_count = len(self.destinations) - successful_count
            print(f"⚠️ Failed to process: {failed_count} destinations")
        
        print(f"{'='*60}")
        
        if successful_count > 0:
            excel_path = self.excel_exporter.get_excel_path(self.excel_filename)
            print(f"📁 Results saved to: {excel_path}")
    
    def run(self, playwright: Playwright) -> bool:
        """
        Execute the complete automation workflow.
        
        Args:
            playwright: Playwright instance
            
        Returns:
            True if workflow completed successfully, False otherwise
        """
        try:
            # Step 1: Load configuration
            if not self._load_configuration():
                return False
            
            # Step 2: Prepare Excel file
            if not self._prepare_excel_file():
                return False
            
            # Step 3: Print processing summary
            self._print_summary()
            
            # Step 4: Initialize browser
            page = self.browser_manager.launch_browser(playwright)
            
            # Step 5: Navigate to Hapag-Lloyd
            self.browser_manager.navigate_to_hapag(page)
            
            # Step 6: Handle Cloudflare challenge if present
            self.browser_manager.handle_cloudflare_challenge(page)
            
            # Step 7: Wait for page to load and handle cookie consent
            if not self.browser_manager.wait_for_page_load(page):
                return False
            
            self.browser_manager.handle_cookie_consent(page)
            
            # Step 7: Authenticate
            if not self.auth_manager.verify_login_status(page):
                if not self.auth_manager.login(page):
                    return False
            
            # Step 8: Process each destination
            successful_count = 0
            
            for idx, destination in enumerate(self.destinations, 1):
                try:
                    if self._process_destination(destination, idx, len(self.destinations)):
                        successful_count += 1
                    
                except Exception as e:
                    print(f"❌ CRITICAL ERROR processing {destination}: {e}")
                    continue
            
            # Step 9: Print final summary
            self._print_final_summary(successful_count)
            
            # Step 10: Keep browser open for review
            self.browser_manager.keep_browser_open()
            
            return successful_count > 0
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR in main workflow: {e}")
            return False
            
        finally:
            # Always clean up browser resources
            try:
                self.browser_manager.close_browser()
                print("✅ Automation complete!")
            except:
                pass
    
    def run_standalone(self) -> bool:
        """
        Run automation workflow with automatic Playwright management.
        
        Returns:
            True if workflow completed successfully, False otherwise
        """
        print("🚀 Starting Hapag-Lloyd Quote Extraction...")
        print("="*60)
        
        try:
            with sync_playwright() as playwright:
                return self.run(playwright)
                
        except Exception as e:
            print(f"❌ FATAL ERROR: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current run configuration.
        
        Returns:
            Dictionary with run statistics
        """
        return {
            "total_destinations": len(self.destinations),
            "excel_filename": self.excel_filename,
            "headless_mode": self.headless,
            "has_credentials": self.auth_manager.has_credentials(),
            "downloads_dir": self.excel_exporter.get_downloads_dir()
        }