# Merging with your model repository

This document is for when you combine **this repo** (ESP32 + HTTP ingest) with **another repo** that already has the vision model.

## What each repo owns

| Repo | Owns |
|------|------|
| **This repo (edge)** | `firmware/esp32/`, `src/esp32/`, `backend/app.py` (HTTP), ingest |
| **Model repo** | Inference code, Ollama prompts, training, business logic |

## Single integration point

Edit **`backend/detector_ollama.py`** in the merged tree:

```python
def detect_cup(jpeg_bytes: bytes) -> dict:
    # Import and call your model from the other repo, e.g.:
    # from your_model.inference import run_vision
    # return run_vision(jpeg_bytes)
    ...
```

`backend/app.py` already calls `detect_cup(body)` on every `POST /api/frame`.

## Runtime layout after merge

1. **Model laptop** runs only: `cd backend && .\start_backend.ps1`
2. **ESP32** posts to `http://<model-laptop-ip>:8000/api/frame` (unchanged)
3. Your model reads `jpeg_bytes` in memory or `backend/last_frame.jpg` on disk

## Folder copy checklist (monorepo)

If you paste into an existing monorepo instead of merging Git history:

- [ ] `firmware/esp32/` — flash tooling
- [ ] `src/esp32/` — device Python
- [ ] `backend/app.py` — keep or merge routes into your API
- [ ] `backend/detector_ollama.py` — replace with your model wrapper
- [ ] `backend/requirements.txt` — merge dependencies
- [ ] Do **not** commit `wifi_config.py` or firmware `.bin`

## ESP32 config after merge

No code change required on the board if:

- `BACKEND_URL` still points to the same host/port/path
- You did not rename `/api/frame`

## Testing the merged stack

1. Model laptop: `.\start_backend.ps1`
2. Browser: `http://127.0.0.1:8000/health`
3. ESP32: WiFi upload running (`POST status: 200`)
4. `GET http://<ip>:8000/api/status` — `detection` should reflect your model, not the stub note
