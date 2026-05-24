# NomSpot ESP32-WROVER — MicroPython runs boot.py then main.py on reset.
import gc
import time

gc.enable()

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
