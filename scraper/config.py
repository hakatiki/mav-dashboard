"""
Configuration file for MÁV scraper with common station codes and settings.
"""

# Common MÁV station codes
STATION_CODES = {
    # Major cities
    'budapest_keleti': '005504748',  # Budapest-Keleti (need to find correct code)
    'budapest_deli': '005510009',    # Budapest-Déli
    'keszthely': '005504747',        # Keszthely
    'szeged': '005501024',          # Szeged
    'debrecen': '005504744',        # Debrecen
    'pecs': '005504748',            # Pécs
    'gyor': '005504745',            # Győr
    'miskolc': '005504746',         # Miskolc
    'szolnok': '005504749',         # Szolnok
    
    # Add more station codes as needed
    # You can find these by monitoring the MÁV website network requests
}

# Reverse lookup for station names
STATION_NAMES = {v: k for k, v in STATION_CODES.items()}

# API settings
API_CONFIG = {
    'base_url': 'https://jegy-a.mav.hu/IK_API_PROD/api/OfferRequestApi/GetOfferRequest',
    'timeout': 15,
    'headers': {
        "Content-Type": "application/json; charset=utf-8",
        "UserSessionId": "''"
    }
}

# Default passenger configuration
DEFAULT_PASSENGER = {
    "passengerCount": 1,
    "passengerId": 0,
    "customerTypeKey": "HU_44_025-065",  # Standard adult ticket
    "customerDiscountsKeys": []
}

# Output settings
OUTPUT_CONFIG = {
    'default_dir': 'output',
    'save_raw': True,
    'save_processed': True,
    'display_limit': 10
} 