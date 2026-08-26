import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    url: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(
        String,
        unique=True,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="pending",
    )

    file_path: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    audio_path: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    duration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    fps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frame_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    transcript_words: Mapped[list["TranscriptWord"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )
    dialogue_matches: Mapped[list["DialogueMatch"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )
    ocr_results: Mapped[list["OCRResult"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )


class TranscriptWord(Base):
    __tablename__ = "transcript_words"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )

    word: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    start_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    end_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    video: Mapped["Video"] = relationship(
        back_populates="transcript_words",
    )


class DialogueMatch(Base):
    __tablename__ = "dialogue_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )

    query_text: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    matched_text: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    start_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    end_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    frame_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    frame_timestamp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    frame_path: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    video: Mapped["Video"] = relationship(
        back_populates="dialogue_matches",
    )


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    frame_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    timestamp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    video: Mapped["Video"] = relationship(
        back_populates="ocr_results",
    )

    __table_args__ = (
        UniqueConstraint(
            "video_id",
            "frame_number",
            name="uq_ocr_results_video_frame",
        ),
    )
