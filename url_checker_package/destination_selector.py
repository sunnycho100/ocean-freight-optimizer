"""Destination selection logic with smart matching"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .config import (
    ELEMENT_WAIT_TIMEOUT,
    DROPDOWN_TIMEOUT,
    EXACT_MATCH_SCORE,
    NORMALIZED_MATCH_SCORE,
    ALL_PARTS_MATCH_SCORE,
    PARTIAL_MATCH_SCORE,
    FIRST_WORD_MATCH_SCORE,
    WEAK_MATCH_SCORE,
    COUNTRY_BONUS_SCORE,
    MINIMUM_CONFIDENCE_SCORE
)

# Stopwords that should not be used alone as search terms
STOP_TOKENS = {
    "LE", "LA", "DE", "DI", "DA", "DEL", "DES", "DU", "DO", "DOS", "DAS",
    "ST", "STE", "SAINT", "SAN", "SANTA", "EL", "AL", "THE", "OF"
}


def select_destination(driver, destination_name):
    """
    Fill in the destination field with smart partial matching
    
    Strategy:
    - If city has hyphen: type first part only (to handle hyphen variations)
    - If city has NO hyphen: type FULL city name (to avoid partial matches)
    - Wait for dropdown, score all options, select best match
    - VERIFY selection matches expected destination
    
    Args:
        driver: Selenium WebDriver instance
        destination_name: Full destination string (e.g., "PARIS, FRANCE")
        
    Returns:
        dict: {'success': bool, 'selected': str or None, 'error': str or None}
    """
    print(f"\n[FILLING] Entering destination: {destination_name}")
    
    # Parse the input
    parts = [p.strip() for p in destination_name.split(',')]
    if len(parts) >= 2:
        city = parts[0]
        country = parts[-1]
        # Extract region/state if present (e.g., "MUENSTER, NW, GERMANY" -> region="NW")
        region = parts[1] if len(parts) == 3 else None
    else:
        city = destination_name
        country = destination_name
        region = None
    
    try:
        wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)
        
        # Find destination input field
        dest_input = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//label[contains(text(), 'Destination')]/following::input[1]"
            ))
        )
        
        # Determine search strategy based on city name
        # Strategy:
        # 1. Hyphenated cities (ARQUES-LA-BATAILLE): type first part only
        # 2. Multi-word cities with stopwords (LE HAVRE, LA SPEZIA): type meaningful chunk
        # 3. Multi-word cities (PORT KLANG, FOS SUR MER): type enough tokens for signal
        # 4. Single-word cities (VALENCE, TAMPERE): type full name for exact match
        
        tokens = city.upper().replace('-', ' ').split()
        
        if '-' in city:
            # Hyphenated city: type first part only (handle variations)
            partial_search = city.split('-')[0].upper()
            print(f"[STRATEGY] Hyphenated city: typing first part '{partial_search}' to handle variations")
        elif len(tokens) == 1:
            # Single-word city: type full name for exact match (avoid VALENCAY vs VALENCE)
            partial_search = city.upper()
            print(f"[STRATEGY] Single-word city: typing full name '{partial_search}' for exact match")
        else:
            # Multi-word city: build a meaningful prefix with enough signal
            if tokens[0] in STOP_TOKENS or len(tokens[0]) < 3:
                # First token is a stopword or too short: include at least 2 tokens
                partial_search = ' '.join(tokens[:2])
                print(f"[STRATEGY] Multi-word city with stopword/short prefix: typing '{partial_search}'")
            else:
                # First token is meaningful: start with it
                partial_search = tokens[0]
                print(f"[STRATEGY] Multi-word city: typing first meaningful word '{partial_search}'")
            
            # Ensure enough signal (at least 6-8 characters)
            if len(partial_search.replace(' ', '')) < 6 and len(tokens) >= 3:
                partial_search = ' '.join(tokens[:3])
                print(f"[STRATEGY] Extended to 3 tokens for more signal: '{partial_search}'")
        
        # Clear and type search term
        dest_input.click()
        dest_input.send_keys(Keys.CONTROL + "a")
        dest_input.send_keys(Keys.DELETE)
        dest_input.send_keys(partial_search)
        time.sleep(0.3)
        
        # Normalize city name for comparison
        city_normalized = city.upper().replace('-', ' ').strip()
        city_parts = city_normalized.split()
        
        # Use keyboard navigation to iterate through dropdown options
        print(f"[STRATEGY] Using keyboard navigation to scan dropdown options...")
        
        # Wait a moment for dropdown to appear
        time.sleep(1.0)  # Increased wait
        
        # Try multiple XPath patterns for dropdown options
        option_xpaths = [
            "//div[@role='option']",
            "//li[@role='option']",
            "//div[contains(@class, 'option')]",
            "//li[contains(@class, 'option')]",
            "//div[contains(@class, 'dropdown')]//div",
            "//ul[contains(@class, 'dropdown')]//li",
            "//div[@class='ant-select-item']",  # Ant Design
            "//div[contains(@class, 'ant-select-item')]",
        ]
        
        option_elements = []
        for xpath_pattern in option_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath_pattern)
                if elements:
                    print(f"[DEBUG] Found {len(elements)} elements with: {xpath_pattern[:60]}")
                    option_elements = elements
                    break
            except:
                continue
        
        if not option_elements:
            print(f"[WARN] No dropdown options found with any XPath pattern")
        
        best_match_index = -1
        best_score = 0
        best_option_text = None
        options_checked = []
        
        # Navigate through options using arrow keys
        max_options = 20  # Check up to 20 options
        
        # First, get a snapshot of all available options in the dropdown
        all_dropdown_options = []
        unavailable_options = []
        if option_elements:
            print(f"[DEBUG] Reading {len(option_elements)} option elements from DOM")
            for idx, opt in enumerate(option_elements[:20]):
                text = (opt.text or opt.get_attribute("innerText") or opt.get_attribute("textContent") or "").strip()
                if text and len(text) > 1:  # Ignore single characters
                    # Filter out options marked as "(No rates available)"
                    if "(No rates available)" in text or "(no rates available)" in text.lower():
                        unavailable_options.append(text)
                        print(f"   [DOM OPTION {idx+1}] {text[:70]}")
                    else:
                        all_dropdown_options.append((idx, text, opt))
                        print(f"   [DOM OPTION {idx+1}] {text[:70]}")
        
        # Check if ALL options are unavailable
        if unavailable_options and not all_dropdown_options:
            print(f"[ERROR] All {len(unavailable_options)} options show '(No rates available)'")
            import os
            from datetime import datetime
            from .error_summary import append_no_rates
            
            # Save error screenshot and log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = destination_name.replace(',', '').replace(' ', '_')
            error_dir = os.path.join(os.getcwd(), 'error_checks')
            os.makedirs(error_dir, exist_ok=True)
            
            screenshot_path = os.path.join(error_dir, f"NO_RATES_{safe_name}_{timestamp}.png")
            try:
                driver.save_screenshot(screenshot_path)
                print(f"[ERROR] Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"[WARNING] Could not save screenshot: {e}")
            
            log_path = os.path.join(error_dir, f"NO_RATES_{safe_name}_{timestamp}.txt")
            try:
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(f"ERROR: No Rates Available\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"Destination: {destination_name}\n")
                    f.write(f"Error: All dropdown options marked as '(No rates available)'\n\n")
                    f.write(f"Unavailable options found:\n")
                    for opt in unavailable_options:
                        f.write(f"  - {opt}\n")
                    f.write(f"\nTimestamp: {datetime.now()}\n")
                print(f"[ERROR] Error log saved: {log_path}")
            except Exception as e:
                print(f"[WARNING] Could not save error log: {e}")
            
            # Add to error summary (simple format for no rates)
            append_no_rates(destination_name, city, country)
            
            return {'success': False, 'selected': None, 'error': 'All options show no rates available'}
        
        
        # If we successfully read options from DOM, score them directly
        if all_dropdown_options:
            print(f"[INFO] Scoring {len(all_dropdown_options)} options from DOM...")
            best_match_index = -1
            best_score = 0
            best_option_text = None
            best_element = None
            
            for idx, option_text, opt_element in all_dropdown_options:
                option_text_upper = option_text.upper()
                option_normalized = option_text_upper.replace('-', ' ')
                
                score = _calculate_match_score(
                    city, city_normalized, city_parts, country, region,
                    option_text_upper, option_normalized
                )
                
                if score > best_score:
                    best_score = score
                    best_match_index = idx
                    best_option_text = option_text
                    best_element = opt_element
                    print(f"   [NEW BEST] Score: {best_score} at index {idx}")
            
            print(f"[RESULT] Best match: index {best_match_index}, score {best_score}")
            
            # CRITICAL CHECK: If country was specified, verify best match includes correct country
            # This prevents selecting "ATHENS, AL, USA" when we want "ATHENS, GREECE"
            if best_option_text and country:
                if country.upper() not in best_option_text.upper():
                    print(f"[ERROR] Best match doesn't contain expected country '{country}'")
                    print(f"        Best option: {best_option_text[:70]}")
                    print(f"        This would be incorrect - rejecting selection")
                    
                    import os
                    from datetime import datetime
                    from .error_summary import append_error
                    
                    # Save error screenshot and log
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = destination_name.replace(',', '').replace(' ', '_')
                    error_dir = os.path.join(os.getcwd(), 'error_checks')
                    os.makedirs(error_dir, exist_ok=True)
                    
                    screenshot_path = os.path.join(error_dir, f"WRONG_COUNTRY_{safe_name}_{timestamp}.png")
                    try:
                        driver.save_screenshot(screenshot_path)
                        print(f"[ERROR] Screenshot saved: {screenshot_path}")
                    except Exception as e:
                        print(f"[WARNING] Could not save screenshot: {e}")
                    
                    log_path = os.path.join(error_dir, f"WRONG_COUNTRY_{safe_name}_{timestamp}.txt")
                    try:
                        with open(log_path, 'w', encoding='utf-8') as f:
                            f.write(f"ERROR: Wrong Country Selected\n")
                            f.write(f"{'='*60}\n\n")
                            f.write(f"Destination: {destination_name}\n")
                            f.write(f"Expected Country: {country}\n")
                            f.write(f"Best Match Found: {best_option_text}\n")
                            f.write(f"Error: Best available option doesn't match expected country\n\n")
                            if unavailable_options:
                                f.write(f"Note: {len(unavailable_options)} options marked as '(No rates available)':\n")
                                for opt in unavailable_options:
                                    if country.upper() in opt.upper():
                                        f.write(f"  - {opt} ← CORRECT COUNTRY BUT NO RATES\n")
                                    else:
                                        f.write(f"  - {opt}\n")
                            f.write(f"\nTimestamp: {datetime.now()}\n")
                        print(f"[ERROR] Error log saved: {log_path}")
                    except Exception as e:
                        print(f"[WARNING] Could not save error log: {e}")
                    
                    # Add to error summary
                    error_msg = f"Best available option doesn't match expected country {country}. Found: {best_option_text}"
                    append_error("WRONG_COUNTRY", destination_name, error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    
                    return {'success': False, 'selected': None, 'error': f'No available options for {country}'}
            
            # Click the best match directly
            if best_match_index >= 0 and best_score >= MINIMUM_CONFIDENCE_SCORE:
                try:
                    print(f"[SELECTING] Clicking option: {best_option_text[:70]}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", best_element)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", best_element)
                    time.sleep(0.5)
                    
                    # Verify selection worked
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'POD')]/following::div[1]"))
                        )
                        print(f"[SUCCESS] Selected best match via DOM click")
                        return _verify_destination_selection(driver, destination_name, city, region, country, best_option_text)
                    except:
                        print(f"[ERROR] POD field didn't appear after click")
                        return {'success': False, 'selected': None, 'error': 'POD field not found after selection'}
                except Exception as e:
                    print(f"[ERROR] Failed to click element: {e}")
                    return {'success': False, 'selected': None, 'error': f'Click failed: {e}'}
            elif best_match_index >= 0:
                # Score below threshold but we have a match - select anyway
                print(f"[WARN] Best score ({best_score}) below threshold, selecting anyway...")
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", best_element)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", best_element)
                    time.sleep(0.5)
                    
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'POD')]/following::div[1]"))
                        )
                        return _verify_destination_selection(driver, destination_name, city, region, country, best_option_text)
                    except:
                        return {'success': False, 'selected': None, 'error': 'Selection failed'}
                except Exception as e:
                    return {'success': False, 'selected': None, 'error': f'Click failed: {e}'}
            else:
                print(f"[ERROR] No valid options found")
                return {'success': False, 'selected': None, 'error': 'No valid options found'}
        
        # Fallback: Try keyboard navigation if DOM reading failed
        print(f"[FALLBACK] DOM reading failed, trying keyboard navigation...")
        for i in range(max_options):
            try:
                # Press down arrow to move to next option
                if i > 0:  # Don't press down on first iteration
                    dest_input.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.15)
                else:
                    # First press down to enter dropdown
                    dest_input.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.2)
                
                # Try multiple methods to read the focused option text
                focused_text = None
                
                # Method 1: Check the input field value (some dropdowns update it)
                input_value = dest_input.get_attribute('value') or ""
                if input_value and input_value != partial_search:
                    focused_text = input_value
                    print(f"   [READ METHOD 1] Input value: {input_value[:60]}")
                
                # Method 2: Look for aria-activedescendant
                if not focused_text:
                    try:
                        active_id = dest_input.get_attribute('aria-activedescendant')
                        if active_id:
                            active_elem = driver.find_element(By.ID, active_id)
                            text = (active_elem.text or active_elem.get_attribute("innerText") or active_elem.get_attribute("textContent") or "").strip()
                            if text:
                                focused_text = text
                                print(f"   [READ METHOD 2] aria-activedescendant: {text[:60]}")
                    except:
                        pass
                
                # Method 3: Find element with focused/selected/active class
                if not focused_text:
                    try:
                        active_option = driver.find_element(By.XPATH, 
                            "//div[@role='option'][contains(@class, 'focused')] | "
                            "//li[@role='option'][contains(@class, 'focused')] | "
                            "//div[@role='option'][contains(@class, 'selected')] | "
                            "//li[@role='option'][contains(@class, 'selected')] | "
                            "//div[@role='option'][contains(@class, 'active')] | "
                            "//li[@role='option'][contains(@class, 'active')] | "
                            "//div[@role='option'][contains(@class, 'highlighted')] | "
                            "//li[@role='option'][contains(@class, 'highlighted')]")
                        text = (active_option.text or active_option.get_attribute("innerText") or active_option.get_attribute("textContent") or "").strip()
                        if text:
                            focused_text = text
                            print(f"   [READ METHOD 3] Class-based: {text[:60]}")
                    except:
                        pass
                
                # Method 4: Check all options for various state attributes
                if not focused_text:
                    try:
                        all_options = driver.find_elements(By.XPATH, option_xpath)
                        for opt in all_options:
                            # Check multiple attributes that might indicate focus
                            aria_selected = opt.get_attribute("aria-selected")
                            data_focused = opt.get_attribute("data-focused")
                            data_selected = opt.get_attribute("data-selected")
                            class_attr = opt.get_attribute("class") or ""
                            
                            if (aria_selected == "true" or 
                                data_focused == "true" or 
                                data_selected == "true" or
                                "focused" in class_attr.lower() or 
                                "selected" in class_attr.lower() or 
                                "active" in class_attr.lower() or 
                                "highlighted" in class_attr.lower()):
                                text = (opt.text or opt.get_attribute("innerText") or opt.get_attribute("textContent") or "").strip()
                                if text and text != partial_search:
                                    focused_text = text
                                    print(f"   [READ METHOD 4] Attribute-based: {text[:60]}")
                                    break
                    except:
                        pass
                
                # Method 5: Try to find any visible option with hover state
                if not focused_text:
                    try:
                        hover_option = driver.find_element(By.XPATH, 
                            "//div[@role='option'][contains(@class, 'hover')] | "
                            "//li[@role='option'][contains(@class, 'hover')]")
                        text = (hover_option.text or hover_option.get_attribute("innerText") or hover_option.get_attribute("textContent") or "").strip()
                        if text:
                            focused_text = text
                            print(f"   [READ METHOD 5] Hover state: {text[:60]}")
                    except:
                        pass
                
                # Debug: Print what we found
                if not focused_text:
                    print(f"   [OPTION {i+1}] Could not read text - trying to debug...")
                    # Print input attributes for debugging
                    print(f"      Input value: '{input_value}'")
                    print(f"      Partial search: '{partial_search}'")
                    try:
                        aria_id = dest_input.get_attribute('aria-activedescendant')
                        print(f"      aria-activedescendant: {aria_id}")
                    except:
                        pass
                    
                    if i > 5:  # If we've tried several times and still nothing, break
                        print(f"[INFO] Could not read options after {i} attempts")
                        break
                    continue
                
                # Check if we've seen this option before (loop detection)
                if focused_text in options_checked:
                    print(f"[INFO] Reached end of dropdown (option repeated)")
                    break
                
                options_checked.append(focused_text)
                option_text_upper = focused_text.upper()
                option_normalized = option_text_upper.replace('-', ' ')
                
                print(f"   [OPTION {i+1}] {focused_text[:70]}")
                
                # Score this option
                score = _calculate_match_score(
                    city, city_normalized, city_parts, country, region,
                    option_text_upper, option_normalized
                )
                
                if score > best_score:
                    best_score = score
                    best_match_index = i
                    best_option_text = focused_text
                    print(f"   [NEW BEST] Score: {best_score} at position {i+1}")
                
            except Exception as e:
                print(f"[DEBUG] Error reading option {i}: {e}")
                if i > 3:  # If we've successfully read a few options, continue
                    continue
                else:
                    break
        
        print(f"[RESULT] Checked {len(options_checked)} options. Best score: {best_score} at position {best_match_index+1}")
        
        # Navigate to and select the best match
        if best_match_index >= 0 and best_score >= MINIMUM_CONFIDENCE_SCORE:
            print(f"[SELECTING] Navigating to best match: {best_option_text[:70]}")
            
            # We're currently past the best option, need to go back up
            current_position = len(options_checked) - 1
            steps_to_go_back = current_position - best_match_index
            
            if steps_to_go_back > 0:
                print(f"[NAV] Going up {steps_to_go_back} steps to reach best match")
                for _ in range(steps_to_go_back):
                    dest_input.send_keys(Keys.ARROW_UP)
                    time.sleep(0.1)
            
            # Press Enter to select
            time.sleep(0.2)
            dest_input.send_keys(Keys.ENTER)
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            
            # Verify selection worked
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'POD')]/following::div[1]"))
                )
                print(f"[SUCCESS] Selected best match via keyboard navigation")
                return _verify_destination_selection(driver, destination_name, city, region, country, best_option_text)
            except:
                print(f"[ERROR] Selection failed - POD field didn't appear")
                return {'success': False, 'selected': None, 'error': 'POD field not found after selection'}
        
        elif best_match_index >= 0:
            # We found options but score was too low - select the best one anyway
            print(f"[WARN] Best score ({best_score}) below threshold ({MINIMUM_CONFIDENCE_SCORE}), selecting anyway...")
            
            current_position = len(options_checked) - 1
            steps_to_go_back = current_position - best_match_index
            
            if steps_to_go_back > 0:
                for _ in range(steps_to_go_back):
                    dest_input.send_keys(Keys.ARROW_UP)
                    time.sleep(0.1)
            
            time.sleep(0.2)
            dest_input.send_keys(Keys.ENTER)
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'POD')]/following::div[1]"))
                )
                print(f"[SUCCESS] Selected best available option")
                return _verify_destination_selection(driver, destination_name, city, region, country, best_option_text)
            except:
                return {'success': False, 'selected': None, 'error': 'Selection failed'}
        
        else:
            # No options found at all
            print(f"[ERROR] Could not read any dropdown options")
            return {'success': False, 'selected': None, 'error': 'No readable dropdown options found'}
                
    except Exception as e:
        print(f"[ERROR] Failed to select destination: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'selected': None, 'error': str(e)}


def _verify_destination_selection(driver, destination_name, city, region, country, selected_text):
    """
    Verify that the selected destination matches what we wanted
    
    Returns:
        dict: {'success': bool, 'selected': str, 'error': str or None}
    """
    import os
    from datetime import datetime
    
    # Normalize for comparison
    city_normalized = city.upper().replace('-', ' ')
    selected_normalized = selected_text.upper().replace('-', ' ')
    
    # Get first word of city for loose matching (handles spelling variations)
    city_first_word = city.split()[0].upper() if ' ' in city or '-' in city else city.upper()
    
    # Check if city name matches (loose matching for multi-word cities)
    city_matches = (
        city.upper() in selected_text or 
        city_normalized in selected_normalized or
        city_first_word in selected_text  # First word match (handles ALLGAEU vs ALLGAU)
    )
    
    # Check if region matches (if specified)
    region_matches = True
    if region:
        region_matches = region.upper() in selected_text
        if not region_matches:
            print(f"[WARNING] Region mismatch! Expected: {region}, Selected: {selected_text}")
    
    # Check if country matches
    country_matches = country.upper() in selected_text
    
    if city_matches and region_matches and country_matches:
        print(f"[VERIFIED] Selection matches expected destination ✓")
        return {'success': True, 'selected': selected_text, 'error': None}
    else:
        # Mismatch detected - but still return success=True to continue processing
        # Just flag it as a warning
        error_msg = f"Destination mismatch! Expected: {destination_name}, Selected: {selected_text}"
        print(f"[WARNING] {error_msg}")
        
        # Save screenshot and error log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = destination_name.replace(',', '').replace(' ', '_')
        
        error_dir = os.path.join(os.getcwd(), 'error_checks')
        os.makedirs(error_dir, exist_ok=True)
        
        # Screenshot
        screenshot_path = os.path.join(error_dir, f"MISMATCH_{safe_name}_{timestamp}.png")
        try:
            driver.save_screenshot(screenshot_path)
            print(f"[WARNING] Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"[WARNING] Could not save screenshot: {e}")
        
        # Error log
        log_path = os.path.join(error_dir, f"MISMATCH_{safe_name}_{timestamp}.txt")
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"WARNING: Destination Selection Mismatch\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"Expected: {destination_name}\n")
                f.write(f"Selected: {selected_text}\n\n")
                f.write(f"City match: {city_matches}\n")
                f.write(f"Region match: {region_matches} (expected: {region})\n")
                f.write(f"Country match: {country_matches}\n\n")
                f.write(f"Status: Continuing with search to extract location code\n\n")
                f.write(f"Timestamp: {datetime.now()}\n")
            print(f"[WARNING] Warning log saved: {log_path}")
        except Exception as e:
            print(f"[WARNING] Could not save warning log: {e}")
        
        # Return success=True to continue, but with error message
        return {'success': True, 'selected': selected_text, 'error': error_msg}


def _calculate_match_score(city, city_normalized, city_parts, country, region, option_text, option_normalized):
    """
    Calculate match score for a dropdown option
    
    Args:
        region: Expected region/state code (e.g., "NW", "BB") or None
    
    Returns:
        int: Match score (higher is better)
    """
    import re
    score = 0
    
    # Extract first part (city name) using delimiter-agnostic split
    # Handles formats like: "CITY, COUNTRY", "CITY - COUNTRY", "CITY (CC)", "CITY / COUNTRY"
    head = re.split(r"[,/()\-]| - ", option_text)[0].strip()
    
    # Special case: "CITY, CITY, COUNTRY" format (e.g., "PARIS, PARIS, FRANCE")
    # Where city name appears twice (city and region have same name)
    option_parts = [p.strip() for p in option_text.split(',')]
    if len(option_parts) >= 3 and option_parts[0].upper() == option_parts[1].upper():
        # This is a "CITY, CITY, COUNTRY" pattern
        if city.upper() == option_parts[0].upper() and country.upper() in option_text:
            score = EXACT_MATCH_SCORE + 100  # Extra bonus for this special format
            print(f"      → Special case: City appears twice ('{option_parts[0]}, {option_parts[1]}, ...')! Score: {score}")
            return score  # Early return with high confidence
    
    # Best: Exact city name match (with or without hyphens)
    if city.upper() == head:
        score = EXACT_MATCH_SCORE
        print(f"      → Exact match! Score: {score}")
    # Very good: Normalized city matches start of option
    elif option_normalized.startswith(city_normalized + ',') or option_normalized.startswith(city_normalized + ' -') or option_normalized.startswith(city_normalized + ' /'):
        score = NORMALIZED_MATCH_SCORE
        print(f"      → Normalized exact match! Score: {score}")
    # Good: All city parts present in option
    elif all(part in option_normalized for part in city_parts):
        if city_normalized in option_normalized:
            score = ALL_PARTS_MATCH_SCORE
            print(f"      → All parts in order! Score: {score}")
        else:
            score = PARTIAL_MATCH_SCORE
            print(f"      → All parts present! Score: {score}")
    # OK: First significant word matches
    elif len(city_parts) > 0 and city_parts[0] in option_normalized.split():
        score = FIRST_WORD_MATCH_SCORE
        print(f"      → First word match! Score: {score}")
    # Weak: Partial first word match
    elif len(city_parts) > 0 and city_parts[0][:4] in option_normalized:
        score = WEAK_MATCH_SCORE
        print(f"      → Partial first word! Score: {score}")
    
    # Bonus: Country match
    if score > 0 and country.upper() in option_text:
        score += COUNTRY_BONUS_SCORE
        print(f"      → Country matched! New score: {score}")
    
    # CRITICAL: Region match (e.g., "NW", "BB", "HE")
    # If region is specified and present in option, boost score significantly
    # If region is specified but DIFFERENT region in option, heavily penalize
    if region:
        option_parts = [p.strip() for p in option_text.split(',')]
        if len(option_parts) >= 3:
            option_region = option_parts[1].strip()  # Middle part
            if option_region == region.upper():
                score += 300  # Big bonus for exact region match
                print(f"      → Region matched ({region})! New score: {score}")
            elif option_region != region.upper() and len(option_region) <= 3:
                # Different region code found - heavy penalty
                score -= 500
                print(f"      → Region MISMATCH! Expected {region}, found {option_region}. Score: {score}")
    else:
        # No region specified - prefer options WITHOUT middle region codes
        # This helps select main city (e.g., "Frankfurt, Germany") over variants
        # (e.g., "Frankfurt (Oder), BB, Germany")
        option_parts = [p.strip() for p in option_text.split(',')]
        if len(option_parts) == 2:
            # Simple format like "FRANKFURT, GERMANY" - slight bonus
            score += 10
            print(f"      → Simple format (no region code) - slight bonus! Score: {score}")
    
    return score


def _fallback_selection(driver, dest_input):
    """
    Fallback: press Enter on first dropdown result
    
    Returns:
        bool: True if POD field appeared, False otherwise
    """
    print(f"[FALLBACK] Pressing Enter on first result...")
    dest_input.send_keys(Keys.ARROW_DOWN)
    dest_input.send_keys(Keys.ENTER)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)
    
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'POD')]/following::div[1]"))
        )
        return True
    except:
        return False
