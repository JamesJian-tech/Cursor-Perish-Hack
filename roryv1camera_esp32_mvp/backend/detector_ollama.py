# Phase 3 placeholder — wire Ollama vision model here later.


def detect_cup(jpeg_bytes: bytes) -> dict:
    """
    Analyze a JPEG frame for cup presence.

    TODO: call Ollama (e.g. llava) with jpeg_bytes and parse JSON response.
    """
    _ = jpeg_bytes
    return {
        "cup_present": None,
        "confidence": None,
        "note": "Ollama detection not wired yet — stub only",
    }
