"""
Hapag-Lloyd Quote Extraction Module

A modular package for automating Hapag-Lloyd shipping quote extraction,
including login automation, price breakdown scraping, and Excel export.

Components:
- config_loader: Configuration and destination management
- browser_manager: Browser automation and stealth setup
- auth_manager: Login and authentication handling
- quote_scraper: Quote search and price breakdown extraction
- data_extractor: Import surcharges table parsing
- excel_exporter: Excel file management and data export
- main_runner: Main automation workflow
"""

__version__ = "1.0.0"
__author__ = "Automation Team"

from .config_loader import ConfigLoader
from .browser_manager import BrowserManager
from .auth_manager import AuthManager
from .quote_scraper import QuoteScraper
from .data_extractor import DataExtractor
from .excel_exporter import ExcelExporter
from .main_runner import MainRunner

__all__ = [
    "ConfigLoader",
    "BrowserManager", 
    "AuthManager",
    "QuoteScraper",
    "DataExtractor",
    "ExcelExporter",
    "MainRunner"
]