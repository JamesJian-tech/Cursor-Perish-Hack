"""Recover ESP32 when Phase 2 boot loop blocks mpremote soft-reset."""
import subprocess
import sys
import time
from pathlib import Path

import serial

PORT = "COM4"
ROOT = Path(__file__).resolve().parents[2] / "src" / "esp32"


def raw_exec(ser, code, wait=1.0):
    ser.reset_input_buffer()
    ser.write(b"\x01")
    time.sleep(0.15)
    ser.read(4096)
    ser.write(code.encode())
    ser.write(b"\x04")
    time.sleep(wait)
    out = ser.read(65536)
    text = out.decode("utf-8", "replace")
    print(text)
    return text


def main():
    ser = serial.Serial(PORT, 115200, timeout=0.5)
    for _ in range(10):
        ser.write(b"\x03")
        time.sleep(0.2)
    time.sleep(0.5)
    print("--- break ---")
    print(ser.read(4096).decode("utf-8", "replace"))

    raw_exec(
        ser,
        "import os\n"
        "try:\n"
        "    os.remove('wifi_config.py')\n"
        "    print('removed wifi_config')\n"
        "except OSError as e:\n"
        "    print('remove failed', e)\n",
    )
    time.sleep(0.5)
    raw_exec(ser, "import machine\nmachine.reset()\n", wait=2)
    ser.close()
    time.sleep(3)

    for name in ("boot.py", "upload_client.py", "main_upload.py", "wifi_config.py"):
        path = ROOT / name
        print("Uploading", name)
        subprocess.run(
            [sys.executable, "-m", "mpremote", "connect", PORT, "fs", "cp", str(path), f":{name}"],
            check=True,
        )

    subprocess.run([sys.executable, "-m", "mpremote", "connect", PORT, "reset"], check=True)


if __name__ == "__main__":
    main()
