from pathlib import Path

from db.database import SessionLocal
from db.repository import (
    create_transcript_words,
    create_video,
    get_video_by_url,
    has_transcript,
    update_video,
)
from services.audio import extract_audio
from services.downloader import download_video
from services.transcription import transcribe_audio


def process_video(url: str) -> dict:

    with SessionLocal() as session:

        # 1. Find existing video
        video = get_video_by_url(session, url)

        # 2. Create record if this URL is new
        if video is None:
            video = create_video(session, url)

        try:

            output_dir = Path("outputs") / str(video.id)

            # --------------------------------
            # 3. Download video if necessary
            # --------------------------------

            if not video.file_path:

                video = update_video(
                    session,
                    video,
                    status="downloading",
                )

                video_path = download_video(
                    url,
                    output_dir=str(output_dir),
                )

                video = update_video(
                    session,
                    video,
                    status="video_ready",
                    file_path=video_path,
                )

            # --------------------------------
            # 4. Extract audio if necessary
            # --------------------------------

            if not video.audio_path:

                video = update_video(
                    session,
                    video,
                    status="extracting_audio",
                )

                audio_path = extract_audio(
                    video.file_path,
                    output_dir=str(output_dir),
                )

                video = update_video(
                    session,
                    video,
                    status="audio_ready",
                    audio_path=audio_path,
                )

            # --------------------------------
            # 5. Transcribe if necessary
            # --------------------------------

            if not has_transcript(session, video.id):

                video = update_video(
                    session,
                    video,
                    status="transcribing",
                )

                words = transcribe_audio(
                    video.audio_path,
                )

                create_transcript_words(
                    session,
                    video.id,
                    words,
                )

                video = update_video(
                    session,
                    video,
                    status="transcribed",
                )

            # --------------------------------
            # 6. Return result
            # --------------------------------

            return {
                "video_id": str(video.id),
                "url": video.url,
                "status": video.status,
                "file_path": video.file_path,
                "audio_path": video.audio_path,
            }

        except Exception:

            update_video(
                session,
                video,
                status="failed",
            )

            raise
