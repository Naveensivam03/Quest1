import cv2
from paddleocr import PaddleOCR

VIDEO_PATH = "video.mkv"

# ocr = PaddleOCR(
#     lang="en",
# )
ocr = PaddleOCR(
    lang="en",
    device="gpu",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError(f"Could not open video: {VIDEO_PATH}")

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = frame_count / fps if fps else 0

print(f"FPS: {fps}")
print(f"Frames: {frame_count}")
print(f"Duration: {duration:.2f}s")
print()

sample_every_seconds = 1.0
frame_interval = max(1, int(fps * sample_every_seconds))

frame_number = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    if frame_number % frame_interval == 0:
        timestamp = frame_number / fps

        print(f"\n--- {timestamp:.2f}s ---")

        result = ocr.predict(frame)

        for res in result:
            res.print()

    frame_number += 1

cap.release()
