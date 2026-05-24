# Phase 1 — ESP32 camera (commit baseline)

Phase 1 proves the Freenove ESP32-WROVER + OV3660 captures valid JPEGs over USB. Phase 2 (WiFi upload) and Phase 3 (Ollama) stay in the repo but are **not** required on the device for this baseline.

## What Phase 1 includes

| Piece | Path |
|-------|------|
| Camera firmware (lemariva / Freenove) | `firmware/esp32/micropython_camera.bin` (gitignored — run `download_firmware.ps1`) |
| Pin map + capture helpers | `src/esp32/camera_freenove.py` |
| Smoke test | `src/esp32/main.py` |
| Single-frame save (verify) | `src/esp32/capture_one.py` |
| Boot | `src/esp32/boot.py` — runs `main.py` unless `wifi_config.py` exists on device |

## One-time PC setup

```powershell
cd firmware\esp32
python -m pip install -r requirements.txt
.\download_firmware.ps1
```

CH340 driver: see `firmware/esp32/README.md`.

## Flash + verify (board on COM port)

```powershell
cd firmware\esp32
.\setup.ps1 -Port COM4
```

Re-upload scripts only (no reflash):

```powershell
.\verify_phase1.ps1 -Port COM4
```

## Success criteria

Serial output after reset or `main.py`:

```
=== NomSpot Phase 1 smoke test ===
Camera init OK
frame 1: JPEG bytes ... (header OK)
...
PASS: 3 frames, <min>–<max> bytes
```

PC file created: `captures/phase1_sample.jpg` (open in an image viewer).

## Then MVP WiFi (Phase 2)

See [MVP.md](MVP.md) — model laptop runs `backend/start_backend.ps1`, then `firmware/esp32/prepare_wifi_config.ps1` + `upload_wifi.ps1`.

## Commit checklist

- [ ] `.\verify_phase1.ps1 -Port COMx` passes
- [ ] `captures/phase1_sample.jpg` looks like a real camera image
- [ ] No `wifi_config.py` committed (gitignored)
- [ ] No `firmware/esp32/*.bin` committed (gitignored)
- [ ] No secrets in `backend/` or `src/esp32/`

Suggested commit message:

```
feat(esp32): Phase 1 camera capture on Freenove WROVER

- lemariva MicroPython camera firmware + Freenove pin map
- smoke test with JPEG validation
- setup/verify scripts and sample capture pull to PC
```

## Phase 2 later

Do **not** upload `wifi_config.py` until the laptop backend is running. See `SETUP.md` and `firmware/esp32/upload_wifi.ps1`.
