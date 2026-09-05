"""Constants for the Olimpia Splendid UNICO integration."""

DOMAIN = "olimpia_unico"
PLATFORMS = ["climate", "switch", "sensor"]

CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"

TUYA_VERSION = 3.4

# Stability / recovery settings for the UNICO Wi-Fi module.
DEFAULT_SCAN_INTERVAL = 60  # 60 seconds
SOCKET_TIMEOUT = 8
SOCKET_RETRY_LIMIT = 1  # one real connection attempt, no aggressive retry loop
SOCKET_RETRY_DELAY = 2
RECONNECT_BACKOFF = (45,)  # fixed short backoff; next 60s poll can retry

# Preventive maintenance: once per day, only while the UNICO is known to be off.
DAILY_MAINTENANCE_HOUR = 10
DAILY_MAINTENANCE_MINUTE = 0

DP_POWER = 1
DP_TARGET_TEMP = 2
DP_CURRENT_TEMP = 3
DP_MODE = 4
DP_FAN = 5
DP_ECO = 8
DP_SWING = 15
DP_TEMP_UNIT = 19
DP_ERROR = 22
DP_SILENT = 25
DP_DISPLAY = 36

DP_DIAG_101 = 101
DP_DIAG_102 = 102
DP_DIAG_103 = 103
DP_DIAG_104 = 104
DP_DIAG_105 = 105
DP_DIAG_107 = 107
DP_DIAG_110 = 110
DP_DIAG_111 = 111
DP_DIAG_115 = 115
DP_DIAG_117 = 117

MIN_TEMP = 16
MAX_TEMP = 30

PRESET_NORMAL = "normal"
PRESET_ECO = "eco"
PRESET_SILENT = "silent"
PRESET_ECO_SILENT = "eco_silent"
