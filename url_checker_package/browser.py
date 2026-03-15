"""Browser setup and management"""

import os
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

from .config import BROWSER_MAXIMIZE, IGNORE_CERT_ERRORS

_DRIVER_PATH = None
_DRIVER_PATH_LOCK = threading.Lock()


def _get_chromedriver_path():
    """
    Resolve and cache ChromeDriver path.

    webdriver-manager network/version checks are expensive, so caching the
    resolved binary path avoids repeated startup overhead when multiple
    workers/browsers are created.
    """
    global _DRIVER_PATH

    if _DRIVER_PATH and os.path.exists(_DRIVER_PATH):
        return _DRIVER_PATH

    with _DRIVER_PATH_LOCK:
        if _DRIVER_PATH and os.path.exists(_DRIVER_PATH):
            return _DRIVER_PATH
        # Force webdriver-manager cache to a writable runtime folder.
        cache_manager = DriverCacheManager(root_dir=os.getcwd())
        _DRIVER_PATH = ChromeDriverManager(cache_manager=cache_manager).install()
        return _DRIVER_PATH


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

    service = Service(_get_chromedriver_path())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver
