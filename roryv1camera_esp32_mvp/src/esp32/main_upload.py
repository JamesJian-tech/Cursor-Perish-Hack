# Phase 2 — WiFi connect, capture JPEG, POST to laptop backend.
# Started from boot.py when wifi_config.py exists on the device.
import gc
import sys
import time

import camera_freenove as cam
from upload_client import post_jpeg
from wifi_config import BACKEND_URL, PASSWORD, SSID

try:
    from wifi_config import UPLOAD_INTERVAL_S
except ImportError:
    UPLOAD_INTERVAL_S = 2


def connect_wifi(ssid, password, timeout_s=30):
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("WiFi already connected:", wlan.ifconfig())
        return wlan

    print("Connecting to WiFi:", ssid)
    wlan.connect(ssid, password)
    deadline = time.ticks_add(time.ticks_ms(), timeout_s * 1000)
    while not wlan.isconnected():
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            raise OSError("WiFi connect timeout")
        time.sleep(0.5)
    print("WiFi OK:", wlan.ifconfig())
    return wlan


def run():
    print("NomSpot WiFi JPEG upload")
    connect_wifi(SSID, PASSWORD)

    try:
        cam.init_camera()
        print("Camera init OK - uploading to", BACKEND_URL)
    except Exception as e:
        sys.print_exception(e)
        return

    try:
        while True:
            jpeg = cam.capture_jpeg()
            status = post_jpeg(BACKEND_URL, jpeg)
            print("POST status:", status, "JPEG bytes:", len(jpeg))
            del jpeg
            gc.collect()
            time.sleep(UPLOAD_INTERVAL_S)
    except Exception as e:
        sys.print_exception(e)
    finally:
        cam.deinit_camera()
        print("Upload loop stopped.")
