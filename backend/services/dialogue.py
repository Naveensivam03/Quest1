from pathlib import Path

from db.database import SessionLocal
from db.models import Video
from db.repository import (
    create_dialogue_match,
    get_transcript,
)

from services.frame import extract_frame
from services.timeline import find_timeline
from services.ocr import scan_video, find_text


def find_dialogue(
    video_id,
    target_text: str,
    use_ocr: bool = False,
) -> dict | None:

    with SessionLocal() as session:

        video = session.get(Video, video_id)

        if video is None:
            raise ValueError(
                f"Video not found: {video_id}"
            )

        if not video.file_path:
            raise RuntimeError(
                "Video has not been downloaded yet."
            )

        transcript = get_transcript(
            session,
            video.id,
        )

        if not transcript:
            raise RuntimeError(
                "Video has not been transcribed yet."
            )

        # -------------------------------------------------
        # Phase 1: Whisper
        # -------------------------------------------------

        timeline = find_timeline(
            target_text,
            transcript,
        )

        print(f"[DIALOGUE] target={target_text!r}")
        print(f"[DIALOGUE] whisper_match={timeline is not None}")

        # -------------------------------------------------
        # OCR disabled
        #
        # Preserve the existing Phase 1 behaviour.
        # -------------------------------------------------

        if not use_ocr:

            if timeline is None:
                return None

            return build_dialogue_result(
                video,
                target_text,
                timeline,
                session,
            )

        # -------------------------------------------------
        # OCR enabled + Whisper found it
        #
        # Search only around the Whisper interval.
        # -------------------------------------------------

        if timeline is not None:

            margin = 1.5

            print(
                f"[OCR] Whisper found dialogue: "
                f"{timeline['start_time']:.2f}s -> {timeline['end_time']:.2f}s"
            )

            print(
                f"[OCR] Scanning window: "
                f"{max(0.0, timeline['start_time'] - margin):.2f}s -> "
                f"{timeline['end_time'] + margin:.2f}s "
                f"at 2 FPS"
            )

            ocr_results = scan_video(
                video_path=video.file_path,
                start_time=max(
                    0.0,
                    timeline["start_time"] - margin,
                ),
                end_time=timeline["end_time"] + margin,
                sample_fps=2.0,
                session=session,
                video_id=video.id,
            )

            ocr_match = find_text(
                target_text,
                ocr_results,
            )

            print(
                f"[OCR] frames_scanned={len(ocr_results)} "
                f"match_found={ocr_match is not None}"
            )

            if ocr_match is not None:

                print(
                    f"[OCR] CONFIRMED at {ocr_match.timestamp:.2f}s "
                    f"text={ocr_match.text!r}"
                )

                return build_ocr_dialogue_result(
                    video,
                    target_text,
                    timeline,
                    ocr_match,
                    session,
                )

            # OCR did not visually confirm it.
            # We can fall back to the Whisper result.
            print(
                "[OCR] No visual match. "
                "Falling back to Whisper result."
            )
            return build_dialogue_result(
                video,
                target_text,
                timeline,
                session,
            )

        # -------------------------------------------------
        # OCR enabled + Whisper did NOT find it
        #
        # Search the entire video.
        # -------------------------------------------------

        print("[OCR] Whisper found no match.")
        print("[OCR] Scanning entire video at 1 FPS.")

        ocr_results = scan_video(
            video_path=video.file_path,
            sample_fps=1.0,
            session=session,
            video_id=video.id,
        )

        ocr_match = find_text(
            target_text,
            ocr_results,
        )

        print(
            f"[OCR] frames_scanned={len(ocr_results)} "
            f"match_found={ocr_match is not None}"
        )

        if ocr_match is None:
            return None

        print(
            f"[OCR] Found dialogue at {ocr_match.timestamp:.2f}s "
            f"text={ocr_match.text!r}"
        )

        return build_ocr_dialogue_result(
            video,
            target_text,
            None,
            ocr_match,
            session,
        )


def build_dialogue_result(
    video,
    target_text,
    timeline,
    session,
):

    frames_dir = (
        Path(video.file_path).parent / "frames"
    )

    frame = extract_frame(
        video_path=video.file_path,
        timestamp=timeline["start_time"],
        output_dir=str(frames_dir),
    )

    match = create_dialogue_match(
        session=session,
        video_id=video.id,
        query_text=target_text,
        timeline=timeline,
        frame=frame,
    )

    return {
        "match_id": str(match.id),
        "video_id": str(video.id),
        "text": timeline["text"],
        "start_time": timeline["start_time"],
        "end_time": timeline["end_time"],
        "frame_number": frame["frame_number"],
        "frame_timestamp": frame["timestamp"],
        "frame_path": frame["image_path"],
        "match_source": "whisper"
    }


def build_ocr_dialogue_result(
    video,
    target_text,
    timeline,
    ocr_match,
    session,
):

    frames_dir = (
        Path(video.file_path).parent / "frames"
    )

    frame = extract_frame(
        video_path=video.file_path,
        timestamp=ocr_match.timestamp,
        output_dir=str(frames_dir),
    )

    if timeline is not None:
        start_time = timeline["start_time"]
        end_time = timeline["end_time"]
        text = timeline["text"]
    else:
        start_time = ocr_match.timestamp
        end_time = ocr_match.timestamp
        text = ocr_match.text

    # create_dialogue_match expects the existing
    # timeline structure, so construct one for OCR-only
    # matches.
    ocr_timeline = {
        "text": text,
        "start_time": start_time,
        "end_time": end_time,
        "matched_words": [],
        "match_type": "ocr",
    }

    match = create_dialogue_match(
        session=session,
        video_id=video.id,
        query_text=target_text,
        timeline=ocr_timeline,
        frame=frame,
    )

    return {
        "match_id": str(match.id),
        "video_id": str(video.id),
        "text": text,
        "start_time": start_time,
        "end_time": end_time,
        "frame_number": frame["frame_number"],
        "frame_timestamp": frame["timestamp"],
        "frame_path": frame["image_path"],
        "match_source": "ocr"
    }
