# Phase 1 smoke test — validates camera init and JPEG capture on serial.
import gc
import sys

import camera_freenove as cam

NUM_FRAMES = 3


def run():
    print("=== NomSpot Phase 1 smoke test ===")
    failed = False

    try:
        cam.init_camera()
        print("Camera init OK")
    except Exception as e:
        sys.print_exception(e)
        print("FAIL: camera init")
        return False

    sizes = []
    try:
        for i in range(NUM_FRAMES):
            jpeg = cam.capture_jpeg()
            n = len(jpeg)
            sizes.append(n)
            print("frame %d: JPEG bytes %d (header OK)" % (i + 1, n))
            del jpeg
            gc.collect()
    except Exception as e:
        sys.print_exception(e)
        failed = True
    finally:
        cam.deinit_camera()

    if failed or not sizes:
        print("FAIL: capture")
        return False

    if min(sizes) < cam.MIN_JPEG_BYTES:
        print("FAIL: frame too small")
        return False

    print("PASS: %d frames, %d–%d bytes" % (len(sizes), min(sizes), max(sizes)))
    return True


if __name__ == "__main__":
    ok = run()
    print("Done." if ok else "Done with errors.")
