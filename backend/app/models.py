from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    duration = Column(Float, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    progress = Column(Float, default=0.0, nullable=False)
    progress_message = Column(String, nullable=True)
    match_date = Column(DateTime, nullable=True)
    player_name = Column(String, nullable=True)
    opponent_name = Column(String, nullable=True)
    result = Column(String, nullable=True)  # win, loss, draw, unknown
    score = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    table_points = Column(Text, nullable=True)
    custom_title = Column(String, nullable=True)

    rallies = relationship("Rally", back_populates="match", cascade="all, delete-orphan")


class Rally(Base):
    __tablename__ = "rallies"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    clip_filename = Column(String, nullable=True)
    clip_path = Column(String, nullable=True)
    is_highlight = Column(Boolean, default=False)
    highlight_score = Column(Float, default=0.0)
    validation_status = Column(String, default="accepted")
    confidence = Column(Float, default=0.0)
    impact_count = Column(Integer, default=0)
    user_marked_highlight = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="rallies")
