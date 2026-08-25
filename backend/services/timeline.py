import re


def normalize_text(text: str) -> list[str]:
    """
    Convert text into normalized words for matching.
    """
    return re.findall(r"\b\w+\b", text.lower())


def find_timeline(
    target_text: str,
    transcript: list[dict],
) -> dict | None:

    target_words = normalize_text(target_text)

    if not target_words:
        return None

    normalized_transcript = []

    for item in transcript:
        words = normalize_text(item["word"])

        if words:
            normalized_transcript.append(
                {
                    "word": words[0],
                    "start": item["start"],
                    "end": item["end"],
                }
            )

    target_length = len(target_words)

    for i in range(
        len(normalized_transcript) - target_length + 1
    ):

        window = [
            item["word"]
            for item in normalized_transcript[
                i:i + target_length
            ]
        ]

        if window == target_words:

            matched_words = normalized_transcript[
                i:i + target_length
            ]

            return {
                "text": target_text,
                "start_time": matched_words[0]["start"],
                "end_time": matched_words[-1]["end"],
                "matched_words": matched_words,
            }

    return None
