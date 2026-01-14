"""
Quote search and price breakdown extraction for Hapag-Lloyd.

This module handles the quote search process, port selection, 
and opening price breakdown dialogs.
"""

import time
from typing import Dict, Any, Optional
from playwright.sync_api import Page


class QuoteScraper:
    """Handles quote searching and price breakdown navigation."""
    
    def __init__(self, origin_port: str = "BUSAN", origin_code: str = "KRPUS"):
        """
        Initialize QuoteScraper.
        
        Args:
            origin_port: Name of origin port (default: BUSAN)
            origin_code: Port code for origin (default: KRPUS)
        """
        self.origin_port = origin_port
        self.origin_code = origin_code
    
    def set_origin_port(self, page: Page, is_first_search: bool = True) -> bool:
        """
        Set the origin port for shipping quote.
        
        Args:
            page: Page instance to interact with
            is_first_search: Whether this is the first search (needs origin entry)
            
        Returns:
            True if origin set successfully, False otherwise
        """
        if not is_first_search:
            print(f"   ℹ️ Keeping origin: {self.origin_port} ({self.origin_code}) from previous search")
            return True
        
        print(f"📍 Entering origin: {self.origin_port} ({self.origin_code})...")
        
        try:
            # Click and fill origin field
            start_input = page.get_by_test_id("start-input")
            start_input.click()
            start_input.fill(self.origin_port.lower())
            time.sleep(2.5)  # Wait for autocomplete dropdown to populate
            
            # Select the correct port - prefer exact code match
            try:
                exact_match = f"{self.origin_port} ({self.origin_code})"
                page.get_by_text(exact_match).click()
                time.sleep(1)
                print(f"✅ Selected exact match: {exact_match}")
                
            except:
                print(f"⚠️ Could not find exact match, using arrow key selection")
                start_input.press("ArrowDown")
                start_input.press("Enter")
                time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR setting origin port: {e}")
            return False
    
    def set_destination_port(self, page: Page, location_code: str, alternate_codes: list = None, is_first_search: bool = True) -> bool:
        """
        Set the destination port for shipping quote with fallback support.
        
        Args:
            page: Page instance to interact with
            location_code: Primary destination port location code
            alternate_codes: List of alternate codes to try if primary fails
            is_first_search: Whether this is the first search
            
        Returns:
            True if destination set successfully, False otherwise
        """
        # Clear destination if this is not the first search
        if not is_first_search:
            try:
                clear_button = page.get_by_test_id("end-column").get_by_role("button", name="Clear")
                clear_button.click()
                time.sleep(0.5)
            except:
                pass  # Clear button not found or not needed
        
        # Build list of codes to try
        codes_to_try = [location_code]
        if alternate_codes:
            codes_to_try.extend(alternate_codes)
        
        # Try each code
        for code in codes_to_try:
            print(f"📍 Trying destination code: {code}...")
            
            try:
                # Click and fill destination field
                end_input = page.get_by_test_id("end-input")
                end_input.click()
                
                # Clear any previous input
                end_input.fill("")
                time.sleep(0.3)
                
                end_input.fill(code.lower())
                time.sleep(1.5)  # Wait for autocomplete dropdown to populate
                
                # Try to click the exact match with location code
                try:
                    exact_match = f"({code})"
                    page.get_by_text(exact_match).first.click()
                    time.sleep(0.5)
                    print(f"✅ Selected destination with code: {code}")
                    return True
                    
                except:
                    print(f"⚠️ WARNING: Could not find exact match for {code}, trying arrow key selection")
                    try:
                        end_input.press("ArrowDown")
                        end_input.press("Enter")
                        time.sleep(0.5)
                        print(f"✅ Selected destination using arrow key for code: {code}")
                        return True
                    except:
                        print(f"❌ Failed to select with code: {code}")
                        continue
                
            except Exception as e:
                print(f"❌ ERROR with code {code}: {e}")
                continue
        
        # All codes failed
        print(f"❌ ERROR: Could not set destination with any of the codes: {codes_to_try}")
        return False
    
    def select_delivery_option(self, page: Page) -> bool:
        """
        Select 'Delivered to your Door' delivery option.
        
        Args:
            page: Page instance to interact with
            
        Returns:
            True if delivery option selected successfully, False otherwise
        """
        print("🚚 Selecting 'Delivered to your Door'...")
        
        try:
            time.sleep(0.5)
            delivery_radio = page.get_by_role("radio", name="Delivered to your Door (")
            delivery_radio.click()
            time.sleep(0.5)
            
            print("✅ Delivery option selected")
            return True
            
        except Exception as e:
            print(f"❌ ERROR selecting delivery option: {e}")
            return False
    
    def search_quotes(self, page: Page) -> bool:
        """
        Submit quote search and wait for results.
        
        Args:
            page: Page instance to interact with
            
        Returns:
            True if search successful and results loaded, False otherwise
        """
        print("🔍 Searching for quotes...")
        
        try:
            # Click search button
            search_button = page.get_by_test_id("search-submit")
            search_button.click()
            
            # Wait for search results to load - use smart waiting for Price Breakdown button
            print("⏳ Waiting for search results and Price Breakdown button...")
            
            # Wait for Price Breakdown button to be visible (up to 60 seconds with retry logic)
            price_breakdown_btn = page.get_by_role("button", name="Price Breakdown").first
            
            # Try multiple approaches to find the button
            try:
                price_breakdown_btn.wait_for(state="visible", timeout=60000)
            except:
                # Fallback: try finding by partial text
                print("   [RETRY] Trying alternative Price Breakdown button selector...")
                time.sleep(3)
                price_breakdown_btn = page.locator("button:has-text('Price Breakdown')").first
                price_breakdown_btn.wait_for(state="visible", timeout=30000)
            
            print("   ✅ Price Breakdown button found!")
            time.sleep(1)  # Brief pause to ensure page is stable
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Search failed or Price Breakdown button did not appear: {e}")
            return False
    
    def open_price_breakdown(self, page: Page) -> bool:
        """
        Open the Price Breakdown dialog.
        
        Args:
            page: Page instance to interact with
            
        Returns:
            True if dialog opened successfully, False otherwise
        """
        print("💰 Opening Price Breakdown...")
        
        try:
            price_breakdown_btn = page.get_by_role("button", name="Price Breakdown").first
            price_breakdown_btn.click()
            time.sleep(3)  # Wait for dialog to fully load
            
            print("✅ Price Breakdown dialog opened")
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Could not open Price Breakdown: {e}")
            return False
    
    def close_price_breakdown(self, page: Page) -> bool:
        """
        Close the Price Breakdown dialog.
        
        Args:
            page: Page instance to interact with
            
        Returns:
            True if dialog closed successfully, False otherwise
        """
        try:
            page.keyboard.press("Escape")
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"⚠️ Warning: Could not close Price Breakdown dialog: {e}")
            return False
    
    def start_new_search(self, page: Page) -> bool:
        """
        Start a new search by clicking the Edit button.
        
        Args:
            page: Page instance to interact with
            
        Returns:
            True if new search started successfully, False otherwise
        """
        print("✏️ Starting new search...")
        
        try:
            # Wait a bit for page to stabilize
            time.sleep(2)
            
            # Click Edit button with retry logic
            edit_button = page.get_by_role("button", name="Edit").first
            
            # First try: direct click
            try:
                edit_button.click(timeout=10000)
            except:
                # Second try: force click
                print("   [RETRY] Forcing click on Edit button...")
                edit_button.click(force=True)
            
            # Click "Edit Search" from dropdown
            edit_search_item = page.get_by_role("listitem").filter(has_text="Edit Search")
            edit_search_item.click()
            time.sleep(1)
            
            print("✅ New search initiated")
            return True
            
        except Exception as e:
            print(f"❌ ERROR starting new search: {e}")
            return False
    
    def extract_route_info(self, page: Page) -> Dict[str, str]:
        """
        Extract route information (From, To, Via) from Price Breakdown dialog.
        
        Args:
            page: Page instance to extract from
            
        Returns:
            Dictionary with keys: from, to, via
        """
        route = {"from": "", "to": "", "via": ""}
        
        print("📍 Extracting route information...")
        
        try:
            # Extract "From" location
            from_text = page.get_by_text("From", exact=True).locator("..").inner_text()
            route["from"] = from_text.replace("From", "").strip()
        except:
            print("   [WARNING] Could not extract 'From' location")
        
        try:
            # Extract "To" location
            to_text = page.get_by_text("To", exact=True).locator("..").inner_text()
            route["to"] = to_text.replace("To", "").strip()
        except:
            print("   [WARNING] Could not extract 'To' location")
        
        try:
            # Extract "via" location
            via_text = page.get_by_text("via").locator("..").inner_text()
            route["via"] = via_text.replace("via", "").strip()
        except:
            print("   [WARNING] Could not extract 'via' location")
        
        print(f"   [ROUTE] From: {route['from']}, To: {route['to']}, Via: {route['via']}")
        return route
    
    def perform_full_search(self, page: Page, location_code: str, is_first_search: bool = True, alternate_codes: list = None) -> bool:
        """
        Perform a complete quote search workflow.
        
        Args:
            page: Page instance to interact with
            location_code: Primary destination port location code
            is_first_search: Whether this is the first search
            alternate_codes: List of alternate codes to try if primary fails
            
        Returns:
            True if complete search workflow successful, False otherwise
        """
        try:
            # Start new search if not first
            if not is_first_search:
                if not self.start_new_search(page):
                    return False
            
            # Set origin port (only for first search)
            if not self.set_origin_port(page, is_first_search):
                return False
            
            # Set destination port (with alternate codes support)
            if not self.set_destination_port(page, location_code, alternate_codes, is_first_search):
                return False
            
            # Select delivery option
            if not self.select_delivery_option(page):
                return False
            
            # Search for quotes
            if not self.search_quotes(page):
                return False
            
            # Open price breakdown
            if not self.open_price_breakdown(page):
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR in full search workflow: {e}")
            return False