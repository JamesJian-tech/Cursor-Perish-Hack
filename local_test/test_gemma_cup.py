#!/usr/bin/env python3
"""Local cup detector using Ollama Gemma vision model."""

import base64
import os
import re
import sys

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:e2b"
TIMEOUT_SECONDS = 30
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


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("Error: Missing image path.")
        print("Usage: python3 local_test/test_gemma_cup.py <image_path>")
        return 1

    image_path = sys.argv[1]
    if not os.path.isfile(image_path):
        print(f"Error: Image file does not exist: {image_path}")
        return 1

    try:
        image_b64 = image_to_base64(image_path)
    except OSError as exc:
        print(f"Error: Failed to read image file: {exc}")
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
