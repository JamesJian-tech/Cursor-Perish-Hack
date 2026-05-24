# Freenove ESP32-WROVER camera pin map (OV2640 / OV3660)
# https://docs.freenove.com/projects/fnk0060/en/latest/fnk0060/codes/Python/30_Camera_Web_Server.html

import camera
import gc

# Rough minimum for a valid VGA JPEG from this sensor (well below typical ~15–25 KB)
MIN_JPEG_BYTES = 1000
JPEG_MAGIC = b"\xff\xd8\xff"
DEFAULT_FRAMESIZE = camera.FRAME_VGA

CAMERA_PINS = {
    "d0": 4,
    "d1": 5,
    "d2": 18,
    "d3": 19,
    "d4": 36,
    "d5": 39,
    "d6": 34,
    "d7": 35,
    "href": 23,
    "vsync": 25,
    "reset": -1,
    "pwdn": -1,
    "sioc": 27,
    "siod": 26,
    "xclk": 21,
    "pclk": 22,
}


def deinit_camera():
    try:
        camera.deinit()
    except OSError:
        pass


def init_camera(framesize=None):
    deinit_camera()
    if framesize is None:
        framesize = DEFAULT_FRAMESIZE

    camera.init(
        0,
        d0=CAMERA_PINS["d0"],
        d1=CAMERA_PINS["d1"],
        d2=CAMERA_PINS["d2"],
        d3=CAMERA_PINS["d3"],
        d4=CAMERA_PINS["d4"],
        d5=CAMERA_PINS["d5"],
        d6=CAMERA_PINS["d6"],
        d7=CAMERA_PINS["d7"],
        format=camera.JPEG,
        framesize=framesize,
        xclk_freq=camera.XCLK_20MHz,
        href=CAMERA_PINS["href"],
        vsync=CAMERA_PINS["vsync"],
        reset=CAMERA_PINS["reset"],
        pwdn=CAMERA_PINS["pwdn"],
        sioc=CAMERA_PINS["sioc"],
        siod=CAMERA_PINS["siod"],
        xclk=CAMERA_PINS["xclk"],
        pclk=CAMERA_PINS["pclk"],
        fb_location=camera.PSRAM,
    )

    camera.framesize(framesize)
    camera.flip(1)
    camera.mirror(1)
    camera.saturation(0)
    camera.brightness(0)
    camera.contrast(0)
    camera.quality(10)
    camera.speffect(camera.EFFECT_NONE)
    camera.whitebalance(camera.WB_NONE)
    gc.collect()


def validate_jpeg(buf):
    if not buf or len(buf) < MIN_JPEG_BYTES:
        raise OSError("JPEG too small: %s bytes" % (len(buf) if buf else 0))
    if buf[:3] != JPEG_MAGIC:
        raise OSError("Invalid JPEG header (expected FF D8 FF)")


def capture_jpeg():
    buf = camera.capture()
    validate_jpeg(buf)
    return buf
