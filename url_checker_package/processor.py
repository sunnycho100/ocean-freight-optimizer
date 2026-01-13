"""Main processing workflow for extracting destination configurations"""

import time
from selenium.webdriver.support.ui import WebDriverWait

from .config import BASE_URL, PAGE_LOAD_TIMEOUT
from .destination_selector import select_destination
from .form_handler import (
    handle_cookie_popup,
    select_import_mode,
    click_dropdown_select_all,
    set_date_and_weight,
    click_search_button
)
from .url_extractor import wait_for_results, extract_url_parameters


def process_destination(driver, destination_name):
    """
    Process a single destination through the complete workflow:
    1. Navigate to search page
    2. Handle cookie popup
    3. Select Import mode
    4. Fill Destination
    5. Select All POD
    6. Select All Container Type
    7. Click Search (skip Date/Weight/Transport)
    8. Extract URL parameters
    
    Args:
        driver: Selenium WebDriver instance
        destination_name: Full destination string (e.g., "PARIS, FRANCE")
        
    Returns:
        dict: Extracted config (locationCode, pols, pods) or None if failed
    """
    print("\n" + "=" * 60)
    print(f"PROCESSING: {destination_name}")
    print("=" * 60)
    
    try:
        # Navigate to search page
        print("[LOADING] Opening ONE Line search page...")
        driver.get(BASE_URL)
        
        # Wait for page to load
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Handle cookie popup
        handle_cookie_popup(driver)
        
        # Select Import mode
        print("[STEP 1] Switching to IMPORT...")
        select_import_mode(driver)
        
        # Fill destination
        print("[STEP 2] Entering Destination...")
        dest_result = select_destination(driver, destination_name)
        
        if not dest_result['success']:
            error = dest_result.get('error', 'Unknown error')
            print(f"[ERROR] Destination selection failed: {error}")
            
            # Save error screenshot
            import os
            from datetime import datetime
            from .error_summary import append_error
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = destination_name.replace(',', '').replace(' ', '_')
            error_dir = os.path.join(os.getcwd(), 'error_checks')
            os.makedirs(error_dir, exist_ok=True)
            
            screenshot_path = os.path.join(error_dir, f"SELECTION_FAILED_{safe_name}_{timestamp}.png")
            try:
                driver.save_screenshot(screenshot_path)
                print(f"[ERROR] Screenshot saved: {screenshot_path}")
            except:
                pass
            
            log_path = os.path.join(error_dir, f"SELECTION_FAILED_{safe_name}_{timestamp}.txt")
            try:
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(f"ERROR: Destination Selection Failed\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"Destination: {destination_name}\n")
                    f.write(f"Error: {error}\n\n")
                    f.write(f"Timestamp: {datetime.now()}\n")
                print(f"[ERROR] Error log saved: {log_path}")
            except:
                pass
            
            # Add to error summary
            append_error("SELECTION_FAILED", destination_name, error, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            return None
        
        # Check if there was a warning but still successful
        if dest_result.get('error'):
            print(f"[WARNING] Destination mismatch but continuing: {dest_result.get('error')}")
            # Continue processing to get location code anyway
        
        # Select POD (all) - needed for URL parameters
        print("[STEP 3] Selecting POD...")
        click_dropdown_select_all(driver, "POD")
        
        # Select Container Type (all) - needed for URL parameters
        print("[STEP 4] Selecting Container Type...")
        click_dropdown_select_all(driver, "Container Type")
        
        # Click Search (skip Date & Weight and Transport Mode)
        print("[STEP 5] Clicking Search...")
        if not click_search_button(driver):
            return None
        
        # Wait for results
        wait_for_results(driver)
        
        # Extract URL parameters
        config = extract_url_parameters(driver)
        
        return config
        
    except Exception as e:
        print(f"[ERROR] Failed to process destination: {e}")
        import traceback
        traceback.print_exc()
        
        # Save screenshot for debugging
        try:
            driver.save_screenshot("url_checker_crash.png")
            print("[INFO] Screenshot saved: url_checker_crash.png")
        except:
            pass
        
        return None
