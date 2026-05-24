# NomSpot ESP32-WROVER — MicroPython runs boot.py then main.py on reset.
# pylint: disable=import-error,no-member,broad-exception-caught,unused-import
import gc
import time

gc.enable()

try:
    import ap_config  # noqa: F401
except ImportError:
    pass
else:
    print("AP mode: ap_config present — local hotspot preview")
    try:
        import main_ap

        main_ap.run()
    except Exception as e:
        import sys

        sys.print_exception(e)
        print("AP mode failed — edit ap_config.py and reset.")
        while True:
            time.sleep(3600)

try:
    import wifi_config  # noqa: F401
except ImportError:
    print("Phase 1: ready (main.py runs next)")
else:
    print("Phase 2: wifi_config present — upload loop (main.py skipped)")
    try:
        import main_upload

        main_upload.run()
    except Exception as e:
        import sys

        sys.print_exception(e)
        print("Phase 2 failed — edit wifi_config.py, start backend, reset.")
        while True:
            time.sleep(3600)
