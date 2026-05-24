"""NomSpot laptop backend — receive JPEG frames from ESP32."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from detector_ollama import detect_cup

APP_DIR = Path(__file__).resolve().parent
FRAME_PATH = APP_DIR / "last_frame.jpg"

app = FastAPI(title="NomSpot backend", version="0.1.0")

_last_detection: dict = detect_cup(b"")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def api_status():
    return {
        "has_frame": FRAME_PATH.is_file(),
        "frame_bytes": FRAME_PATH.stat().st_size if FRAME_PATH.is_file() else 0,
        "detection": _last_detection,
    }


@app.post("/api/frame")
async def api_frame(request: Request):
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")

    FRAME_PATH.write_bytes(body)

    global _last_detection
    _last_detection = detect_cup(body)

    return JSONResponse(
        {
            "ok": True,
            "bytes": len(body),
            "saved": str(FRAME_PATH.name),
            "detection": _last_detection,
        }
    )
