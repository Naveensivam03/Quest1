from services.transcription import transcribe_audio
#
#
# video_id = "580d895e-32f7-4659-b9d5-437121c0e517"
#
# audio_path = f"outputs/{video_id}/audio.wav"
#
# transcript = transcribe_audio(audio_path)
#
# for word in transcript:
#     print(
#         f"[{word['start']:.3f}s -> "
#         f"{word['end']:.3f}s] "
#         f"{word['word']}"
#     )
#

audio_path = "outputs/8437d81d-a2d8-44e8-a8ae-9a43f029d325/audio.wav"

words = transcribe_audio(audio_path)

for word in words:
    print(
        f"{word['word']} "
        f"[{word['start']:.3f} → {word['end']:.3f}]"
    )
