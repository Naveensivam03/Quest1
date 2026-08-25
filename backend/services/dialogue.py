from pathlib import Path

from db.database import SessionLocal
from db.models import Video
from db.repository import (
    create_dialogue_match,
    get_transcript,
)
from services.frame import extract_frame
from services.timeline import find_timeline


def find_dialogue(
    video_id,
    target_text: str,
) -> dict | None:

    with SessionLocal() as session:

        video = session.get(Video, video_id)

        if video is None:
            raise ValueError(
                f"Video not found: {video_id}"
            )

        if not video.file_path:
            raise RuntimeError(
                "Video has not been downloaded yet."
            )

        transcript = get_transcript(
            session,
            video.id,
        )

        if not transcript:
            raise RuntimeError(
                "Video has not been transcribed yet."
            )

        timeline = find_timeline(
            target_text,
            transcript,
        )

        if timeline is None:
            return None

        frames_dir = (
            Path(video.file_path).parent / "frames"
        )

        frame = extract_frame(
            video_path=video.file_path,
            timestamp=timeline["start_time"],
            output_dir=str(frames_dir),
        )

        match = create_dialogue_match(
            session=session,
            video_id=video.id,
            query_text=target_text,
            timeline=timeline,
            frame=frame,
        )

        return {
            "match_id": str(match.id),
            "video_id": str(video.id),
            "text": timeline["text"],
            "start_time": timeline["start_time"],
            "end_time": timeline["end_time"],
            "frame_number": frame["frame_number"],
            "frame_timestamp": frame["timestamp"],
            "frame_path": frame["image_path"],
        }
