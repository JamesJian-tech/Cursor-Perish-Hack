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

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def color(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


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


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def detect_image(image_path: str) -> Dict[str, str]:
    start = time.time()
    payload = {
        "model": MODEL_NAME,
        "prompt": STRICT_PROMPT,
        "images": [image_to_base64(image_path)],
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


def resolve_image_paths(targets: List[str], recursive: bool) -> List[str]:
    image_paths: List[str] = []

    for target in targets:
        path = Path(target)

        if path.is_file():
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                image_paths.append(str(path))
            continue

        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            for candidate in sorted(path.glob(pattern)):
                if candidate.is_file():
                    if candidate.suffix.lower() in IMAGE_EXTENSIONS:
                        image_paths.append(str(candidate))

    # Keep order stable while removing duplicates.
    deduped = list(dict.fromkeys(image_paths))
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a pretty local demo for Gemma cup detection.",
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Image files and/or folders containing images",
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
    args = parser.parse_args()

    missing = [path for path in args.targets if not os.path.exists(path)]
    if missing:
        for path in missing:
            print(color(f"Error: File does not exist: {path}", "31"))
        return 1

    image_paths = resolve_image_paths(args.targets, recursive=args.recursive)
    if not image_paths:
        print(color("Error: No image files found in the given paths.", "31"))
        print("Supported extensions: .jpg .jpeg .png .webp .bmp")
        return 1

    print_header(total=len(image_paths))
    parsed_results: List[str] = []
    failures = 0
    report_items: List[Dict[str, str]] = []

    for idx, image_path in enumerate(image_paths, start=1):
        try:
            result = detect_image(image_path)
            parsed_results.append(result["parsed"])
            report_items.append(
                {
                    "image": image_path,
                    "parsed": result["parsed"],
                    "confidence": result["confidence"],
                    "elapsed": result["elapsed"],
                    "raw": result["raw"],
                }
            )
            print_result(idx, len(image_paths), image_path, result)
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
                    "image": image_path,
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
                    "image": image_path,
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
                    "image": image_path,
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
                    "image": image_path,
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
                    "image": image_path,
                    "parsed": "FAILED",
                    "confidence": "N/A",
                    "elapsed": "N/A",
                    "raw": str(exc),
                }
            )

    print_summary(parsed_results, failures)
    summary = {
        "total": len(image_paths),
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
