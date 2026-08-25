from services.dialogue import find_dialogue


VIDEO_ID = "8437d81d-a2d8-44e8-a8ae-9a43f029d325"

TARGET = "Give me problems"


result = find_dialogue(
    video_id=VIDEO_ID,
    target_text=TARGET,
)

if result is None:
    print("Dialogue not found.")

else:
    print("Dialogue found!")
    print(
        f"Text:       {result['text']}"
    )
    print(
        f"Start:      {result['start_time']:.3f}s"
    )
    print(
        f"End:        {result['end_time']:.3f}s"
    )
    print(
        f"Frame:      {result['frame_number']}"
    )
    print(
        f"Frame time: {result['frame_timestamp']:.3f}s"
    )
    print(
        f"Image:      {result['frame_path']}"
    )
