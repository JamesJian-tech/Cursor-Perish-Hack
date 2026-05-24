# NomSpot ESP32 camera — agent guide

## What this project is

Freenove **ESP32-WROVER** + **OV3660** camera running **MicroPython** with the `camera` module. **Phase 1:** flash camera firmware, upload scripts, confirm JPEG capture on serial. **Phase 2:** WiFi POST to laptop `backend/app.py`. **Phase 3:** `backend/detector_ollama.py` stub (wire Ollama later).

## Phase 1 (commit baseline)

See [PHASE1.md](PHASE1.md). Board on USB as **CH340 (COMx)**:

```powershell
cd firmware\esp32
python -m pip install -r requirements.txt
.\download_firmware.ps1    # if micropython_camera.bin missing
.\setup.ps1 -Port COM4       # flash + verify → captures/phase1_sample.jpg
.\verify_phase1.ps1 -Port COM4   # re-verify without reflash
```

Phase 1 upload uses `upload_phase1.ps1` only (`boot.py`, `camera_freenove.py`, `main.py`, `capture_one.py`). Full `upload.ps1` adds Phase 2 scripts.

## Required artifacts (do not use stock micropython.org ESP32 firmware)

| Item | Path |
|------|------|
| Camera firmware (~1.4 MB) | `firmware/esp32/micropython_camera.bin` (lemariva / Freenove Path A) |
| PC tools | `esptool`, `mpremote` via `firmware/esp32/requirements.txt` |
| On-device code | `src/esp32/camera_freenove.py`, `main.py`, `boot.py`, `main_upload.py`, `upload_client.py` |
| WiFi template | `src/esp32/wifi_config.example.py` → copy to `wifi_config.py` on device (not in git) |
| Laptop backend | `backend/app.py`, `backend/requirements.txt` — `uvicorn app:app --host 0.0.0.0 --port 8000` |
| Cup detection stub | `backend/detector_ollama.py` — placeholder until Ollama wired |

**No extra Python `lib/` on the ESP32** for Phase 1 or WiFi upload. Optional MJPEG stream needs Freenove `lib/picoweb` (`picoweb_stream.example.py`, not bundled).

When `wifi_config.py` exists on the device, `boot.py` calls `main_upload.run()` (blocks; Phase 1 `main.py` does not run).

## ESP32 boot / camera checklist

1. **USB cable** — data-capable, connected to the board’s USB port (not only power).
2. **Driver** — CH340 installed; Device Manager shows **Ports (COM & LPT)** → `USB-SERIAL CH340 (COMx)`.
3. **Firmware** — camera-enabled `.bin` flashed at offset **0x1000** (not vanilla MicroPython).
4. **After flash** — press **RST** once; do **not** hold GPIO0 to GND (download mode only if `esptool` fails).
5. **Camera ribbon** — OV3660 flex cable fully seated.
6. **Serial test** — after reset, console shows `Camera init OK` and `JPEG bytes: <non-zero>`.

## Pin map (Freenove — do not change without docs)

Encoded in `src/esp32/camera_freenove.py`: `fb_location=camera.PSRAM`, VGA JPEG, pins d0–d7, href, vsync, sioc/siod, xclk, pclk per Freenove tutorial.

## If smoke test fails (OV3660)

1. Reseat camera, RST, retry `.\setup.ps1 -Port COMx`.
2. Path B: flash [cnadler86/micropython-camera-API](https://github.com/cnadler86/micropython-camera-API) **v0.6.0** ESP32+SPIRAM build; keep same Freenove pins in init.

## Agent constraints

- Use `python -m esptool` and `python -m mpremote` (Scripts folder may not be on PATH).
- Do not edit `.cursor/plans/*.plan.md` unless the user asks.
- Do not commit `firmware/esp32/*.bin` (gitignored).
