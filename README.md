# ollama-cup-detector

Local first step for cup recognition using Ollama Gemma vision model.

This stage only includes a local Python test. No ESP32 or Arduino code is included yet.

## Project Structure

```text
ollama-cup-detector/
├── README.md
├── .gitignore
└── local_test/
    ├── test_gemma_cup.py
    ├── requirements.txt
    └── sample_images/
        └── README.md
```

## 1) Install Ollama

Install Ollama from the official site:

- [https://ollama.com/download](https://ollama.com/download)

After install, ensure Ollama is running locally.

## 2) Pull model `gemma4:e2b`

```bash
ollama pull gemma4:e2b
```

If needed, start the server manually:

```bash
ollama serve
```

## 3) Install Python dependencies

From project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r local_test/requirements.txt
```

## 4) Run local cup detection test

Command format:

```bash
python3 local_test/test_gemma_cup.py <image_path>
```

Example:

```bash
python3 local_test/test_gemma_cup.py local_test/sample_images/cup.jpg
```

## 5) Expected output

The script prints:

1. Raw model response (text returned by Gemma)
2. Parsed label:
   - `CUP_DETECTED`
   - `NO_CUP`
   - `UNKNOWN`

Example:

```text
=== RAW MODEL RESPONSE ===
RESULT: YES
CONFIDENCE: 92
REASON: A real mug is visible on the table.

=== PARSED RESULT ===
CUP_DETECTED
```

## Notes

- The script calls Ollama API: `http://localhost:11434/api/generate`
- Model used: `gemma4:e2b`
- It includes error handling for:
  - missing image path
  - image file not found
  - Ollama server unavailable
  - model not found
  - request timeout
