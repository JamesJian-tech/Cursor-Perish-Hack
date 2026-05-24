# NomSpot ESP32-WROVER — MicroPython runs boot.py then main.py on reset.
# pylint: disable=import-error,no-member,broad-exception-caught,unused-import
import gc
import sys
import time

gc.enable()


def _hold_on_error(exc, message):
    sys.print_exception(exc)
    print(message)
    while True:
        time.sleep(3600)

try:
    import wifi_config  # noqa: F401
except ImportError:
    print("AP mode: start local hotspot preview")
    try:
        import main_ap

        main_ap.run()
    except Exception as e:
        _hold_on_error(e, "AP mode failed — reset board and retry.")
else:
    print("Phase 2: wifi_config present — upload loop (main.py skipped)")
    try:
        import main_upload

        main_upload.run()
    except Exception as e:
        _hold_on_error(e, "Phase 2 failed — edit wifi_config.py, start backend, reset.")
