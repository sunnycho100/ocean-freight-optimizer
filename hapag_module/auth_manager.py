"""
Authentication management for Hapag-Lloyd login.

This module handles credential loading and login automation.
"""

import os
import time
from typing import Optional
from playwright.sync_api import Page
from dotenv import load_dotenv


class AuthManager:
    """Manages authentication and login for Hapag-Lloyd."""
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize AuthManager.
        
        Args:
            env_file: Path to environment file containing credentials
        """
        self.env_file = env_file
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self._load_credentials()
    
    def _load_credentials(self) -> None:
        """Load credentials from environment variables."""
        # Load environment variables
        load_dotenv(self.env_file)
        
        self.email = os.getenv('HAPAG_EMAIL')
        self.password = os.getenv('HAPAG_PASSWORD')
        
        if not self.email or not self.password:
            print("❌ ERROR: HAPAG_EMAIL and HAPAG_PASSWORD must be set in .env file")
            print("💡 Create a .env file with:")
            print("   HAPAG_EMAIL=your_email@example.com")
            print("   HAPAG_PASSWORD=your_password")
            raise ValueError("Missing credentials in environment variables")
        
        print("✅ Credentials loaded from environment")
    
    def login(self, page: Page) -> bool:
        """
        Perform login to Hapag-Lloyd.
        
        Args:
            page: Page instance to perform login on
            
        Returns:
            True if login successful, False otherwise
        """
        if not self.email or not self.password:
            print("❌ ERROR: No credentials available")
            return False
        
        print("🔐 Logging in to Hapag-Lloyd...")
        
        try:
            # Fill email field
            print("   📧 Entering email...")
            email_field = page.get_by_role("textbox", name="E-mail Address")
            email_field.click()
            email_field.fill(self.email)
            email_field.press("Tab")
            
            # Fill password field
            print("   🔒 Entering password...")
            password_field = page.get_by_role("textbox", name="Password")
            password_field.fill(self.password)
            password_field.press("Enter")
            
            # Wait for redirect back to quote page
            print("⏳ Waiting for quote page to load after login...")
            page.get_by_test_id("start-input").wait_for(timeout=30000)
            time.sleep(2)
            
            print("✅ Login successful!")
            return True
            
        except Exception as e:
            print(f"❌ LOGIN ERROR: {e}")
            return False
    
    def verify_login_status(self, page: Page) -> bool:
        """
        Verify if user is already logged in.
        
        Args:
            page: Page instance to check
            
        Returns:
            True if already logged in, False if login required
        """
        try:
            # Check if we're already on the quote page (logged in)
            start_input = page.get_by_test_id("start-input")
            start_input.wait_for(state="visible", timeout=5000)
            
            print("ℹ️ Already logged in, skipping authentication")
            return True
            
        except:
            print("ℹ️ Login required")
            return False
    
    def get_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get loaded credentials.
        
        Returns:
            Tuple of (email, password)
        """
        return self.email, self.password
    
    def has_credentials(self) -> bool:
        """
        Check if credentials are available.
        
        Returns:
            True if both email and password are available
        """
        return bool(self.email and self.password)