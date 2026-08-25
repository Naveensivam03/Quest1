from pathlib import Path
import subprocess


def extract_audio(
    video_path: str,
    output_dir: str,
) -> str:

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    audio_path = output / "audio.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(audio_path),
    ]

    subprocess.run(
        command,
        check=True,
    )

    return str(audio_path)
