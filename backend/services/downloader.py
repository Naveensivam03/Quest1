from pathlib import Path

import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget


def download_video(
    url: str,
    output_dir: str,
) -> str:

    video_dir = Path(output_dir)
    video_dir.mkdir(parents=True, exist_ok=True)

    options = {
        "outtmpl": str(video_dir / "video.%(ext)s"),
        "impersonate": ImpersonateTarget.from_str("chrome"),
        "retries": 5,
        "socket_timeout": 30,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info)

    return video_path
