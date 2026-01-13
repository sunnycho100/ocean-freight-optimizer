"""
Quick Download Package
Modular package for downloading ONE Line Inland Tariff data.

Components:
- config_loader: Configuration and URL management
- browser_manager: Browser lifecycle management
- table_scraper: Data extraction from web pages
- data_processor: Data cleaning and validation
- excel_manager: Excel file operations
- destination_processor: Destination processing orchestration
"""

from .config_loader import ConfigLoader
from .browser_manager import BrowserManager
from .table_scraper import TableScraper
from .data_processor import DataProcessor
from .excel_manager import ExcelManager
from .destination_processor import DestinationProcessor

__all__ = [
    'ConfigLoader',
    'BrowserManager',
    'TableScraper',
    'DataProcessor',
    'ExcelManager',
    'DestinationProcessor',
]

__version__ = '1.0.0'
