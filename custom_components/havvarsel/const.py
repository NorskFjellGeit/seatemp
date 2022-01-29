from datetime import timedelta

# Base component constants
NAME = "Havvarsel"
DOMAIN = "havvarsel"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by https://havvarsel.no"
ISSUE_URL = "https://github.com/NorskFjellGeit/seatemp/issues"

PER_MILLE_UNIT = "‰"

# Icons
ICON = "mdi:pool"

# Device classes

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

# Defaults
DEFAULT_NAME = DOMAIN

# Other

SCAN_INTERVAL = timedelta(hours=2)
