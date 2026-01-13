"""
Table Scraping Module
Handles extraction of data from the Inland Tariff table on the web page.
"""

import time
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TableScraper:
    """Scrapes table data from the ONE Line Inland Tariff page."""
    
    def __init__(self, driver, error_folder=None):
        """
        Initialize the table scraper.
        
        Args:
            driver: Selenium WebDriver instance
            error_folder: Directory for error screenshots (defaults to ./scraping_errors)
        """
        self.driver = driver
        self.error_folder = error_folder or os.path.join(os.getcwd(), "scraping_errors")
        
        # Ensure error folder exists
        if not os.path.exists(self.error_folder):
            os.makedirs(self.error_folder)
    
    def scrape_inland_tariff_table(self):
        """
        Scrape all data from the Inland Tariff (DOOR) table on the page.
        
        Returns:
            dict: Contains 'headers', 'data', and 'totalCount' keys
                  'data' is a list of dictionaries with the table data
        """
        print("\n>>> [SCRAPING] Extracting table data from page...")
        
        try:
            # Wait for table to be visible
            table_container = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//table | //div[contains(@class, 'table')] | //div[@role='table']"
                ))
            )
            print("   [Info] Table container found!")
            
            # Scroll to ensure all rows are loaded (for lazy loading)
            self._scroll_page()
            
            # Give table time to fully populate
            time.sleep(3)
            
            # Extract table data using JavaScript - TARGET ONLY INLAND TARIFF (DOOR)
            table_data = self._extract_table_data_js()
            
            print(f"   [Success] Found {len(table_data['data'])} rows")
            print(f"   [Info] Headers: {table_data['headers']}")
            
            if len(table_data['data']) > 0:
                print(f"   [Sample] First row: {list(table_data['data'][0].values())[:3]}...")
                print(f"   [Sample] Last row: {list(table_data['data'][-1].values())[:3]}...")
            
            return table_data
            
        except Exception as e:
            print(f"   [ERROR] Failed to scrape table: {e}")
            self._save_error_screenshot("SCRAPE_FAILED")
            
            # Fallback: try to get visible text data
            return self._fallback_text_extraction()
    
    def _scroll_page(self):
        """Scroll the page to ensure all content is loaded."""
        try:
            # Scroll down to make sure all rows are loaded
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception as e:
            print(f"   [Warning] Scroll error: {e}")
    
    def _extract_table_data_js(self):
        """
        Extract table data using JavaScript.
        Targets specifically the Inland Tariff (DOOR) section.
        
        Returns:
            dict: Contains headers, data, and totalCount
        """
        table_data = self.driver.execute_script("""
            var data = [];
            var headers = [];
            
            // Find all sections on the page
            var allSections = document.querySelectorAll('div, section');
            var inlandSection = null;
            
            // Look for the section containing "Inland Tariff (DOOR)"
            for (var i = 0; i < allSections.length; i++) {
                var sectionText = allSections[i].textContent;
                // Look for Inland Tariff (DOOR) but NOT Arbitrary Tariff (CY)
                if (sectionText.includes('Inland Tariff') && sectionText.includes('DOOR')) {
                    // Make sure this section doesn't contain "Arbitrary Tariff"
                    if (!sectionText.includes('Arbitrary Tariff')) {
                        inlandSection = allSections[i];
                        console.log('Found Inland Tariff (DOOR) section');
                        break;
                    }
                }
            }
            
            // Fallback: Look for section headers
            if (!inlandSection) {
                var allHeaders = document.querySelectorAll('h1, h2, h3, h4, h5, h6, strong, b, .title, .header, [class*="title"], [class*="header"]');
                for (var i = 0; i < allHeaders.length; i++) {
                    var headerText = allHeaders[i].textContent.trim();
                    if ((headerText.includes('Inland Tariff') || headerText.includes('DOOR')) && 
                        !headerText.includes('Arbitrary') && !headerText.includes('CY)')) {
                        console.log('Found Inland Tariff header:', headerText);
                        // Get parent section/div
                        var parent = allHeaders[i].parentElement;
                        while (parent && parent.querySelectorAll('table').length === 0) {
                            parent = parent.parentElement;
                        }
                        if (parent) {
                            inlandSection = parent;
                            break;
                        }
                    }
                }
            }
            
            if (!inlandSection) {
                console.error('Could not find Inland Tariff (DOOR) section');
                return {headers: [], data: [], error: 'Inland Tariff section not found'};
            }
            
            // Find the table within the Inland section only
            var inlandTable = inlandSection.querySelector('table');
            
            if (!inlandTable) {
                console.error('No table found in Inland Tariff section');
                return {headers: [], data: [], error: 'No table in Inland Tariff section'};
            }
            
            console.log('Found Inland Tariff table');
            
            // Extract headers from the table
            var headerCells = inlandTable.querySelectorAll('thead th, thead td');
            if (headerCells.length === 0) {
                // Try first row
                var firstRow = inlandTable.querySelector('tr');
                if (firstRow) {
                    headerCells = firstRow.querySelectorAll('th, td');
                }
            }
            
            headerCells.forEach(function(cell) {
                headers.push(cell.textContent.trim());
            });
            
            console.log('Headers:', headers);
            
            // Extract data rows (skip header row)
            var rows = inlandTable.querySelectorAll('tbody tr');
            if (rows.length === 0) {
                // If no tbody, get all rows and skip the first (header) row
                var allRows = inlandTable.querySelectorAll('tr');
                rows = Array.from(allRows).slice(1);
            }
            
            console.log('Data rows found:', rows.length);
            
            // Look for "Total: X results" text in the Inland Tariff section
            var totalText = '';
            var totalCount = 0;
            var totalElements = inlandSection.querySelectorAll('*');
            for (var i = 0; i < totalElements.length; i++) {
                var elemText = totalElements[i].textContent.trim();
                // Look for "Total: X results" pattern (case insensitive)
                if (elemText.match(/Total:\\s*\\d+\\s*results?/i)) {
                    totalText = elemText;
                    // Extract just the number
                    var match = elemText.match(/Total:\\s*(\\d+)\\s*results?/i);
                    if (match) {
                        totalCount = parseInt(match[1]);
                        console.log('Found total count:', totalCount);
                    }
                    break;
                }
            }
            
            rows.forEach(function(row) {
                var cells = row.querySelectorAll('td');
                if (cells.length === 0) return; // Skip if no td cells (probably a header row)
                
                var rowData = {};
                var hasData = false;
                
                cells.forEach(function(cell, cellIndex) {
                    var header = headers[cellIndex] || 'Column_' + cellIndex;
                    var value = cell.textContent.trim();
                    rowData[header] = value;
                    if (value) hasData = true;
                });
                
                // Only add row if it has actual data and is not a header
                if (hasData && !rowData[headers[0]]?.includes('Container Type')) {
                    data.push(rowData);
                }
            });
            
            console.log('Final data rows:', data.length);
            return {headers: headers, data: data, totalCount: totalCount};
        """)
        
        return table_data
    
    def _save_error_screenshot(self, prefix="ERROR"):
        """Save a screenshot when an error occurs."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.error_folder, f"{prefix}_{timestamp}.png")
            self.driver.save_screenshot(screenshot_path)
            print(f"   [ERROR] Screenshot saved: {screenshot_path}")
        except Exception as screenshot_err:
            print(f"   [WARNING] Could not save screenshot: {screenshot_err}")
    
    def _fallback_text_extraction(self):
        """Fallback method to extract visible text if table scraping fails."""
        try:
            print("   [Fallback] Attempting to extract visible text...")
            all_text = self.driver.find_element(By.TAG_NAME, "body").text
            print(f"   [Debug] Page text length: {len(all_text)} characters")
            return {"headers": ["Raw_Data"], "data": [{"Raw_Data": all_text[:5000]}], "totalCount": 0}
        except:
            return {"headers": [], "data": [], "totalCount": 0}
