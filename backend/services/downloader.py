# from pathlib import Path
#
# import yt_dlp
# from yt_dlp.networking.impersonate import ImpersonateTarget
#
#
# def download_video(
#     url: str,
#     output_dir: str,
# ) -> str:
#
#     video_dir = Path(output_dir)
#     video_dir.mkdir(parents=True, exist_ok=True)
#
#     options = {
#         "outtmpl": str(video_dir / "video.%(ext)s"),
#         "impersonate": ImpersonateTarget.from_str("chrome"),
#         "retries": 5,
#         "socket_timeout": 30,
#     }
#
#     with yt_dlp.YoutubeDL(options) as ydl:
#         info = ydl.extract_info(url, download=True)
#         video_path = ydl.prepare_filename(info)
#
#     return video_path
#
# # from pathlib import Path
# #
# # import yt_dlp
# # from yt_dlp.networking.impersonate import ImpersonateTarget
# #
# #
# # def download_video(
# #     url: str,
# #     output_dir: str,
# # ) -> str:
# #
# #     video_dir = Path(output_dir)
# #     video_dir.mkdir(parents=True, exist_ok=True)
# #
# #     options = {
# #         "format": (
# #             "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio/"
# #             "best[ext=mp4][vcodec^=avc1]/"
# #             "best"
# #         ),
# #         "merge_output_format": "mp4",
# #
# #         "outtmpl": str(video_dir / "video.%(ext)s"),
# #
# #         "impersonate": ImpersonateTarget.from_str("chrome"),
# #
# #         "retries": 5,
# #         "socket_timeout": 30,
# #     }
# #
# #     with yt_dlp.YoutubeDL(options) as ydl:
# #         info = ydl.extract_info(
# #             url,
# #             download=True,
# #         )
# #
# #         video_path = ydl.prepare_filename(info)
# #
# #         # yt-dlp may merge the selected video/audio streams
# #         # into MP4, so make sure we return the actual path.
# #         if not Path(video_path).exists():
# #             possible_path = video_dir / "video.mp4"
# #
# #             if possible_path.exists():
# #                 video_path = str(possible_path)
# #             else:
# #                 raise RuntimeError(
# #                     f"Downloaded video not found: {video_path}"
# #                 )
# #
# #     return video_path

from pathlib import Path
import subprocess
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget


def get_video_codec(video_path: str) -> str | None:
    """
    Return the video codec using ffprobe.
    """
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    codec = result.stdout.strip()
    return codec or None


def normalize_video(
    input_path: str,
    output_path: str,
) -> str:
    """
    Convert video to H.264 while preserving the original
    resolution and frame rate.
    """
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]
    subprocess.run(
        command,
        check=True,
    )
    return output_path


def _build_ydl_options(
    video_dir: Path,
    use_impersonate: bool,
    cookies_file: str | None,
) -> dict:
    """
    Build yt-dlp options.

    Notes on the choices below:

    - format: "bv*+ba/best" instead of plain "best".
      "best" restricts yt-dlp to formats that already contain
      both video AND audio muxed together. Many sites (ok.ru,
      YouTube's higher-res streams, etc.) only serve separate
      video-only and audio-only tracks at their best quality,
      so "best" silently falls back to a low-quality combined
      format or fails to find anything at all. "bv*+ba" tells
      yt-dlp to grab the best video-only + best audio-only
      streams and mux them (needs ffmpeg, which we already use).
      The "/best" is a fallback for sites that only ever expose
      pre-muxed formats.

    - format_sort prefers avc1 (H.264) over vp9/av1 so we avoid
      unnecessary re-encoding when a H.264 option exists at the
      same resolution. This does not guarantee H.264 (some
      Shorts/4K-only streams are AV1-only), so normalize_video()
      is still the safety net.

    - impersonate is now toggleable. Some non-YouTube sites
      (ok.ru is one of them) can behave worse when a browser
      impersonation profile is forced, so we retry without it
      if the first attempt fails.

    - cookies_file lets you pass a cookies.txt for sites that
      gate content behind a login/region check (ok.ru sometimes
      does this for certain videos).
    """
    options = {
        "format": "bv*+ba/best",
        "format_sort": ["res", "fps", "codec:avc1", "codec:h264"],
        "outtmpl": str(video_dir / "video.%(ext)s"),
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
        "merge_output_format": "mp4",
        "noplaylist": True,
    }
    if use_impersonate:
        options["impersonate"] = ImpersonateTarget.from_str("chrome")
    if cookies_file:
        options["cookiefile"] = cookies_file
    return options


def download_video(
    url: str,
    output_dir: str,
    cookies_file: str | None = None,
) -> str:
    """
    Download a video from any yt-dlp-supported URL
    (YouTube, YouTube Shorts, ok.ru, etc.), then make sure
    the result is H.264 for downstream compatibility.
    """
    video_dir = Path(output_dir)
    video_dir.mkdir(parents=True, exist_ok=True)

    info = None
    last_error = None

    # Try with impersonation first, then without it. Some sites
    # (ok.ru in particular) can 403 or return an empty format
    # list when a Chrome impersonation profile is forced, since
    # their edge/CDN fingerprint checks differ from YouTube's.
    for use_impersonate in (True, False):
        options = _build_ydl_options(
            video_dir=video_dir,
            use_impersonate=use_impersonate,
            cookies_file=cookies_file,
        )
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_path = Path(ydl.prepare_filename(info))
            break
        except yt_dlp.utils.DownloadError as exc:
            last_error = exc
            continue

    if info is None:
        raise RuntimeError(
            f"Failed to download {url!r} after all attempts: {last_error}"
        )

    # -----------------------------------------------------
    # Locate the actual downloaded file.
    # yt-dlp can change the final extension after merging.
    # -----------------------------------------------------
    if not downloaded_path.exists():
        candidates = list(video_dir.glob("video.*"))
        downloaded_path = next(
            (c for c in candidates if c.suffix.lower() in
             (".mp4", ".webm", ".mkv", ".flv", ".ts")),
            None,
        )
        if downloaded_path is None:
            raise RuntimeError(
                f"Downloaded video not found in {video_dir}"
            )

    # -----------------------------------------------------
    # Inspect codec.
    # -----------------------------------------------------
    codec = get_video_codec(str(downloaded_path))

    # H.264 is already suitable — do NOT unnecessarily re-encode.
    if codec == "h264":
        return str(downloaded_path)

    # Anything else gets normalized, e.g.:
    # AV1 -> H.264, VP9 -> H.264, H.265 -> H.264
    # (This is what catches AV1-only YouTube Shorts streams.)
    normalized_path = video_dir / "video_normalized.mp4"
    normalize_video(
        input_path=str(downloaded_path),
        output_path=str(normalized_path),
    )
    return str(normalized_path)
