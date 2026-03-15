"""
Hapag-Lloyd Quote Checker - Modular Version

This is the main entry point that uses the hapag_module package
for automated Hapag-Lloyd shipping quote extraction.

The script has been refactored into a modular structure for:
- Better maintainability
- Code reusability  
- Easier testing
- Cleaner separation of concerns

Usage:
    python hapag_checker.py

Requirements:
    - .env file with HAPAG_EMAIL and HAPAG_PASSWORD
    - destinations.txt file with destination names
    - destination_configs.json with location codes
"""

from hapag_module import MainRunner


def main():
    """Main entry point for Hapag-Lloyd automation."""
    
    # Initialize and run automation
    # Set headless=True to run without browser UI
    # keep_browser_open=False avoids a manual "Press Enter" blocker at the end.
    runner = MainRunner(headless=False, keep_browser_open=False)
    
    # Print configuration stats
    stats = runner.get_stats()
    print(f"📊 Configuration Summary:")
    print(f"   • Destinations to process: {stats['total_destinations']}")
    print(f"   • Excel output file: {stats['excel_filename']}")  
    print(f"   • Headless mode: {stats['headless_mode']}")
    print(f"   • Downloads directory: {stats['downloads_dir']}")
    print(f"   • Credentials available: {stats['has_credentials']}")
    print()
    
    # Run the automation
    success = runner.run_standalone()
    
    if success:
        print("🎉 Automation completed successfully!")
        return 0
    else:
        print("❌ Automation failed!")
        return 1


if __name__ == "__main__":
    exit(main())
