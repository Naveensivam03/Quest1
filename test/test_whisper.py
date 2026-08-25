from faster_whisper import WhisperModel

print("Loading Whisper model...")

# model = WhisperModel(
#     "base",
#     device="cuda",
#     compute_type="float16"
# )
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)
print("Model loaded successfully.")

segments, info = model.transcribe(
    "audio.wav",
    beam_size=5
)

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

print("Done.")
