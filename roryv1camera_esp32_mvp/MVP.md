# NomSpot MVP — camera on ESP32, model on another laptop

Two machines:

| Machine | Role |
|---------|------|
| **ESP32** | Captures JPEG every few seconds, POSTs over WiFi |
| **Model laptop** | Runs `backend/` (receives `last_frame.jpg`; Ollama later) |
| **Dev PC** (optional) | USB once to flash Phase 1 + upload `wifi_config.py` |

Both ESP32 and model laptop must use the **same WiFi**.

---

## A. Finish Phase 1 (USB, once)

```powershell
cd firmware\esp32
.\test_phase1.ps1 -Port COM4
```

Success: `PASS: 3 frames` and `captures\phase1_sample.jpg` opens as a real photo.

If COM port busy: close Thonny/serial tools, unplug USB, replug, press RST.

---

## B. Model laptop — receive photos

On the **laptop that will run the model**:

```powershell
cd backend
python -m pip install -r requirements.txt
.\start_backend.ps1
```

Note the IP printed (e.g. `192.168.1.50`). Allow Python through Windows Firewall for **private** networks, port **8000**.

Test in a browser on that laptop: `http://127.0.0.1:8000/health`

---

## C. WiFi config + upload to ESP32 (USB on dev PC)

On the PC with the ESP32 plugged in:

```powershell
cd firmware\esp32
.\prepare_wifi_config.ps1
# Enter WiFi name, password, and the MODEL laptop IP from step B

.\upload_wifi.ps1 -Port COM4
```

Unplug USB. Power ESP32 from USB power; it should connect to WiFi and POST frames.

Check model laptop: `backend\last_frame.jpg` updates every ~2 s.

Serial debug (optional): `python -m mpremote connect COM4`

---

## D. Model (later)

`backend/detector_ollama.py` is a stub. Install Ollama on the model laptop and wire vision when ready.

`GET http://<model-ip>:8000/api/status` shows last frame size and detection placeholder.

---

## Optional: ESP32 AP preview (no router/backend)

If you only want direct preview from ESP32:

```powershell
cd firmware\esp32
.\prepare_ap_config.ps1
.\upload_ap.ps1 -Port COM4
```

Then connect laptop/phone to ESP32 WiFi and open `http://192.168.4.1/`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `POST status: None` | Wrong `BACKEND_URL` IP, firewall, or backend not running |
| WiFi timeout | Wrong SSID/password; 2.4 GHz WiFi often works better for ESP32 |
| Phase 1 FAIL | Reseat camera ribbon; run `.\setup.ps1 -Port COM4` |
| COM port busy | Close other serial apps |
