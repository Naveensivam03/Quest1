from services.ocr import scan_video, find_text


VIDEO = "outputs/8437d81d-a2d8-44e8-a8ae-9a43f029d325/video.mkv"


results = scan_video(
    VIDEO,
    start_time=0,
    end_time=54,
    sample_fps=2,
)

print(f"OCR results: {len(results)}")

for result in results:
    if result.text:
        print(
            f"{result.timestamp:.2f}s -> "
            f"{result.text}"
        )


target = "My mind rebels at stagnation."

match = find_text(
    target,
    results,
)

print("\nTARGET:")
print(target)

print("\nMATCH:")
print(match)
