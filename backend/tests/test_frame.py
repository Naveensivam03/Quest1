# from services.frame import get_video_metadata, extract_frame
#
#
# video_id = "580d895e-32f7-4659-b9d5-437121c0e517"
#
# video_path = f"outputs/{video_id}/video.mkv"
# output_dir = f"outputs/{video_id}/frames"
#
#
# metadata = get_video_metadata(video_path)
#
# print("Video metadata:")
# print(f"FPS:        {metadata['fps']}")
# print(f"Frames:     {metadata['frame_count']}")
# print(f"Resolution: {metadata['width']}x{metadata['height']}")
# print(f"Duration:   {metadata['duration']:.3f}s")
#
#
# result = extract_frame(
#     video_path,
#     timestamp=5.840,
#     output_dir=output_dir,
# )
#
# print("\nFrame extracted:")
# print(f"Frame:      {result['frame_number']}")
# print(f"Timestamp:  {result['timestamp']:.3f}s")
# print(f"Image:      {result['image_path']}")

from services.frame import extract_frame


video_path = (
    "outputs/8437d81d-a2d8-44e8-a8ae-9a43f029d325/video.mkv"
)

result = extract_frame(
    video_path=video_path,
    timestamp=4.4,
    output_dir=(
        "outputs/8437d81d-a2d8-44e8-a8ae-9a43f029d325/frames"
    ),
)

print(f"Frame:     {result['frame_number']}")
print(f"Timestamp: {result['timestamp']:.3f}s")
print(f"FPS:       {result['fps']}")
print(f"Image:     {result['image_path']}")
