"""Configuration constants for URL checker"""

# Website URL
BASE_URL = "https://ecomm.one-line.com/one-ecom/prices/rate-tariff/inland-search"

# File paths (will be resolved relative to execution directory)
CONFIG_FILE_NAME = "destination_configs.json"
DESTINATIONS_FILE_NAME = "destinations.txt"

# Timeouts (in seconds)
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 20
DROPDOWN_TIMEOUT = 4
SEARCH_RESULT_TIMEOUT = 30

# Matching thresholds
EXACT_MATCH_SCORE = 1000
NORMALIZED_MATCH_SCORE = 900
ALL_PARTS_MATCH_SCORE = 800
PARTIAL_MATCH_SCORE = 600
FIRST_WORD_MATCH_SCORE = 400
WEAK_MATCH_SCORE = 200
COUNTRY_BONUS_SCORE = 50
MINIMUM_CONFIDENCE_SCORE = 800

# Browser options
BROWSER_MAXIMIZE = True
IGNORE_CERT_ERRORS = True
