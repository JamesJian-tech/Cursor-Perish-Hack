# ESP32-WROVER camera firmware (MicroPython)

Freenove ESP32-WROVER with OV3660 needs **camera-enabled** MicroPython (stock builds have no `camera` module).

## Phase 1 quick start (board plugged in via USB)

```powershell
cd firmware\esp32
python -m pip install -r requirements.txt
.\download_firmware.ps1   # skip if micropython_camera.bin already exists
.\setup.ps1               # flash + Phase 1 verify (see PHASE1.md)
```

If auto-detect fails: `.\setup.ps1 -Port COM4` (check Device Manager for **USB-SERIAL CH340**).

Re-verify without reflashing:

```powershell
.\verify_phase1.ps1 -Port COM4
```

Expected serial output:

```
=== NomSpot Phase 1 smoke test ===
Camera init OK
frame 1: JPEG bytes ... (header OK)
PASS: 3 frames, ...
```

Sample image on PC: `captures/phase1_sample.jpg`.

## Phase 2 ? WiFi upload (after Phase 1 works)

1. Laptop: `cd backend` ? `python -m pip install -r requirements.txt` ?  
   `python -m uvicorn app:app --host 0.0.0.0 --port 8000`
2. Copy `src/esp32/wifi_config.example.py` ? `wifi_config.py` (SSID, password, `BACKEND_URL` with laptop IP from `ipconfig`).
3. Upload:

```powershell
.\upload.ps1 -Port COM4
python -m mpremote connect COM4 fs cp ..\..\src\esp32\wifi_config.py :wifi_config.py
python -m mpremote connect COM4 reset
```

`upload.ps1` copies `boot.py`, `camera_freenove.py`, `main.py`, `upload_client.py`, `main_upload.py`.  
With `wifi_config.py` on the device, `boot.py` runs the upload loop (blocks before `main.py`).

## 1. Install tools

```powershell
cd firmware\esp32
python -m pip install -r requirements.txt
```

If the board does not show a COM port, see **[CH340 driver](#ch340-driver-usb-serial)** below.


## CH340 driver (USB serial)

The Freenove ESP32-WROVER uses a **WCH CH340** USB-to-serial chip. Windows 10/11 may not assign a COM port until the driver is installed.

**Official source (used here):** [WCH CH341SER release on GitHub](https://github.com/WCH-IC/download/releases/tag/CH341) ? direct EXE: [CH341SER.EXE](https://github.com/WCH-IC/download/releases/download/CH341/CH341SER.EXE) (covers CH340 and CH341). Manufacturer pages: [wch-ic.com](https://www.wch-ic.com/downloads/CH341SER_EXE.html) / [wch.cn](https://www.wch.cn/downloads/CH341SER_EXE.html).

A copy is kept at `firmware/esp32/drivers/CH341SER.EXE` for offline install.

**Install (admin):**

```powershell
cd firmware\esp32\drivers
Start-Process .\CH341SER.EXE -ArgumentList '/S' -Verb RunAs -Wait
```

Or run the EXE from the WCH site and click through the wizard. Plug in the board with a **data** USB cable, then check **Device Manager** ? **Ports (COM & LPT)** for **USB-SERIAL CH340 (COMx)**.

**Verify in PowerShell:**

```powershell
[System.IO.Ports.SerialPort]::getportnames()
Get-CimInstance Win32_SerialPort | Select-Object DeviceID, Name
```

Then from `firmware\esp32`: `.\setup.ps1` (or `.\setup.ps1 -Port COMx`).

## 2. Firmware binary

Download **Path A** (Freenove / lemariva):

- [micropython-camera-driver releases / firmware folder](https://github.com/lemariva/micropython-camera-driver/tree/master/firmware)
- File: `micropython_camera_feeeb5ea3_esp32_idf4_4.bin` (or newer ESP32 build from that repo)

Save as:

```
firmware/esp32/micropython_camera.bin
```

**Path B** (only if capture fails on OV3660): [cnadler86/micropython-camera-API](https://github.com/cnadler86/micropython-camera-API/releases) v0.6.0, ESP32 + SPIRAM asset.

## 3. Flash

```powershell
python -m mpremote connect list
.\flash.ps1 -Port COM4
```

Press **RST** on the board if `esptool` cannot connect.

## 4. Upload scripts

```powershell
.\upload.ps1 -Port COM4
```

Or manually from repo root:

```powershell
python -m mpremote connect COM4 fs cp src/esp32/boot.py :
python -m mpremote connect COM4 fs cp src/esp32/camera_freenove.py :
python -m mpremote connect COM4 fs cp src/esp32/main.py :
python -m mpremote connect COM4 fs cp src/esp32/upload_client.py :
python -m mpremote connect COM4 fs cp src/esp32/main_upload.py :
python -m mpremote connect COM4 reset
```

## 5. Verify Phase 1

Open serial REPL (`python -m mpremote connect COM4`) or watch output after reset. Expect:

```
Camera init OK
JPEG bytes: <non-zero>
```

## 5b. Verify Phase 2

With backend running and `wifi_config.py` on the board:

```
WiFi OK: ('192.168.x.x', ...)
Camera init OK ? uploading to http://...
POST status: 200 JPEG bytes: ...
```

Check `backend/last_frame.jpg` on the laptop.

## AP mode preview (ESP32 hotspot)

No router or backend required.

```powershell
.\prepare_ap_config.ps1
.\upload_ap.ps1 -Port COM4
```

Connect to ESP32 SSID (default `NomSpot-Cam`) and open:

```text
http://192.168.4.1/
```
