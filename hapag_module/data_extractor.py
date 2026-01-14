"""
Data extraction module for Import Surcharges table parsing.

This module handles the extraction of Import Surcharges table data
from Hapag-Lloyd price breakdown dialogs with dynamic header parsing.
"""

import re
import time
from typing import List, Dict, Any, Tuple
from playwright.sync_api import Page


class DataExtractor:
    """Handles extraction of Import Surcharges table data."""
    
    def __init__(self):
        """Initialize DataExtractor."""
        pass
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text by removing extra whitespace.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        return re.sub(r"\s+", " ", (text or "").strip())
    
    def _split_first_cell(self, text: str) -> Tuple[str, str]:
        """
        Split first cell into description and remarks.
        
        Args:
            text: Cell text to split
            
        Returns:
            Tuple of (description, remarks)
        """
        lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
        
        if not lines:
            return "", ""
        if len(lines) == 1:
            return lines[0], ""
        
        return lines[0], " ".join(lines[1:])
    
    def _find_header_row(self, rows) -> Tuple[Dict[int, str], int]:
        """
        Find header row and build column mapping.
        
        Args:
            rows: Playwright row elements
            
        Returns:
            Tuple of (header_map, header_row_index)
        """
        header_map = {}
        header_row_index = -1
        row_count = rows.count()
        
        # Check first 20 rows for header
        for i in range(min(row_count, 20)):
            try:
                r = rows.nth(i)
                cells = r.get_by_role("cell")
                
                if cells.count() < 3:
                    continue
                
                # Get all cell texts
                cell_texts = []
                for j in range(cells.count()):
                    try:
                        cell_text = self._normalize_text(cells.nth(j).inner_text())
                        cell_texts.append(cell_text)
                    except:
                        cell_texts.append("")
                
                # Look for currency column as header indicator
                if "Curr." in cell_texts or "Currency" in cell_texts:
                    header_row_index = i
                    for j, text in enumerate(cell_texts):
                        header_map[j] = text
                    
                    print(f"   [INFO] Found header row at index {i}")
                    print(f"   [INFO] Header columns: {header_map}")
                    break
                    
            except Exception as e:
                print(f"   [WARNING] Error checking row {i} for header: {e}")
                continue
        
        return header_map, header_row_index
    
    def _identify_container_columns(self, header_map: Dict[int, str]) -> Dict[int, str]:
        """
        Identify container type columns (20STD, 40STD, 40HC, etc.).
        
        Args:
            header_map: Mapping of column index to header name
            
        Returns:
            Dictionary mapping column index to container type
        """
        container_columns = {}
        
        for idx, col_name in header_map.items():
            # Match pattern like "20STD", "40STD", "40HC", "45HC"
            if re.match(r'\d+[A-Z]+', col_name):
                container_columns[idx] = col_name
        
        print(f"   [INFO] Container columns found: {container_columns}")
        return container_columns
    
    def _find_currency_column(self, header_map: Dict[int, str]) -> int:
        """
        Find currency column index.
        
        Args:
            header_map: Mapping of column index to header name
            
        Returns:
            Index of currency column, or None if not found
        """
        for idx, col_name in header_map.items():
            if "Curr" in col_name or col_name == "Currency":
                return idx
        return None
    
    def _extract_row_data(self, row, desc_idx: int, curr_idx: int, 
                         container_columns: Dict[int, str], header_row_index: int, 
                         row_index: int) -> Dict[str, Any]:
        """
        Extract data from a single table row.
        
        Args:
            row: Playwright row element
            desc_idx: Index of description column
            curr_idx: Index of currency column
            container_columns: Mapping of container column indices
            header_row_index: Index of header row
            row_index: Current row index
            
        Returns:
            Dictionary of extracted row data, or None if row should be skipped
        """
        if row_index == header_row_index:
            return None  # Skip header row
        
        try:
            cells = row.get_by_role("cell")
            cell_count = cells.count()
            
            if cell_count < 3:
                return None
            
            # Extract description and remarks from first cell
            try:
                first_cell_text = cells.nth(desc_idx).inner_text()
                desc, remarks = self._split_first_cell(first_cell_text)
            except:
                desc, remarks = "", ""
            
            # Filter out header-like rows
            skip_values = ["Import Surcharges", "Export Surcharges", "Description", 
                          "Curr.", "40STD", "40HC", "20STD", ""]
            if desc in skip_values:
                return None
            
            # Extract currency
            curr = ""
            if curr_idx is not None and curr_idx < cell_count:
                try:
                    curr = self._normalize_text(cells.nth(curr_idx).inner_text())
                except:
                    pass
            
            # Extract container values dynamically
            container_values = {}
            for col_idx, col_name in sorted(container_columns.items()):
                if col_idx < cell_count:
                    try:
                        value = self._normalize_text(cells.nth(col_idx).inner_text())
                        container_values[col_name] = value
                        print(f"      [COL {col_idx}] {col_name} = {value}")
                    except:
                        container_values[col_name] = ""
            
            if desc:  # Only return if we have a description
                return {
                    "description": desc,
                    "curr": curr,
                    "container_values": container_values,
                    "remarks": remarks
                }
            
        except Exception as e:
            print(f"   [WARNING] Error extracting row {row_index}: {e}")
        
        return None
    
    def extract_import_surcharges_table(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract Import Surcharges table data using dynamic header parsing.
        Works with any combination of container types (20STD, 40STD, 40HC, etc.)
        
        Args:
            page: Page instance containing the table
            
        Returns:
            List of dictionaries with extracted table data
        """
        print("📊 Extracting Import Surcharges table...")
        print("   [INFO] Using dynamic header parsing...")
        
        # Wait until at least one known row is present
        try:
            page.get_by_role("cell", name="Terminal Handling Charge Dest.").wait_for(timeout=30000)
            print("   [INFO] Table loaded successfully")
        except Exception as e:
            print(f"   [WARNING] Timeout waiting for table: {e}")
        
        # Find all rows
        rows = page.get_by_role("row")
        row_count = rows.count()
        print(f"   [INFO] Found {row_count} rows")
        
        if row_count == 0:
            # Fallback: try finding <tr> elements directly
            rows = page.locator("tr")
            row_count = rows.count()
            print(f"   [INFO] Fallback: Found {row_count} <tr> rows")
        
        # Step 1: Find header row and build column map
        header_map, header_row_index = self._find_header_row(rows)
        
        if not header_map:
            print("   [WARNING] No header row found, using position-based extraction")
            # Fallback: assume standard structure
            header_map = {0: "Description", 1: "Curr.", 2: "40STD", 3: "40HC"}
        
        # Step 2: Identify container type columns
        container_columns = self._identify_container_columns(header_map)
        
        # Step 3: Find currency column index and description column
        curr_idx = self._find_currency_column(header_map)
        desc_idx = 0  # Usually first column
        
        # Step 4: Extract data rows
        data = []
        extracted_count = 0
        
        for i in range(row_count):
            try:
                r = rows.nth(i)
                row_data = self._extract_row_data(
                    r, desc_idx, curr_idx, container_columns, header_row_index, i
                )
                
                if row_data:
                    data.append(row_data)
                    extracted_count += 1
                    print(f"   [EXTRACTED] {row_data['description']}: {row_data['curr']} "
                          f"{row_data['container_values']} | Remarks: {row_data['remarks'] or 'N/A'}")
                    
            except Exception as e:
                print(f"   [ERROR] Failed to process row {i}: {e}")
                continue
        
        if not data:
            print("   [ERROR] No data successfully extracted")
        else:
            print(f"   [SUCCESS] ✅ Extracted {extracted_count} rows from Import Surcharges")
        
        return data
    
    def validate_extracted_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Validate extracted data for completeness.
        
        Args:
            data: List of extracted data dictionaries
            
        Returns:
            True if data appears valid, False otherwise
        """
        if not data:
            print("   [VALIDATION] ❌ No data to validate")
            return False
        
        valid_rows = 0
        for item in data:
            if (item.get("description") and 
                item.get("container_values") and 
                len(item["container_values"]) > 0):
                valid_rows += 1
        
        validation_passed = valid_rows > 0
        
        if validation_passed:
            print(f"   [VALIDATION] ✅ {valid_rows}/{len(data)} rows have valid data")
        else:
            print(f"   [VALIDATION] ❌ No rows contain valid data")
        
        return validation_passed