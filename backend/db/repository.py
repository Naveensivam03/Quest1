from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import DialogueMatch, TranscriptWord, Video


def get_video_by_url(
    session: Session,
    url: str,
) -> Video | None:
    statement = select(Video).where(Video.url == url)

    return session.scalar(statement)


def create_video(
    session: Session,
    url: str,
) -> Video:
    video = Video(
        url=url,
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
