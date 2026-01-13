"""
Quick Download - Main Entry Point
Downloads ONE Line Inland Tariff data for multiple destinations.

This is a refactored version that uses the quick_download_package for better
organization and easier debugging.
"""

import os
import sys
import time

# --- CONFIG: IGNORE SSL ERRORS ---
os.environ["WDM_SSL_VERIFY"] = "0"
os.environ["WDM_LOCAL"] = "1"

from quick_download_package import (
    ConfigLoader,
    BrowserManager,
    TableScraper,
    DataProcessor,
    ExcelManager,
    DestinationProcessor
)


# --- CONFIGURATION ---
USE_IMPORT = True  # Set to False for Export, True for Import
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
ERROR_FOLDER = os.path.join(os.getcwd(), "scraping_errors")


def quick_download():
    """
    Main function: Loop through destinations, scrape each, and save to Excel.
    """
    # Initialize components
    config_loader = ConfigLoader()
    browser_manager = BrowserManager(download_dir=DOWNLOAD_DIR)
    excel_manager = ExcelManager(output_dir=DOWNLOAD_DIR, error_folder=ERROR_FOLDER)
    data_processor = DataProcessor()
    
    # Load destination configurations
    config_loader.load_destination_configs()
    destinations = config_loader.get_destinations()
    
    if not destinations:
        print("\n>>> No destinations found in destination_configs.json. Exiting.")
        print(">>> Please run url_checker_refactored.py first to generate destination configs.")
        return
    
    print(f">>> Loaded {len(destinations)} destinations from destination_configs.json:")
    for i, dest in enumerate(destinations, 1):
        print(f"    {i}. {dest}")
    
    # Setup browser
    driver = browser_manager.setup_browser()
    
    try:
        # Initialize components that need driver
        table_scraper = TableScraper(driver, error_folder=ERROR_FOLDER)
        destination_processor = DestinationProcessor(driver, config_loader, table_scraper)
        
        # Generate filename (same for all destinations)
        filename = config_loader.generate_filename()
        
        print("\n" + "=" * 60)
        print(f"OUTPUT FILE: {filename}")
        print(f"DESTINATIONS: {len(destinations)}")
        print(f"MODE: {'IMPORT' if USE_IMPORT else 'EXPORT'}")
        print("=" * 60)
        
        # Process each destination
        results = []
        
        for i, destination in enumerate(destinations, 1):
            print(f"\n[{i}/{len(destinations)}] Processing {destination}...")
            
            try:
                # Process destination
                result = destination_processor.process_destination(destination, use_import=USE_IMPORT)
                results.append(result)
                
                if result['success']:
                    # Clean and validate data
                    cleaned_df = data_processor.clean_and_validate(
                        result['data'],
                        result['destination']
                    )
                    
                    if cleaned_df is not None:
                        # Save to Excel
                        success = excel_manager.save_to_excel(
                            cleaned_df,
                            filename,
                            result['destination']
                        )
                        
                        if not success:
                            print(f">>> [WARNING] Failed to save data for {destination}")
                    else:
                        print(f">>> [WARNING] No data to save for {destination}")
                
            except Exception as e:
                print(f">>> [ERROR] Exception processing {destination}: {e}")
                import traceback
                traceback.print_exc()
                
                # Save error screenshot and log
                excel_manager.save_exception_log(destination, e, driver)
                
                # Try to restart browser on crash
                try:
                    driver = browser_manager.restart_browser()
                    # Reinitialize components with new driver
                    table_scraper = TableScraper(driver, error_folder=ERROR_FOLDER)
                    destination_processor = DestinationProcessor(
                        driver, config_loader, table_scraper
                    )
                except Exception as restart_err:
                    print(f">>> [FATAL] Could not restart browser: {restart_err}")
                    break
                
                results.append({
                    'success': False,
                    'destination': destination,
                    'error': f'Exception: {e}'
                })
            
            # Small delay between destinations
            time.sleep(1)
        
        # Summary
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        successful = sum(1 for r in results if r['success'])
        print(f"Successful: {successful}/{len(destinations)}")
        print(f"Output file: {filename}")
        print(f"Location: {DOWNLOAD_DIR}")
        print("=" * 60)
        
        # Show failed destinations
        failed = [r for r in results if not r['success']]
        if failed:
            print("\nFailed destinations:")
            for r in failed:
                print(f"  - {r['destination']}: {r.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n!!! CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            driver.save_screenshot(os.path.join(ERROR_FOLDER, "scraping_error.png"))
            print("Screenshot saved: scraping_error.png")
        except:
            pass
    
    finally:
        browser_manager.close_browser()


if __name__ == "__main__":
    print("=" * 60)
    print("WEB SCRAPER - ONE Line Inland Tariff")
    print("REFACTORED VERSION - Using quick_download_package")
    print("=" * 60)
    print(f"Mode: {'IMPORT' if USE_IMPORT else 'EXPORT'}")
    print(f"Output Directory: {DOWNLOAD_DIR}")
    print(f"Error Folder: {ERROR_FOLDER}")
    print("\nMULTI-DESTINATION: Scraping from .json config and appending to single file")
    print("SELF-CHECKING: Validating row counts for each city")
    print("=" * 60)
    
    quick_download()
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
