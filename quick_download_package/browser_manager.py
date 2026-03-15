"""
Browser Management Module
Handles browser initialization, setup, and lifecycle management.
"""

import os
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

_DRIVER_PATH = None
_DRIVER_PATH_LOCK = threading.Lock()


def _get_chromedriver_path():
    """Resolve and cache ChromeDriver path for faster browser restarts."""
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


class BrowserManager:
    """Manages Selenium WebDriver browser instance."""
    
    def __init__(self, download_dir=None):
        """
        Initialize browser manager.
        
        Args:
            download_dir: Directory for downloads (defaults to ./downloads)
        """
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        self.driver = None
        
        # Ensure download directory exists
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # Configure SSL settings
        os.environ["WDM_SSL_VERIFY"] = "0"
        # Do not force WDM_LOCAL in frozen apps; it can resolve to invalid temp paths.
        os.environ.pop("WDM_LOCAL", None)
    
    def setup_browser(self):
        """
        Setup and return a configured Chrome WebDriver instance.
        
        Returns:
            WebDriver: Configured Chrome driver
        """
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        
        # Download preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # Browser options
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        
        # Create driver
        service = Service(_get_chromedriver_path())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        print(">>> Browser initialized successfully")
        return self.driver
    
    def restart_browser(self):
        """
        Restart the browser (useful for recovery from crashes).
        
        Returns:
            WebDriver: New driver instance
        """
        print(">>> [Recovery] Restarting browser...")
        self.close_browser()
        return self.setup_browser()
    
    def close_browser(self):
        """Close the browser and cleanup."""
        if self.driver:
            try:
                self.driver.quit()
                print(">>> Browser closed")
            except Exception as e:
                print(f">>> [Warning] Error closing browser: {e}")
            finally:
                self.driver = None
    
    def get_driver(self):
        """Get the current driver instance."""
        return self.driver
    
    def __enter__(self):
        """Context manager entry - setup browser."""
        return self.setup_browser()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close browser."""
        self.close_browser()
