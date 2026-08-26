# backend/services/ocr_worker.py
"""
Runs ONLY under .venv-ocr (Python 3.13) — this is the only file that imports
paddleocr/cv2. Invoked as a subprocess by services/ocr.py (main 3.14 venv).

Usage:
    .venv-ocr/bin/python services/ocr_worker.py <video_path> \
        [--start 0.0] [--end 10.0] [--fps 2.0]

Prints ONE JSON line to stdout (last line of output):
    {"frames": [{"timestamp": 1.0, "text": "...", "boxes": [...]}]}
or on failure:
    {"error": "..."}
"""
from paddleocr import PaddleOCR
import cv2
import os
import sys
import json
import argparse

# keep Paddle/PaddleX logging off stdout so it doesn't corrupt our JSON line
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("FLAGS_call_stack_level", "0")


_ocr: "PaddleOCR | None" = None


def get_ocr() -> PaddleOCR:
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(
            lang="en",
            device="gpu",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
    return _ocr


def box_position(box: list) -> tuple[float, float]:
    x1, y1, _, _ = box
    return float(y1), float(x1)


def sort_boxes(boxes: list[dict]) -> list[dict]:
    return sorted(boxes, key=lambda b: box_position(b["bbox"]))


def build_frame_text(boxes: list[dict]) -> str:
    boxes = sort_boxes(boxes)
    return " ".join(b["text"].strip() for b in boxes if b["text"].strip())


def _get_result_data(result) -> dict:
    if hasattr(result, "json"):
        data = result.json
        if isinstance(data, dict):
            return data
    if isinstance(result, dict):
        return result
    raise TypeError(f"Unsupported PaddleOCR result type: {type(result)!r}")


def extract_ocr_frame(paddle_result, timestamp: float) -> dict:
    boxes: list[dict] = []

    for result in paddle_result:
        data = _get_result_data(result)
        if "res" in data:
            data = data["res"]

        texts = data.get("rec_texts", [])
        scores = data.get("rec_scores", [])
        rec_boxes = data.get("rec_boxes", [])

        for text, score, box in zip(texts, scores, rec_boxes):
            text = str(text).strip()
            if not text:
                continue
            if hasattr(box, "tolist"):
                box = box.tolist()
            boxes.append(
                {"text": text, "confidence": float(score), "bbox": box})

    boxes = sort_boxes(boxes)

    return {
        "timestamp": timestamp,
        "boxes": boxes,
        "text": build_frame_text(boxes),
    }


def scan_video(
    video_path: str,
    start_time: float = 0.0,
    end_time: float | None = None,
    sample_fps: float = 2.0,
) -> list[dict]:
    if sample_fps <= 0:
        raise ValueError("sample_fps must be greater than zero.")

    ocr = get_ocr()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        cap.release()
        raise RuntimeError("Unable to determine video FPS.")

    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps

    if end_time is None:
        end_time = duration

    start_time = max(0.0, start_time)
    end_time = min(end_time, duration)

    if start_time > end_time:
        cap.release()
        return []

    interval = 1.0 / sample_fps
    timestamp = start_time
    results: list[dict] = []

    while timestamp <= end_time:
        frame_number = round(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = cap.read()

        if not success:
            timestamp += interval
            continue

        h, w = frame.shape[:2]
        max_dim = 1920
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            frame = cv2.resize(
                frame,
                (
                    int(w * scale),
                    int(h * scale),
                ),
            )

        paddle_result = ocr.predict(frame)
        results.append(extract_ocr_frame(paddle_result, timestamp))
        timestamp += interval

    cap.release()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float, default=None)
    parser.add_argument("--fps", type=float, default=2.0)
    args = parser.parse_args()

    try:
        frames = scan_video(
            args.video_path,
            start_time=args.start,
            end_time=args.end,
            sample_fps=args.fps,
        )
        print(json.dumps({"frames": frames}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
