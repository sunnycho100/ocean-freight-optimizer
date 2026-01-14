"""
Debug script to check table extraction headers and values.
Run this after logging in and opening a Price Breakdown.
"""

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import re

def normalize_text(text: str) -> str:
    """Normalize extracted text."""
    return text.strip().replace('\n', ' ').replace('\t', ' ')

def debug_table_extraction():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Apply stealth
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        
        # Navigate to Hapag
        page.goto("https://www.hapag-lloyd.com/solutions/new-quote/#/simple?language=en")
        
        print("\n" + "="*60)
        print("MANUAL STEPS REQUIRED:")
        print("1. Log in to Hapag-Lloyd")
        print("2. Search for a destination")
        print("3. Click 'Price Breakdown' on a result")
        print("4. Wait for the breakdown table to load")
        print("5. Press ENTER in this console when ready")
        print("="*60 + "\n")
        
        input("Press ENTER when the Price Breakdown table is visible...")
        
        # Now analyze the tables
        print("\n" + "="*60)
        print("ANALYZING PAGE TABLES...")
        print("="*60 + "\n")
        
        # Find ALL tables on the page
        tables = page.locator("table")
        table_count = tables.count()
        print(f"Found {table_count} tables on the page")
        
        for t_idx in range(table_count):
            table = tables.nth(t_idx)
            print(f"\n--- TABLE {t_idx + 1} ---")
            
            # Get rows in this table
            rows = table.locator("tr")
            row_count = rows.count()
            print(f"  Rows: {row_count}")
            
            for r_idx in range(min(row_count, 10)):  # Check first 10 rows
                row = rows.nth(r_idx)
                
                # Try both th and td cells
                ths = row.locator("th")
                tds = row.locator("td")
                
                th_texts = []
                for i in range(ths.count()):
                    try:
                        th_texts.append(normalize_text(ths.nth(i).inner_text()))
                    except:
                        pass
                
                td_texts = []
                for i in range(tds.count()):
                    try:
                        td_texts.append(normalize_text(tds.nth(i).inner_text()))
                    except:
                        pass
                
                if th_texts:
                    print(f"  Row {r_idx} (TH): {th_texts}")
                if td_texts:
                    print(f"  Row {r_idx} (TD): {td_texts}")
        
        # Also check using get_by_role
        print("\n" + "="*60)
        print("CHECKING WITH get_by_role...")
        print("="*60 + "\n")
        
        rows = page.get_by_role("row")
        row_count = rows.count()
        print(f"Found {row_count} rows using get_by_role")
        
        for r_idx in range(min(row_count, 30)):
            row = rows.nth(r_idx)
            cells = row.get_by_role("cell")
            cell_count = cells.count()
            
            if cell_count < 2:
                continue
            
            cell_texts = []
            for i in range(cell_count):
                try:
                    cell_texts.append(normalize_text(cells.nth(i).inner_text()))
                except:
                    cell_texts.append("")
            
            # Check if this might be a header row
            has_curr = "Curr." in cell_texts or "Currency" in cell_texts
            has_container = any(re.match(r'\d+[A-Z]+', t) for t in cell_texts)
            
            marker = ""
            if has_curr:
                marker += " [HAS CURR]"
            if has_container:
                marker += " [HAS CONTAINER COLS]"
            
            print(f"Row {r_idx} ({cell_count} cells){marker}: {cell_texts[:6]}...")
        
        # Check for specific patterns
        print("\n" + "="*60)
        print("LOOKING FOR SPECIFIC HEADER PATTERNS...")
        print("="*60 + "\n")
        
        # Try to find 20STD header
        headers_20std = page.locator("th:has-text('20STD'), td:has-text('20STD')")
        print(f"Elements with '20STD': {headers_20std.count()}")
        
        headers_40std = page.locator("th:has-text('40STD'), td:has-text('40STD')")
        print(f"Elements with '40STD': {headers_40std.count()}")
        
        headers_40hc = page.locator("th:has-text('40HC'), td:has-text('40HC')")
        print(f"Elements with '40HC': {headers_40hc.count()}")
        
        # Try columnheader role
        print("\n" + "="*60)
        print("CHECKING COLUMN HEADERS...")
        print("="*60 + "\n")
        
        col_headers = page.get_by_role("columnheader")
        ch_count = col_headers.count()
        print(f"Found {ch_count} column headers")
        
        for i in range(ch_count):
            try:
                text = normalize_text(col_headers.nth(i).inner_text())
                print(f"  Column header {i}: '{text}'")
            except:
                pass
        
        print("\n" + "="*60)
        print("DEBUG COMPLETE - Review the output above")
        print("="*60 + "\n")
        
        input("Press ENTER to close browser...")
        
        context.close()
        browser.close()

if __name__ == "__main__":
    debug_table_extraction()
