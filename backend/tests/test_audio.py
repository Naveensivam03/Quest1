from services.audio import extract_audio


video_path = "outputs/580d895e-32f7-4659-b9d5-437121c0e517/video.mkv"

audio_path = extract_audio(
    video_path,
    "outputs/580d895e-32f7-4659-b9d5-437121c0e517"
)

print(f"Audio extracted successfully:")
print(audio_path)
