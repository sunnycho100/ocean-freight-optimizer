"""Browser setup and management"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .config import BROWSER_MAXIMIZE, IGNORE_CERT_ERRORS


def setup_browser():
    """
    Initialize and return Chrome browser instance
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    print("[SETUP] Initializing browser...")
    
    options = webdriver.ChromeOptions()
    
    if BROWSER_MAXIMIZE:
        options.add_argument("--start-maximized")
    
    if IGNORE_CERT_ERRORS:
        options.add_argument("--ignore-certificate-errors")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver
