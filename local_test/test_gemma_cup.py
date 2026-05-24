#!/usr/bin/env python3
"""Local cup detector using Ollama Gemma vision model."""

import argparse
import base64
import os
import re
from urllib.parse import urlparse, urlunparse

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:e2b"
TIMEOUT_SECONDS = 30
IMAGE_FETCH_RETRIES = 3
MAX_STREAM_SCAN_BYTES = 2_000_000
IMAGE_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/*,*/*;q=0.8",
}
STRICT_PROMPT = """You are a visual object detector.

Check whether the image contains a real physical cup.

Count as YES:
- coffee cup
- mug
- tea cup
- paper cup
- water cup
- cup-shaped drinking container

Count as NO:
- bowl
- plate
- bottle
- can
- jar
- printed picture of a cup

Reply strictly:

RESULT: YES or NO
CONFIDENCE: 0-100
REASON: one short sentence"""


def is_http_source(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def classify_response(raw_response: str) -> str:
    match = re.search(
        r"RESULT:\s*(YES|NO)\b",
        raw_response,
        flags=re.IGNORECASE,
    )
    if not match:
        return "UNKNOWN"

    result = match.group(1).upper()
    if result == "YES":
        return "CUP_DETECTED"
    if result == "NO":
        return "NO_CUP"
    return "UNKNOWN"


def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def build_url_candidates(source: str) -> list[str]:
    parsed = urlparse(source)
    base = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    path = parsed.path or "/"

    candidates = [source]

    if path in ("/", "/stream"):
        candidates.extend(
            [
                f"{base}/snapshot",
                f"{base}/snapshot.jpg",
                f"{base}/api/frame/latest",
            ]
        )

    deduped = list(dict.fromkeys(candidates))
    return deduped


def extract_first_jpeg_from_stream(response: requests.Response) -> bytes:
    buffer = b""
    scanned = 0
    for chunk in response.iter_content(chunk_size=8192):
        if not chunk:
            continue
        buffer += chunk
        scanned += len(chunk)
        if scanned > MAX_STREAM_SCAN_BYTES:
            raise RuntimeError("Stream did not provide JPEG frame in time.")

        start = buffer.find(b"\xff\xd8")
        if start == -1:
            continue
        end = buffer.find(b"\xff\xd9", start + 2)
        if end == -1:
            continue
        return buffer[start : end + 2]

    raise RuntimeError("Unable to extract JPEG frame from stream.")


def load_image_bytes(source: str) -> bytes:
    if is_http_source(source):
        session = requests.Session()
        session.trust_env = False
        last_error: Exception | None = None

        for candidate_url in build_url_candidates(source):
            for attempt in range(IMAGE_FETCH_RETRIES):
                try:
                    response = session.get(
                        candidate_url,
                        timeout=TIMEOUT_SECONDS,
                        headers=IMAGE_FETCH_HEADERS,
                        allow_redirects=True,
                        stream=True,
                    )
                    if response.status_code >= 400:
                        raise RuntimeError(
                            "Image URL returned HTTP "
                            f"{response.status_code}: {candidate_url}"
                        )

                    content_type = response.headers.get("Content-Type", "").lower()
                    if "multipart/" in content_type or "/stream" in candidate_url:
                        image_bytes = extract_first_jpeg_from_stream(response)
                    else:
                        image_bytes = response.content

                    if not image_bytes:
                        raise RuntimeError("Image URL returned empty body.")
                    return image_bytes
                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException,
                    RuntimeError,
                ) as exc:
                    last_error = exc
                    if attempt + 1 < IMAGE_FETCH_RETRIES:
                        continue

        if isinstance(last_error, RuntimeError):
            raise last_error
        if isinstance(last_error, requests.exceptions.Timeout):
            raise RuntimeError(
                f"Image URL request timed out after {TIMEOUT_SECONDS} seconds."
            ) from last_error
        raise RuntimeError(f"Cannot connect to image URL: {source}") from last_error

    if not os.path.isfile(source):
        raise RuntimeError(f"Image file does not exist: {source}")
    try:
        with open(source, "rb") as image_file:
            return image_file.read()
    except OSError as exc:
        raise RuntimeError(f"Failed to read image file: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect cup from local image path or image URL.",
    )
    parser.add_argument(
        "source",
        help=(
            "Local image path OR HTTP/HTTPS URL "
            "(example: http://10.42.90.25:8000/api/frame/latest)"
        ),
    )
    args = parser.parse_args()

    try:
        image_bytes = load_image_bytes(args.source)
        image_b64 = image_bytes_to_base64(image_bytes)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1

    payload = {
        "model": MODEL_NAME,
        "prompt": STRICT_PROMPT,
        "images": [image_b64],
        "stream": False,
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.ConnectionError:
        print(
            "Error: Cannot connect to Ollama server at "
            "http://localhost:11434."
        )
        print("Hint: Start Ollama first (for example, run `ollama serve`).")
        return 1
    except requests.exceptions.Timeout:
        print(f"Error: Request timed out after {TIMEOUT_SECONDS} seconds.")
        return 1
    except requests.exceptions.RequestException as exc:
        print(f"Error: Request to Ollama failed: {exc}")
        return 1

    if response.status_code == 404 and MODEL_NAME in response.text:
        print(f"Error: Model not found: {MODEL_NAME}")
        print(f"Hint: Pull it first with `ollama pull {MODEL_NAME}`.")
        return 1

    if response.status_code >= 400:
        print(f"Error: Ollama API returned HTTP {response.status_code}.")
        print(response.text.strip())
        return 1

    try:
        data = response.json()
    except ValueError:
        print("Error: Ollama API returned invalid JSON.")
        print(response.text.strip())
        return 1

    raw_model_response = data.get("response", "").strip()
    if not raw_model_response:
        print("Error: Ollama API response is missing `response` content.")
        return 1

    parsed_result = classify_response(raw_model_response)

    print("=== RAW MODEL RESPONSE ===")
    print(raw_model_response)
    print()
    print("=== PARSED RESULT ===")
    print(parsed_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
