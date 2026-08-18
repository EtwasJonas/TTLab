from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MatchBase(BaseModel):
    filename: str
    original_filename: str


class MatchCreate(MatchBase):
    pass


class MatchResponse(MatchBase):
    id: int
    duration: Optional[float] = None
    upload_date: datetime
    status: str
    error_message: Optional[str] = None
    progress: float = 0.0
    progress_message: Optional[str] = None
    match_date: Optional[datetime] = None
    player_name: Optional[str] = None
    opponent_name: Optional[str] = None
    result: Optional[str] = None
    score: Optional[str] = None
    notes: Optional[str] = None
    table_points: Optional[str] = None

    class Config:
        from_attributes = True


class MatchUpdate(BaseModel):
    match_date: Optional[datetime] = None
    player_name: Optional[str] = None
    opponent_name: Optional[str] = None
    result: Optional[str] = None
    score: Optional[str] = None
    notes: Optional[str] = None
    table_points: Optional[str] = None


class RallyBase(BaseModel):
    start_time: float
    end_time: float
    duration: float


class RallyCreate(RallyBase):
    match_id: int


class RallyResponse(RallyBase):
    id: int
    match_id: int
    clip_filename: Optional[str] = None
    clip_path: Optional[str] = None
    is_highlight: bool = False
    highlight_score: float = 0.0
    validation_status: str = "accepted"
    confidence: float = 0.0
    impact_count: int = 0
    user_marked_highlight: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class RallyDetectionResponse(BaseModel):
    match_id: int
    rallies: List[RallyResponse]
    total_rallies: int


class UploadResponse(BaseModel):
    match_id: int
    filename: str
    message: str


class ProcessingStatus(BaseModel):
    match_id: int
    status: str
    progress: Optional[float] = None
    progress_message: Optional[str] = None
    rallies_count: Optional[int] = None
