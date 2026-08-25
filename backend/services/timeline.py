import re
from difflib import SequenceMatcher


# Basic normalization

def normalize_text(text: str) -> list[str]:
    """
    Convert text into lowercase normalized words.

    Punctuation and casing differences are ignored.
    """
    return re.findall(r"\b\w+\b", text.lower())


# Stage 1 — Exact matching

def exact_tokens(text: str) -> list[str]:
    """
    Split text into raw whitespace-separated tokens.

    This intentionally preserves:
    - casing
    - punctuation
    - hyphens

    Example:

        "Hello, Sherlock."

    becomes:

        ["Hello,", "Sherlock."]
    """
    return text.split()


def exact_match(
    target_text: str,
    transcript: list[dict],
) -> dict | None:
    """
    Strictly match the requested dialogue against the
    transcript without normalization.
    """

    target_words = exact_tokens(target_text)

    if not target_words:
        return None

    transcript_words = [
        {
            "word": item["word"].strip(),
            "start": item["start"],
            "end": item["end"],
        }
        for item in transcript
        if item["word"].strip()
    ]

    target_length = len(target_words)

    for i in range(
        len(transcript_words) - target_length + 1
    ):
        window = [
            item["word"]
            for item in transcript_words[
                i:i + target_length
            ]
        ]

        if window == target_words:
            matched_words = transcript_words[
                i:i + target_length
            ]

            return {
                "text": target_text,
                "start_time": matched_words[0]["start"],
                "end_time": matched_words[-1]["end"],
                "matched_words": matched_words,
                "match_type": "exact",
                "match_score": 1.0,
            }

    return None


# Stage 2 — Normalized matching

def prepare_transcript(
    transcript: list[dict],
) -> list[dict]:
    """
    Normalize transcript words while preserving timestamps.

    Also repairs obvious Whisper hyphen splits.

    Example:

        pre
        -configured
        version

    becomes:

        preconfigured
        version

    with the combined timestamp:

        preconfigured -> start of "pre" to end of
                         "-configured"
    """

    normalized_transcript = []

    for item in transcript:
        raw_word = item["word"].strip()

        if not raw_word:
            continue

        words = normalize_text(raw_word)

        if not words:
            continue

        normalized_word = words[0]

        # -------------------------------------------------
        # Merge obvious hyphen-split words.
        #
        # Case 1:
        #
        #   pre
        #   -configured
        #
        # Case 2:
        #
        #   pre-
        #   configured
        # -------------------------------------------------

        if normalized_transcript:
            previous = normalized_transcript[-1]

            if (
                raw_word.startswith("-")
                or previous["raw_word"].endswith("-")
            ):
                previous["word"] += normalized_word
                previous["end"] = item["end"]
                previous["raw_word"] += raw_word

                continue

        normalized_transcript.append(
            {
                "word": normalized_word,
                "raw_word": raw_word,
                "start": item["start"],
                "end": item["end"],
            }
        )

    return normalized_transcript


def normalized_match(
    target_text: str,
    transcript: list[dict],
) -> dict | None:
    """
    Match after normalization.

    Handles:
    - casing differences
    - punctuation differences
    - whitespace differences
    - Whisper hyphen-split words
    """

    target_words = normalize_text(target_text)

    if not target_words:
        return None

    normalized_transcript = prepare_transcript(
        transcript
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
                "match_type": "normalized",
                "match_score": 1.0,
            }

    return None


# Stage 3 — Fuzzy matching

def similarity(
    target_words: list[str],
    candidate_words: list[str],
) -> float:
    """
    Calculate character-level similarity between two
    normalized word sequences.
    """

    target = " ".join(target_words)
    candidate = " ".join(candidate_words)

    return SequenceMatcher(
        None,
        target,
        candidate,
    ).ratio()


def fuzzy_match(
    target_text: str,
    transcript: list[dict],
) -> dict | None:
    """
    Conservative fuzzy fallback.

    Only used after exact and normalized matching fail.

    The highest-scoring candidate is selected, but only if
    it passes a conservative confidence threshold.
    """

    target_words = normalize_text(target_text)

    if not target_words:
        return None

    normalized_transcript = prepare_transcript(
        transcript
    )

    target_length = len(target_words)

    # Fuzzy matching is more dangerous for very short
    # queries. Require a higher threshold for one-word
    # queries.

    if target_length == 1:
        threshold = 0.94
    else:
        threshold = 0.88

    best_match = None
    best_score = 0.0

    # Allow small insertion/deletion differences.
    min_window = max(1, target_length - 1)
    max_window = target_length + 2

    for window_size in range(
        min_window,
        max_window + 1,
    ):
        if window_size > len(normalized_transcript):
            continue

        for i in range(
            len(normalized_transcript) - window_size + 1
        ):
            matched_words = normalized_transcript[
                i:i + window_size
            ]

            candidate_words = [
                item["word"]
                for item in matched_words
            ]

            score = similarity(
                target_words,
                candidate_words,
            )

            if score > best_score:
                best_score = score
                best_match = matched_words

    if best_match is None:
        return None

    if best_score < threshold:
        return None

    return {
        "text": target_text,
        "start_time": best_match[0]["start"],
        "end_time": best_match[-1]["end"],
        "matched_words": best_match,
        "match_type": "fuzzy",
        "match_score": best_score,
    }


# Main timeline finder

def find_timeline(
    target_text: str,
    transcript: list[dict],
) -> dict | None:

    if not target_text.strip():
        return None

    # Stage 1
    # Strict exact match
    # -----------------------------------------------------

    result = exact_match(
        target_text,
        transcript,
    )

    if result is not None:
        return result

    # Stage 2
    # Normalized / repaired match
    # -----------------------------------------------------

    result = normalized_match(
        target_text,
        transcript,
    )

    if result is not None:
        return result

    # Stage 3
    # Conservative fuzzy fallback

    result = fuzzy_match(
        target_text,
        transcript,
    )

    if result is not None:
        return result

    return None
