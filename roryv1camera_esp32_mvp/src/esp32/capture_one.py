# Save one JPEG to /capture.jpg on the device (used by verify_phase1.ps1 on PC).
import gc
import sys

import camera_freenove as cam

OUT_PATH = "/capture.jpg"


def run():
    try:
        cam.init_camera()
        jpeg = cam.capture_jpeg()
        with open(OUT_PATH, "wb") as f:
            f.write(jpeg)
        print("saved", OUT_PATH, len(jpeg), "bytes")
        del jpeg
        gc.collect()
    except Exception as e:
        sys.print_exception(e)
        return False
    finally:
        cam.deinit_camera()
    return True


if __name__ == "__main__":
    run()
