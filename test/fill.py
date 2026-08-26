import yt_dlp

from db.database import SessionLocal
from db.models import Video


def get_video_id(url: str) -> str:
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            url,
            download=False,
        )

    return info["id"]


with SessionLocal() as session:
    videos = (
        session.query(Video)
        .filter(Video.external_id.is_(None))
        .all()
    )

    print(f"Found {len(videos)} videos to update.")

    for video in videos:
        try:
            external_id = get_video_id(video.url)

            print(
                f"{video.url} -> {external_id}"
            )

            video.external_id = external_id

        except Exception as exc:
            print(
                f"FAILED: {video.url}\n"
                f"ERROR: {exc}"
            )

    session.commit()

    print("Backfill complete.")
