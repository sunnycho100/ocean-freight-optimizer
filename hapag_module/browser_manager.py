"""
Browser management and stealth configuration for Hapag-Lloyd automation.

This module handles browser initialization, stealth mode setup, and 
basic navigation functionality.
"""

import time
from typing import Optional, Dict, Any
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth


class BrowserManager:
    """Manages browser instances and stealth configuration."""
    
    def __init__(self, headless: bool = False):
        """
        Initialize BrowserManager.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.stealth = Stealth()
    
    def launch_browser(self, playwright: Playwright) -> Page:
        """
        Launch browser with stealth configuration.
        
        Args:
            playwright: Playwright instance
            
        Returns:
            Page object ready for automation
        """
        print(f"🌐 Launching browser (headless={self.headless})...")
        
        # Launch browser with slow_mo to appear more human-like
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            slow_mo=100  # 100ms delay between actions to appear human-like
        )
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # Apply stealth mode to avoid detection
        print("🥷 Applying stealth mode...")
        self.stealth.apply_stealth_sync(self.page)
        
        return self.page
    
    def navigate_to_hapag(self, page: Optional[Page] = None) -> None:
        """
        Navigate to Hapag-Lloyd quote page.
        
        Args:
            page: Page instance to use. If None, uses self.page
        """
        if page is None:
            page = self.page
        
        if page is None:
            raise ValueError("No page instance available")
        
        url = "https://www.hapag-lloyd.com/solutions/new-quote/#/simple?language=en"
        print(f"🌐 Navigating to: {url}")
        
        try:
            page.goto(url)
            print("✅ Successfully navigated to Hapag-Lloyd")
        except Exception as e:
            print(f"❌ ERROR navigating to Hapag-Lloyd: {e}")
            raise
    
    def wait_for_page_load(self, page: Optional[Page] = None, timeout: int = 120000) -> bool:
        """
        Wait for Hapag-Lloyd page to load completely.
        
        Args:
            page: Page instance to use. If None, uses self.page
            timeout: Timeout in milliseconds (default 2 minutes for Cloudflare)
            
        Returns:
            True if page loaded successfully, False otherwise
        """
        if page is None:
            page = self.page
        
        if page is None:
            raise ValueError("No page instance available")
        
        print("⏳ Waiting for login page to appear (handle Cloudflare manually if needed)...")
        
        try:
            # Wait for login fields to appear
            page.get_by_role("textbox", name="E-mail Address").wait_for(timeout=timeout)
            time.sleep(1)
            print("✅ Login page loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Login page did not load within {timeout/1000} seconds: {e}")
            return False
    
    def handle_cookie_consent(self, page: Optional[Page] = None) -> bool:
        """
        Handle cookie consent dialog if present.
        
        Args:
            page: Page instance to use. If None, uses self.page
            
        Returns:
            True if consent handled or not needed, False if error
        """
        if page is None:
            page = self.page
        
        if page is None:
            raise ValueError("No page instance available")
        
        try:
            page.get_by_role("button", name="Select All").click()
            time.sleep(0.5)
            print("✅ Cookie consent accepted")
            return True
            
        except Exception:
            print("ℹ️ Cookie consent not required or already accepted")
            return True
    
    def handle_cloudflare_challenge(self, page: Optional[Page] = None, timeout: int = 60000) -> bool:
        """
        Handle Cloudflare challenge/checkbox if present.
        
        Args:
            page: Page instance to use. If None, uses self.page
            timeout: Timeout in milliseconds to wait for challenge
            
        Returns:
            True if challenge handled or not present, False if error
        """
        if page is None:
            page = self.page
        
        if page is None:
            raise ValueError("No page instance available")
        
        print("🔍 Checking for Cloudflare challenge...")
        
        try:
            # Look for Cloudflare challenge iframe
            cf_iframe = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
            
            # Try to find and click the checkbox
            checkbox = cf_iframe.locator("input[type='checkbox']")
            if checkbox.count() > 0:
                print("🤖 Cloudflare challenge detected, attempting to click checkbox...")
                checkbox.first.click()
                time.sleep(3)  # Wait for verification
                print("✅ Cloudflare checkbox clicked")
                return True
            
            # Also try the turnstile checkbox
            turnstile = cf_iframe.locator(".ctp-checkbox-label")
            if turnstile.count() > 0:
                print("🤖 Cloudflare Turnstile detected, attempting to click...")
                turnstile.first.click()
                time.sleep(3)
                print("✅ Cloudflare Turnstile clicked")
                return True
                
        except Exception as e:
            print(f"ℹ️ No Cloudflare challenge found or already passed: {e}")
        
        return True
    
    def get_page(self) -> Optional[Page]:
        """
        Get the current page instance.
        
        Returns:
            Current page instance or None
        """
        return self.page
    
    def close_browser(self) -> None:
        """Close browser and clean up resources."""
        print("🔄 Closing browser...")
        
        try:
            if self.context:
                self.context.close()
                print("✅ Browser context closed")
            
            if self.browser:
                self.browser.close()
                print("✅ Browser closed")
                
        except Exception as e:
            print(f"⚠️ Warning during browser cleanup: {e}")
    
    def keep_browser_open(self) -> None:
        """Keep browser open for manual review."""
        print("\n" + "="*60)
        print("🔍 Browser kept open for review")
        print("="*60)
        input("Press Enter to close browser...")
        
    def restart_page(self) -> Page:
        """
        Create a new page instance (useful for starting fresh searches).
        
        Returns:
            New page instance
        """
        if not self.context:
            raise ValueError("No browser context available")
        
        print("🔄 Creating new page instance...")
        
        if self.page:
            self.page.close()
        
        self.page = self.context.new_page()
        self.stealth.apply_stealth_sync(self.page)
        
        return self.page