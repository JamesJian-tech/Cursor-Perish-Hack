# NomSpot laptop backend (Phase 2–3)

Receives JPEG frames from the ESP32 over WiFi and saves the latest frame as `last_frame.jpg`.

## Setup

```powershell
cd backend
python -m pip install -r requirements.txt
```

## Run

```powershell
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Status (last detection stub): [http://127.0.0.1:8000/api/status](http://127.0.0.1:8000/api/status)
- Frames: `POST /api/frame` with body `Content-Type: image/jpeg`

## ESP32 `wifi_config.py`

1. On the PC, copy `src/esp32/wifi_config.example.py` and edit SSID, password, and `BACKEND_URL`.
2. Find your laptop IP (same WiFi as the board):

   ```powershell
   ipconfig
   ```

   Use the **Wireless LAN adapter** IPv4 address, e.g. `192.168.1.100`.

3. Set:

   ```python
   BACKEND_URL = "http://192.168.1.100:8000/api/frame"
   ```

4. Upload to the board (do not commit `wifi_config.py`):

   ```powershell
   python -m mpremote connect COM4 fs cp src\esp32\wifi_config.py :wifi_config.py
   ```

5. Upload Phase 2 scripts and reset — see `SETUP.md` / `firmware/esp32/README.md`.

When `wifi_config.py` is on the device, `boot.py` runs the upload loop (`main_upload.py`) instead of the Phase 1 smoke test in `main.py`.

## Windows firewall

Allow **Python** or **uvicorn** on **private** networks when Windows Firewall prompts you, or add an inbound rule for TCP port **8000** so the ESP32 can reach the laptop.

## Verify without hardware

```powershell
curl http://127.0.0.1:8000/health
# POST a test image:
curl -X POST http://127.0.0.1:8000/api/frame -H "Content-Type: image/jpeg" --data-binary "@some.jpg"
```

Check `backend/last_frame.jpg` was updated.
