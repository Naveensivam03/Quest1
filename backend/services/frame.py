from pathlib import Path

import cv2


def get_video_metadata(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    duration = frame_count / fps if fps > 0 else 0

    cap.release()

    return {
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration": duration,
    }


def extract_frame(
    video_path: str,
    timestamp: float,
    output_dir: str,
) -> dict:

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        cap.release()
        raise RuntimeError("Unable to determine video FPS.")

    frame_number = round(timestamp * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    success, frame = cap.read()

    if not success:
        cap.release()
        raise RuntimeError(
            f"Unable to read frame {frame_number}"
        )

    frame_path = output / f"frame_{frame_number}.jpg"

    cv2.imwrite(str(frame_path), frame)

    actual_frame_number = int(
        cap.get(cv2.CAP_PROP_POS_FRAMES)
    ) - 1

    actual_timestamp = actual_frame_number / fps

    cap.release()

    return {
        "frame_number": actual_frame_number,
        "timestamp": actual_timestamp,
        "image_path": str(frame_path),
        "fps": fps,
    }
