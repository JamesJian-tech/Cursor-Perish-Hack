#!/usr/bin/env python3
"""Pretty local demo runner for Gemma cup detection."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Dict, List, Optional
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

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def color(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


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
    return "CUP_DETECTED" if match.group(1).upper() == "YES" else "NO_CUP"


def extract_confidence(raw_response: str) -> str:
    match = re.search(
        r"CONFIDENCE:\s*(\d{1,3})",
        raw_response,
        flags=re.IGNORECASE,
    )
    if not match:
        return "N/A"
    return match.group(1)


def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def build_url_candidates(source: str) -> List[str]:
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
                            "Image URL error HTTP "
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

    try:
        with open(source, "rb") as image_file:
            return image_file.read()
    except OSError as exc:
        raise RuntimeError(f"Failed to read image file: {exc}") from exc


def detect_image(source: str) -> Dict[str, str]:
    start = time.time()
    image_bytes = load_image_bytes(source)
    payload = {
        "model": MODEL_NAME,
        "prompt": STRICT_PROMPT,
        "images": [image_bytes_to_base64(image_bytes)],
        "stream": False,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)

    if response.status_code == 404 and MODEL_NAME in response.text:
        raise RuntimeError(
            f"Model not found: {MODEL_NAME}. "
            f"Run: ollama pull {MODEL_NAME}"
        )
    if response.status_code >= 400:
        raise RuntimeError(
            "Ollama API error HTTP "
            f"{response.status_code}: {response.text.strip()}"
        )

    data = response.json()
    raw = data.get("response", "").strip()
    if not raw:
        raise RuntimeError("Ollama response missing `response` content.")

    elapsed = f"{(time.time() - start):.2f}s"
    return {
        "source": source,
        "raw": raw,
        "parsed": classify_response(raw),
        "confidence": extract_confidence(raw),
        "elapsed": elapsed,
    }


def print_header(total: int) -> None:
    print("=" * 68)
    print("OLLAMA GEMMA CUP DETECTION DEMO")
    print(f"Model: {MODEL_NAME}")
    print(f"Endpoint: {OLLAMA_URL}")
    print(f"Images: {total}")
    print("=" * 68)


def print_result(
    index: int,
    total: int,
    image_path: str,
    result: Dict[str, str],
) -> None:
    status = result["parsed"]
    if status == "CUP_DETECTED":
        status_text = color(status, "32")
    elif status == "NO_CUP":
        status_text = color(status, "33")
    else:
        status_text = color(status, "31")

    print(f"\n[{index}/{total}] {image_path}")
    print("-" * 68)
    print(f"Parsed Result : {status_text}")
    print(f"Confidence    : {result['confidence']}")
    print(f"Elapsed       : {result['elapsed']}")
    print("Raw Response  :")
    print(result["raw"])


def print_summary(results: List[str], failures: int) -> None:
    cup_count = sum(1 for item in results if item == "CUP_DETECTED")
    no_cup_count = sum(1 for item in results if item == "NO_CUP")
    unknown_count = sum(1 for item in results if item == "UNKNOWN")
    total = len(results) + failures

    print("\n" + "=" * 68)
    print("SUMMARY")
    print(f"Total images  : {total}")
    print(f"CUP_DETECTED  : {cup_count}")
    print(f"NO_CUP        : {no_cup_count}")
    print(f"UNKNOWN       : {unknown_count}")
    print(f"FAILED        : {failures}")
    print("=" * 68)


def write_reports(
    json_path: Optional[str],
    txt_path: Optional[str],
    report_items: List[Dict[str, str]],
    summary: Dict[str, int],
) -> None:
    if json_path:
        json_payload = {
            "summary": summary,
            "items": report_items,
        }
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(json_payload, file, ensure_ascii=False, indent=2)
        print(f"\nSaved JSON report: {json_path}")

    if txt_path:
        lines = []
        lines.append("OLLAMA GEMMA CUP DETECTION REPORT")
        lines.append("=" * 40)
        lines.append(f"Total images : {summary['total']}")
        lines.append(f"CUP_DETECTED : {summary['cup_detected']}")
        lines.append(f"NO_CUP       : {summary['no_cup']}")
        lines.append(f"UNKNOWN      : {summary['unknown']}")
        lines.append(f"FAILED       : {summary['failed']}")
        lines.append("")
        lines.append("DETAILS")
        lines.append("-" * 40)

        for item in report_items:
            lines.append(f"Image      : {item['image']}")
            lines.append(f"Result     : {item['parsed']}")
            lines.append(f"Confidence : {item['confidence']}")
            lines.append(f"Elapsed    : {item['elapsed']}")
            lines.append(f"Raw        : {item['raw']}")
            lines.append("-" * 40)

        with open(txt_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")
        print(f"Saved TXT report: {txt_path}")


def resolve_image_sources(targets: List[str], recursive: bool) -> List[str]:
    image_sources: List[str] = []

    for target in targets:
        if is_http_source(target):
            image_sources.append(target)
            continue

        path = Path(target)

        if path.is_file():
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                image_sources.append(str(path))
            continue

        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            for candidate in sorted(path.glob(pattern)):
                if candidate.is_file():
                    if candidate.suffix.lower() in IMAGE_EXTENSIONS:
                        image_sources.append(str(candidate))

    # Keep order stable while removing duplicates.
    deduped = list(dict.fromkeys(image_sources))
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a pretty local demo for Gemma cup detection.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Image files/folders and/or image URLs",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan folders recursively",
    )
    parser.add_argument(
        "--save-json",
        help="Save report to JSON file (example: local_test/report.json)",
    )
    parser.add_argument(
        "--save-txt",
        help="Save report to TXT file (example: local_test/report.txt)",
    )
    parser.add_argument(
        "--live-url",
        help="Poll this image URL repeatedly (example: /api/frame/latest)",
    )
    parser.add_argument(
        "--live-interval",
        type=float,
        default=2.0,
        help="Seconds between live polls (default: 2.0)",
    )
    parser.add_argument(
        "--live-count",
        type=int,
        default=10,
        help="How many live frames to test (default: 10)",
    )
    args = parser.parse_args()

    if args.live_url:
        if args.live_count <= 0:
            print(color("Error: --live-count must be > 0", "31"))
            return 1
        if args.live_interval <= 0:
            print(color("Error: --live-interval must be > 0", "31"))
            return 1

        args.targets.extend(
            [f"{args.live_url}#frame-{idx + 1}" for idx in range(args.live_count)]
        )

    if not args.targets:
        print(color("Error: Provide at least one source or --live-url.", "31"))
        return 1

    missing = [
        path
        for path in args.targets
        if (not is_http_source(path)) and (not os.path.exists(path))
    ]
    if missing:
        for path in missing:
            print(color(f"Error: File does not exist: {path}", "31"))
        return 1

    image_sources = resolve_image_sources(args.targets, recursive=args.recursive)
    if not image_sources:
        print(color("Error: No image files found in the given paths.", "31"))
        print("Supported local extensions: .jpg .jpeg .png .webp .bmp")
        print("Or pass image URL(s).")
        return 1

    print_header(total=len(image_sources))
    parsed_results: List[str] = []
    failures = 0
    report_items: List[Dict[str, str]] = []

    for idx, source in enumerate(image_sources, start=1):
        source_for_fetch = source.split("#frame-", 1)[0]
        try:
            result = detect_image(source_for_fetch)
            parsed_results.append(result["parsed"])
            report_items.append(
                {
                    "image": source,
                    "parsed": result["parsed"],
                    "confidence": result["confidence"],
                    "elapsed": result["elapsed"],
                    "raw": result["raw"],
                }
            )
            print_result(idx, len(image_sources), source, result)
            if args.live_url and idx < len(image_sources):
                time.sleep(args.live_interval)
        except requests.exceptions.ConnectionError:
            print(
                color(
                    "\nError: Cannot connect to Ollama at localhost:11434.",
                    "31",
                )
            )
            print("Hint: Start with `ollama serve`.")
            failures += 1
            report_items.append(
                {
                    "image": source,
                    "parsed": "FAILED",
                    "confidence": "N/A",
                    "elapsed": "N/A",
                    "raw": "Cannot connect to Ollama at localhost:11434.",
                }
            )
        except requests.exceptions.Timeout:
            print(
                color(
                    f"\nError: Request timeout after {TIMEOUT_SECONDS}s.",
                    "31",
                )
            )
            failures += 1
            report_items.append(
                {
                    "image": source,
                    "parsed": "FAILED",
                    "confidence": "N/A",
                    "elapsed": "N/A",
                    "raw": f"Request timeout after {TIMEOUT_SECONDS}s.",
                }
            )
        except requests.exceptions.RequestException as exc:
            print(color(f"\nError: Network request failed: {exc}", "31"))
            failures += 1
            report_items.append(
                {
                    "image": source,
                    "parsed": "FAILED",
                    "confidence": "N/A",
                    "elapsed": "N/A",
                    "raw": f"Network request failed: {exc}",
                }
            )
        except ValueError:
            print(color("\nError: Invalid JSON response from Ollama.", "31"))
            failures += 1
            report_items.append(
                {
                    "image": source,
                    "parsed": "FAILED",
                    "confidence": "N/A",
                    "elapsed": "N/A",
                    "raw": "Invalid JSON response from Ollama.",
                }
            )
        except RuntimeError as exc:
            print(color(f"\nError: {exc}", "31"))
            failures += 1
            report_items.append(
                {
                    "image": source,
                    "parsed": "FAILED",
                    "confidence": "N/A",
                    "elapsed": "N/A",
                    "raw": str(exc),
                }
            )

    print_summary(parsed_results, failures)
    summary = {
        "total": len(image_sources),
        "cup_detected": sum(1 for item in parsed_results if item == "CUP_DETECTED"),
        "no_cup": sum(1 for item in parsed_results if item == "NO_CUP"),
        "unknown": sum(1 for item in parsed_results if item == "UNKNOWN"),
        "failed": failures,
    }
    write_reports(
        json_path=args.save_json,
        txt_path=args.save_txt,
        report_items=report_items,
        summary=summary,
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
