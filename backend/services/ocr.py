# backend/services/ocr.py
"""
Runs under the main project venv (Python 3.14).
Delegates the Paddle-dependent scan to .venv-ocr (Python 3.13) via subprocess,
since paddlepaddle-gpu has no Python 3.14 wheels yet.
Matching logic (find_text etc.) is pure Python and runs here directly.
"""
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class OCRTextBox:
    text: str
    confidence: float
    bbox: list


@dataclass
class OCRFrame:
    timestamp: float
    boxes: list[OCRTextBox]
    text: str


_PROJECT_ROOT = Path(__file__).resolve().parents[1]  # backend/
_OCR_PYTHON = _PROJECT_ROOT.parent / ".venv-ocr" / "bin" / "python"
_OCR_WORKER = Path(__file__).parent / "ocr_worker.py"


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def scan_video(
    video_path: str,
    start_time: float = 0.0,
    end_time: float | None = None,
    sample_fps: float = 2.0,
) -> list[OCRFrame]:
    """
    Same signature/behavior as before, but delegates the actual OCR work
    to .venv-ocr via subprocess.
    """
    if not _OCR_PYTHON.exists():
        raise RuntimeError(
            f"OCR interpreter not found at {_OCR_PYTHON}. "
            "Run: uv venv .venv-ocr --python 3.13 (see setup notes)."
        )

    cmd = [
        str(_OCR_PYTHON),
        str(_OCR_WORKER),
        video_path,
        "--start", str(start_time),
        "--fps", str(sample_fps),
    ]
    if end_time is not None:
        cmd += ["--end", str(end_time)]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if proc.returncode != 0:
        raise RuntimeError(f"OCR worker failed: {proc.stderr or proc.stdout}")

    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as e:
        raise RuntimeError(f"Could not parse OCR worker output: {
                           proc.stdout!r}") from e

    if "error" in data:
        raise RuntimeError(f"OCR error: {data['error']}")

    frames: list[OCRFrame] = []
    for f in data["frames"]:
        boxes = [OCRTextBox(**b) for b in f["boxes"]]
        frames.append(
            OCRFrame(timestamp=f["timestamp"], boxes=boxes, text=f["text"]))

    return frames


def text_similarity(target: str, candidate: str) -> float:
    target = normalize_text(target)
    candidate = normalize_text(candidate)
    if not target or not candidate:
        return 0.0
    return SequenceMatcher(None, target, candidate).ratio()


def contains_target(target: str, candidate: str) -> bool:
    target = normalize_text(target)
    candidate = normalize_text(candidate)
    if not target or not candidate:
        return False
    return target in candidate


def find_text(
    target_text: str,
    results: list[OCRFrame],
    threshold: float = 0.80,
) -> OCRFrame | None:
    """
    Unchanged from your original: exact containment first, then similarity fallback.
    Pure Python — no Paddle dependency, runs directly in the main process.
    """
    for result in results:
        if contains_target(target_text, result.text):
            return result

    best_result: OCRFrame | None = None
    best_score = 0.0

    for result in results:
        if not result.text:
            continue
        score = text_similarity(target_text, result.text)
        if score > best_score:
            best_score = score
            best_result = result

    if best_result is None or best_score < threshold:
        return None

    return best_result
