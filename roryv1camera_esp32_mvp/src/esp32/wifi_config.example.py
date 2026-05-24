# Copy to wifi_config.py OR run: firmware\esp32\prepare_wifi_config.ps1
# Do not commit wifi_config.py.
#
# BACKEND_URL = IP of the MODEL laptop (not 127.0.0.1), same WiFi as ESP32.
# On model laptop: cd backend && .\start_backend.ps1

SSID = "YOUR_WIFI_NAME"
PASSWORD = "YOUR_WIFI_PASSWORD"

# Model laptop LAN IP (from ipconfig on that machine)
BACKEND_URL = "http://192.168.1.100:8000/api/frame"

# Seconds between captures (optional; default 2 in main_upload.py)
UPLOAD_INTERVAL_S = 2
