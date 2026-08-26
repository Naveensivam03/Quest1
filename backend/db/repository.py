from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import DialogueMatch, OCRResult, TranscriptWord, Video


def get_video_by_url(
    session: Session,
    url: str,
) -> Video | None:
    statement = select(Video).where(Video.url == url)

    return session.scalar(statement)


def get_video_by_external_id(
    session: Session,
    external_id: str,
) -> Video | None:
    statement = select(Video).where(
        Video.external_id == external_id
    )

    return session.scalar(statement)


def create_video(
    session: Session,
    url: str,
    external_id: str | None = None,
) -> Video:
    existing = get_video_by_url(session, url)
    if existing:
        return existing

    if external_id:
        existing_ext = get_video_by_external_id(session, external_id)
        if existing_ext:
            return existing_ext

    video = Video(
        url=url,
        external_id=external_id,
        status="pending",
    )
    session.add(video)
    session.commit()
    session.refresh(video)

    return video


def update_video(
    session: Session,
    video: Video,
    **fields,
) -> Video:
    for field, value in fields.items():
        setattr(video, field, value)

    session.commit()
    session.refresh(video)

    return video


def create_transcript_words(
    session: Session,
    video_id,
    words: list[dict],
) -> None:

    transcript_words = [
        TranscriptWord(
            video_id=video_id,
            word=item["word"],
            start_time=item["start"],
            end_time=item["end"],
        )
        for item in words
    ]

    session.add_all(transcript_words)
    session.commit()


def has_transcript(
    session: Session,
    video_id,
) -> bool:
    statement = (
        select(TranscriptWord.id)
        .where(TranscriptWord.video_id == video_id)
        .limit(1)
    )

    return session.scalar(statement) is not None


def get_transcript(
    session: Session,
    video_id,
) -> list[dict]:

    statement = (
        select(TranscriptWord)
        .where(TranscriptWord.video_id == video_id)
        .order_by(TranscriptWord.start_time)
    )

    words = session.scalars(statement).all()

    return [
        {
            "word": word.word,
            "start": word.start_time,
            "end": word.end_time,
        }
        for word in words
    ]


def create_dialogue_match(
    session: Session,
    video_id,
    query_text: str,
    timeline: dict,
    frame: dict,
) -> DialogueMatch:

    match = DialogueMatch(
        video_id=video_id,
        query_text=query_text,
        matched_text=timeline["text"],
        start_time=timeline["start_time"],
        end_time=timeline["end_time"],
        frame_number=frame["frame_number"],
        frame_timestamp=frame["timestamp"],
        frame_path=frame["image_path"],
    )

    session.add(match)
    session.commit()
    session.refresh(match)

    return match


def create_ocr_results(
    session: Session,
    video_id,
    results: list[dict],
) -> None:

    ocr_results = [
        OCRResult(
            video_id=video_id,
            frame_number=item["frame_number"],
            timestamp=item["timestamp"],
            text=item["text"],
        )
        for item in results
    ]

    session.add_all(ocr_results)
    session.commit()


def has_ocr_results(
    session: Session,
    video_id,
) -> bool:

    statement = (
        select(OCRResult.id)
        .where(OCRResult.video_id == video_id)
        .limit(1)
    )

    return session.scalar(statement) is not None


def get_ocr_results(
    session: Session,
    video_id,
) -> list[dict]:

    statement = (
        select(OCRResult)
        .where(OCRResult.video_id == video_id)
        .order_by(OCRResult.timestamp)
    )

    results = session.scalars(statement).all()

    return [
        {
            "frame_number": result.frame_number,
            "timestamp": result.timestamp,
            "text": result.text,
        }
        for result in results
    ]


def get_ocr_results_in_range(
    session: Session,
    video_id,
    start_time: float,
    end_time: float | None = None,
) -> list[dict]:
    statement = (
        select(OCRResult)
        .where(
            OCRResult.video_id == video_id,
            OCRResult.timestamp >= start_time,
        )
    )

    if end_time is not None:
        statement = statement.where(
            OCRResult.timestamp <= end_time,
        )

    statement = statement.order_by(OCRResult.timestamp)

    results = session.scalars(statement).all()

    return [
        {
            "frame_number": result.frame_number,
            "timestamp": result.timestamp,
            "text": result.text,
        }
        for result in results
    ]
