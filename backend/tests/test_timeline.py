# from services.timeline import find_timeline
# from services.transcription import transcribe_audio
#
#
# video_id = "580d895e-32f7-4659-b9d5-437121c0e517"
#
# audio_path = f"outputs/{video_id}/audio.wav"
#
# transcript = transcribe_audio(audio_path)
#
# target = "Give me problems"
#
# result = find_timeline(target, transcript)
#
# if result:
#     print("Match found!")
#     print(f"Text: {result['text']}")
#     print(f"Start: {result['start_time']:.3f}s")
#     print(f"End:   {result['end_time']:.3f}s")
#     print("Words:")
#
#     for word in result["matched_words"]:
#         print(
#             f"  {word['word']} "
#             f"[{word['start']:.3f} → {word['end']:.3f}]"
#         )
# else:
#     print("No match found.")
from db.database import SessionLocal
from db.repository import (
    get_transcript,
    get_video_by_url,
)
from services.timeline import find_timeline


VIDEO_URL = (
    "https://youtu.be/abckzfkg4zI?si=vHwAWbKlfq_2eLWE"
)

# TARGET = "Give me problems"
TARGET = "my mind rebels at stagnation"

with SessionLocal() as session:

    video = get_video_by_url(
        session,
        VIDEO_URL,
    )

    if video is None:
        raise RuntimeError("Video not found")

    transcript = get_transcript(
        session,
        video.id,
    )

    result = find_timeline(
        TARGET,
        transcript,
    )

    if result is None:
        print("No match found.")
    else:
        print("Match found!")
        print(
            f"Text: {result['text']}"
        )
        print(
            f"Start: {result['start_time']:.3f}s"
        )
        print(
            f"End: {result['end_time']:.3f}s"
        )

        print("Words:")

        for word in result["matched_words"]:
            print(
                f"  {word['word']} "
                f"[{word['start']:.3f} → "
                f"{word['end']:.3f}]"
            )
#
