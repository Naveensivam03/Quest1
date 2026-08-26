"""
Runs under the main project venv (Python 3.14).

Delegates the Paddle-dependent scan to .venv-ocr (Python 3.13)
via subprocess, since paddlepaddle-gpu has no Python 3.14 wheels yet.

Matching logic (find_text etc.) is pure Python and runs here directly.

OCR results are persisted in PostgreSQL so the same video does not
need to be OCR-scanned repeatedly.
"""

import json
import subprocess
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy.orm import Session

from db import repository


@dataclass
class OCRTextBox:
    text: str
    confidence: float
    bbox: list


@dataclass
class OCRFrame:
    frame_number: int
    timestamp: float
    boxes: list[OCRTextBox]
    text: str


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_OCR_PYTHON = _PROJECT_ROOT.parent / ".venv-ocr" / "bin" / "python"
_OCR_WORKER = Path(__file__).parent / "ocr_worker.py"


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _scan_video_with_worker(
    video_path: str,
    start_time: float = 0.0,
    end_time: float | None = None,
    sample_fps: float = 2.0,
) -> list[OCRFrame]:
    if not _OCR_PYTHON.exists():
        raise RuntimeError(
            f"OCR interpreter not found at {_OCR_PYTHON}. "
            "Run: uv venv .venv-ocr --python 3.13 (see setup notes)."
        )

    cmd = [
        str(_OCR_PYTHON),
        str(_OCR_WORKER),
        video_path,
        "--start",
        str(start_time),
        "--fps",
        str(sample_fps),
    ]

    if end_time is not None:
        cmd += [
            "--end",
            str(end_time),
        ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"OCR worker failed: {proc.stderr or proc.stdout}"
        )

    try:
        data = json.loads(
            proc.stdout.strip().splitlines()[-1]
        )
    except (json.JSONDecodeError, IndexError) as e:
        raise RuntimeError(
            f"Could not parse OCR worker output: {proc.stdout!r}"
        ) from e

    if "error" in data:
        raise RuntimeError(
            f"OCR error: {data['error']}"
        )

    frames: list[OCRFrame] = []

    for frame in data.get("frames", []):
        boxes = [
            OCRTextBox(**box)
            for box in frame.get("boxes", [])
        ]

        frames.append(
            OCRFrame(
                frame_number=frame.get("frame_number", round(frame["timestamp"] * 30)),
                timestamp=frame["timestamp"],
                boxes=boxes,
                text=frame.get("text", ""),
            )
        )

    return frames


def _ocr_frames_from_db(
    session: Session,
    video_id,
    start_time: float | None = None,
    end_time: float | None = None,
) -> list[OCRFrame]:
    if start_time is not None:
        results = repository.get_ocr_results_in_range(
            session,
            video_id,
            start_time=start_time,
            end_time=end_time,
        )
    else:
        results = repository.get_ocr_results(
            session,
            video_id,
        )

    return [
        OCRFrame(
            frame_number=result["frame_number"],
            timestamp=result["timestamp"],
            boxes=[],
            text=result["text"],
        )
        for result in results
    ]


def _save_ocr_frames(
    session: Session,
    video_id,
    frames: list[OCRFrame],
) -> None:
    results = [
        {
            "frame_number": frame.frame_number,
            "timestamp": frame.timestamp,
            "text": frame.text,
        }
        for frame in frames
    ]

    repository.create_ocr_results(
        session,
        video_id,
        results,
    )


def scan_video(
    video_path: str,
    start_time: float = 0.0,
    end_time: float | None = None,
    sample_fps: float = 2.0,
    session: Session | None = None,
    video_id=None,
) -> list[OCRFrame]:
    """
    Return OCR results for a video or a timeline range.

    If session and video_id are provided:
      1. Check the DB for OCR results (for range if specified, or whole video).
      2. If cached in DB -> return DB results.
      3. If missing in DB -> run OCR worker, store in DB, return results.

    If session/video_id are not provided:
      Run OCR worker directly.
    """
    if session is not None and video_id is not None:
        is_range_scan = (start_time > 0.0 or end_time is not None)

        if is_range_scan:
            cached_frames = _ocr_frames_from_db(
                session,
                video_id,
                start_time=start_time,
                end_time=end_time,
            )
            if cached_frames:
                print(
                    f"[OCR] Cache HIT in DB for range {start_time:.2f}s -> "
                    f"{f'{end_time:.2f}s' if end_time is not None else 'end'} "
                    f"({len(cached_frames)} frames)"
                )
                return cached_frames

            print(
                f"[OCR] Cache MISS in DB for range {start_time:.2f}s -> "
                f"{f'{end_time:.2f}s' if end_time is not None else 'end'}. "
                f"Running OCR worker at {sample_fps} FPS..."
            )
            frames = _scan_video_with_worker(
                video_path=video_path,
                start_time=start_time,
                end_time=end_time,
                sample_fps=sample_fps,
            )
            _save_ocr_frames(session, video_id, frames)
            return frames
        else:
            if repository.has_ocr_results(session, video_id):
                cached_frames = _ocr_frames_from_db(session, video_id)
                if cached_frames:
                    print(
                        f"[OCR] Cache HIT in DB for whole video "
                        f"({len(cached_frames)} frames)"
                    )
                    return cached_frames

            print(
                f"[OCR] Cache MISS in DB for whole video. "
                f"Running whole-video OCR worker at {sample_fps} FPS..."
            )
            frames = _scan_video_with_worker(
                video_path=video_path,
                start_time=0.0,
                end_time=None,
                sample_fps=sample_fps,
            )
            _save_ocr_frames(session, video_id, frames)
            return frames

    return _scan_video_with_worker(
        video_path=video_path,
        start_time=start_time,
        end_time=end_time,
        sample_fps=sample_fps,
    )


def text_similarity(
    target: str,
    candidate: str,
) -> float:
    target = normalize_text(target)
    candidate = normalize_text(candidate)

    if not target or not candidate:
        return 0.0

    return SequenceMatcher(
        None,
        target,
        candidate,
    ).ratio()


def contains_target(
    target: str,
    candidate: str,
) -> bool:
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
    Exact containment first, then similarity fallback.
    Pure Python — no Paddle dependency.
    """

    for result in results:
        if contains_target(
            target_text,
            result.text,
        ):
            return result

    best_result: OCRFrame | None = None
    best_score = 0.0

    for result in results:
        if not result.text:
            continue

        score = text_similarity(
            target_text,
            result.text,
        )

        if score > best_score:
            best_score = score
            best_result = result

    if best_result is None or best_score < threshold:
        return None

    return best_result
