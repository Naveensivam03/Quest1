# from faster_whisper import WhisperModel
#
#
# MODEL_SIZE = "small"
#
# print(f"Loading Whisper {MODEL_SIZE} model...")
#
# model = WhisperModel(
#     MODEL_SIZE,
#     device="cpu",
#     compute_type="int8",
# )
#
# print("Whisper model loaded successfully.")
#
#
# def transcribe_audio(audio_path: str) -> list[dict]:
#     segments, info = model.transcribe(
#         audio_path,
#         beam_size=5,
#         word_timestamps=True,
#     )
#
#     transcript = []
#
#     for segment in segments:
#         print(segment)
#         print("-------")
#         for word in segment.words:
#             transcript.append(
#                 {
#                     "word": word.word.strip(),
#                     "start": word.start,
#                     "end": word.end,
#                 }
#             )
#
#     return transcript
# # def transcribe_audio(audio_path: str) -> list[dict]:
# #     # segments, info = model.transcribe(
# #     #     audio_path,
# #     #     beam_size=5,
# #     # )
# #     segments, info = model.transcribe(
# #         audio_path,
# #         beam_size=5,
# #         word_timestamps=True,
# #     )
# #     transcript = []
# #
# #     for segment in segments:
# #         transcript.append(
# #             {
# #                 "start": segment.start,
# #                 "end": segment.end,
# #                 "text": segment.text.strip(),
# #             }
# #         )
# #
# #     return transcript


from faster_whisper import WhisperModel


model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
)


def transcribe_audio(audio_path: str) -> list[dict]:

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
    )

    words = []

    for segment in segments:
        for word in segment.words:

            words.append({
                "word": word.word.strip(),
                "start": word.start,
                "end": word.end,
            })

    return words
