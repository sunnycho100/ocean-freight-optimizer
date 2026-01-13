"""URL parameter extraction"""

import time
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .config import SEARCH_RESULT_TIMEOUT


def wait_for_results(driver):
    """
    Wait for search results to load
    
    Args:
        driver: Selenium WebDriver instance
    """
    print("[STEP 7] Waiting for results...")
    time.sleep(5)
    
    # Check current URL
    current_url_before = driver.current_url
    print(f"[DEBUG] URL after search click: {current_url_before[:100]}...")
    
    # Try to wait for Download All button (indicates results loaded)
    try:
        WebDriverWait(driver, SEARCH_RESULT_TIMEOUT).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "//button[contains(., 'Download All') or .//span[contains(.,'Download All')]]"
            ))
        )
        print("[SUCCESS] Results loaded!")
    except TimeoutException:
        print("[WARNING] Download All button not found - checking URL anyway...")
        current_url_after = driver.current_url
        print(f"[DEBUG] Final URL: {current_url_after[:150]}")
        
        if "destinationLocationCode" not in current_url_after:
            print("[ERROR] URL did not change after clicking Search - search may have failed")
            print("[DEBUG] Taking screenshot for debugging...")
            try:
                driver.save_screenshot("search_failed.png")
                print("[DEBUG] Screenshot saved: search_failed.png")
            except:
                pass


def extract_url_parameters(driver):
    """
    Extract location code and port lists from current URL
    Also checks for zero results
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        dict: Configuration with locationCode, pols, pods, has_results or None if extraction fails
    """
    import os
    from datetime import datetime
    
    print("[STEP 8] Extracting URL parameters...")
    time.sleep(2)
    
    print("[EXTRACTING] Analyzing URL parameters...")
    
    try:
        current_url = driver.current_url
        print(f"[INFO] Current URL: {current_url}")
        
        # Parse URL parameters
        parsed = urlparse(current_url)
        params = parse_qs(parsed.query)
        
        # Extract the parameters we need
        location_code = params.get('destinationLocationCode', [None])[0]
        pols = params.get('pols', [None])[0]
        pods = params.get('pods', [None])[0]
        
        # Fallback: try origin location code
        if not location_code:
            location_code = params.get('originLocationCode', [None])[0]
        
        if location_code:
            config = {
                'locationCode': location_code,
                'pols': pols if pols else '',
                'pods': pods if pods else ''
            }
            
            print(f"[SUCCESS] Extracted parameters:")
            print(f"   Location Code: {location_code}")
            print(f"   POLs: {pols if pols else 'None'}")
            print(f"   PODs: {pods if pods else 'None'}")
            
            # CHECK FOR ZERO RESULTS
            has_results = _check_results_count(driver)
            config['has_results'] = has_results
            
            if not has_results:
                print(f"[WARNING] ⚠ ZERO RESULTS FOUND!")
                print(f"[WARNING] Search completed but returned 0 tariff records")
                
                # Save warning to error_checks
                destination_name = params.get('destinationLocationName', ['UNKNOWN'])[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = destination_name.replace(',', '').replace(' ', '_').replace('%2C', '')
                
                error_dir = os.path.join(os.getcwd(), 'error_checks')
                os.makedirs(error_dir, exist_ok=True)
                
                # Screenshot
                screenshot_path = os.path.join(error_dir, f"ZERO_RESULTS_{safe_name}_{timestamp}.png")
                try:
                    driver.save_screenshot(screenshot_path)
                    print(f"[WARNING] Screenshot saved: {screenshot_path}")
                except Exception as e:
                    print(f"[WARNING] Could not save screenshot: {e}")
                
                # Warning log
                log_path = os.path.join(error_dir, f"ZERO_RESULTS_{safe_name}_{timestamp}.txt")
                try:
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.write(f"WARNING: Zero Results Found\n")
                        f.write(f"{'='*60}\n\n")
                        f.write(f"Destination: {destination_name}\n")
                        f.write(f"Location Code: {location_code}\n")
                        f.write(f"POLs: {pols if pols else 'None'}\n")
                        f.write(f"PODs: {pods if pods else 'None'}\n\n")
                        f.write(f"Status: Search completed successfully but returned 0 tariff records\n")
                        f.write(f"This may indicate:\n")
                        f.write(f"  - No tariff available for this destination\n")
                        f.write(f"  - Service not available to this location\n")
                        f.write(f"  - Configuration issue with PODs/POLs\n\n")
                        f.write(f"Timestamp: {datetime.now()}\n")
                    print(f"[WARNING] Warning log saved: {log_path}")
                except Exception as e:
                    print(f"[WARNING] Could not save warning log: {e}")
            
            return config
        else:
            print("[ERROR] ❌ LOCATION CODE NOT FOUND in URL")
            print("[ERROR] This destination may not exist in ONE Line system")
            print(f"[ERROR] URL checked: {current_url[:100]}...")
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to extract URL parameters: {e}")
        return None


def _check_results_count(driver):
    """
    Check if search returned any results by looking for "Total: X" text
    
    Returns:
        bool: True if results > 0, False if results = 0
    """
    try:
        # Look for "Total: X" or similar result count indicator
        # Try multiple strategies
        time.sleep(1)
        
        # Strategy 1: Look for "Total:" text
        try:
            total_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Total:')]")
            for elem in total_elements:
                text = elem.text
                if 'Total: 0' in text or 'Total:0' in text:
                    print(f"[DEBUG] Found zero results indicator: {text}")
                    return False
                elif 'Total:' in text:
                    print(f"[DEBUG] Found results indicator: {text}")
                    return True
        except:
            pass
        
        # Strategy 2: Look for empty table / no data message
        try:
            no_data_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'No data') or contains(text(), 'no result') or contains(text(), '0 result')]")
            if no_data_elements:
                print(f"[DEBUG] Found 'no data' message")
                return False
        except:
            pass
        
        # Strategy 3: Check for table rows
        try:
            table_rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
            if len(table_rows) == 0:
                print(f"[DEBUG] No table rows found")
                return False
            elif len(table_rows) > 0:
                print(f"[DEBUG] Found {len(table_rows)} table rows")
                return True
        except:
            pass
        
        # Default: assume has results if we can't determine
        print(f"[DEBUG] Could not determine result count, assuming has results")
        return True
        
    except Exception as e:
        print(f"[DEBUG] Error checking results count: {e}")
        return True  # Default to True if we can't check
