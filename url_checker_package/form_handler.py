"""Form interaction utilities"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from .config import ELEMENT_WAIT_TIMEOUT


def click_dropdown_select_all(driver, label_text):
    """
    Find dropdown by label, open it, and click 'Select All'
    
    Args:
        driver: Selenium WebDriver instance
        label_text: Label text to find dropdown (e.g., "POD", "Container Type")
    """
    print(f"   [INFO] Handling '{label_text}'...")
    
    try:
        wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)
        
        # Find and click dropdown
        dropdown_div = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                f"//label[contains(text(), '{label_text}')]/following::div[1]"
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_div)
        dropdown_div.click()
        
        # Try to click 'Select All'
        try:
            select_all_xpath = "//div[contains(text(), 'Select All')] | //span[contains(text(), 'Select All')]"
            select_all = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, select_all_xpath))
            )
            driver.execute_script("arguments[0].click();", select_all)
            print(f"   [SUCCESS] Selected 'All' for {label_text}.")
        except:
            # Fallback: click first checkbox
            print(f"   [INFO] 'Select All' not found for {label_text}. Clicking first checkbox...")
            first_opt = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox']"))
            )
            driver.execute_script("arguments[0].click();", first_opt)
        
        # Close dropdown
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        
    except Exception as e:
        print(f"   [WARNING] Failed to Select All for {label_text}: {e}")


def set_date_and_weight(driver, date_value="2026-01-07", weight_value="21000"):
    """
    Set application date and weight fields
    
    Args:
        driver: Selenium WebDriver instance
        date_value: Date string in YYYY-MM-DD format
        weight_value: Weight value as string
    """
    try:
        wait = WebDriverWait(driver, 15)
        
        # Set date
        date_input = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//label[contains(text(), 'Application Date')]/following::input[1]"
            ))
        )
        date_input.click()
        date_input.send_keys(Keys.CONTROL + "a")
        date_input.send_keys(Keys.DELETE)
        date_input.send_keys(date_value)
        date_input.send_keys(Keys.TAB)
        
        # Set weight
        weight_input = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//label[contains(text(), 'Weight')]/following::input[1]"
            ))
        )
        weight_input.click()
        weight_input.send_keys(Keys.CONTROL + "a")
        weight_input.send_keys(Keys.DELETE)
        weight_input.send_keys(weight_value)
        
        print("[SUCCESS] Date and Weight set")
        
    except Exception as e:
        print(f"[WARNING] Date/Weight step had an issue (continuing): {e}")


def click_search_button(driver):
    """
    Click the Search button with retry logic
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("[SEARCHING] Clicking Search button...")
    
    try:
        # Close any open dropdowns first
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        
        wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)
        
        # Find Search button
        search_btn = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[.//span[contains(.,'Search')] or contains(.,'Search')]"
            ))
        )
        
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search_btn)
        
        # Wait for button to be enabled
        wait.until(lambda d: search_btn.is_enabled())
        
        # Try ActionChains click first, fallback to JavaScript
        try:
            wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, 
                    "//button[.//span[contains(.,'Search')] or contains(.,'Search')]"
                ))
            )
            ActionChains(driver).move_to_element(search_btn).pause(0.05).click().perform()
            print("[SUCCESS] Search button clicked")
        except (ElementClickInterceptedException, TimeoutException):
            driver.execute_script("arguments[0].click();", search_btn)
            print("[SUCCESS] Search button clicked (JavaScript)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to click Search button: {e}")
        import traceback
        traceback.print_exc()
        return False


def select_import_mode(driver):
    """
    Click the Import radio button/label
    
    Args:
        driver: Selenium WebDriver instance
    """
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Import')]"))
        ).click()
        print("[SUCCESS] Import mode selected")
    except Exception as e:
        print(f"[WARNING] Could not select Import (might be default): {e}")


def handle_cookie_popup(driver):
    """
    Accept cookie consent popup if present
    
    Args:
        driver: Selenium WebDriver instance
    """
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("[INFO] Accepted cookies")
    except:
        print("[INFO] No cookie popup")
