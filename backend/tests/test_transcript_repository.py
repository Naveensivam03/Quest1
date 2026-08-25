from db.database import SessionLocal
from db.repository import (
    create_transcript_words,
    get_video_by_url,
)
from services.transcription import transcribe_audio


VIDEO_URL = "https://youtu.be/abckzfkg4zI?si=vHwAWbKlfq_2eLWE"

AUDIO_PATH = (
    "outputs/8437d81d-a2d8-44e8-a8ae-9a43f029d325/audio.wav"
)


with SessionLocal() as session:

    video = get_video_by_url(
        session,
        VIDEO_URL,
    )

    if video is None:
        raise RuntimeError("Video not found in database")

    words = transcribe_audio(AUDIO_PATH)

    create_transcript_words(
        session,
        video.id,
        words,
    )

    print(f"Stored {len(words)} words.")
