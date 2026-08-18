from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import os
import uuid
from datetime import datetime
import json
import aiofiles
import asyncio

from app.database import get_db, init_db, async_session_maker
from app.models import Match, Rally
from app.schemas import (
    UploadResponse, 
    MatchResponse, 
    RallyResponse, 
    RallyDetectionResponse,
    ProcessingStatus,
    MatchUpdate,
    RallyUpdate,
)
from app.rally_detection import RallyDetector
from app.video_processor import VideoProcessor
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TTLab API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEO_STORAGE_PATH = os.getenv("VIDEO_STORAGE_PATH", "../data/videos")
CLIP_STORAGE_PATH = os.getenv("CLIP_STORAGE_PATH", "../data/clips")

os.makedirs(VIDEO_STORAGE_PATH, exist_ok=True)
os.makedirs(CLIP_STORAGE_PATH, exist_ok=True)

app.mount("/clips", StaticFiles(directory=CLIP_STORAGE_PATH), name="clips")
app.mount("/videos", StaticFiles(directory=VIDEO_STORAGE_PATH), name="videos")


@app.on_event("startup")
async def startup_event():
    await init_db()
    async with async_session_maker() as db:
        # A process killed during analysis must be restartable instead of staying
        # permanently stuck in the processing state.
        result = await db.execute(select(Match).where(Match.status == "processing"))
        stale_matches = result.scalars().all()
        for stale_match in stale_matches:
            stale_match.status = "pending"
            stale_match.progress = 0
            stale_match.progress_message = "Analyse kann erneut gestartet werden"
        await db.commit()
    print("[OK] Datenbank initialisiert")


@app.post("/api/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="Ungültiges Videoformat")

    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = os.path.join(VIDEO_STORAGE_PATH, safe_filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    async with async_session_maker() as db:
        match = Match(
            filename=safe_filename,
            original_filename=file.filename,
            file_path=file_path,
            status="pending"
        )
        db.add(match)
        await db.commit()
        await db.refresh(match)

    return {
        "match_id": match.id,
        "filename": file.filename,
        "message": "Video hochgeladen. Tisch markieren und Analyse starten."
    }


def start_analysis_job(match_id: int):
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, process_match_background_sync, match_id)


def process_match_background_sync(match_id: int):
    async def process():
        async def update_progress(value: float, message: str):
            async with async_session_maker() as progress_db:
                result = await progress_db.execute(select(Match).where(Match.id == match_id))
                current = result.scalar_one_or_none()
                if current:
                    current.progress = value
                    current.progress_message = message
                    await progress_db.commit()

        try:
            async with async_session_maker() as db:
                result = await db.execute(select(Match).where(Match.id == match_id))
                match = result.scalar_one_or_none()
                
                if not match:
                    return

                match.status = "processing"
                match.progress = 1
                match.progress_message = "Analyse wird vorbereitet"
                await db.commit()

            await update_progress(10, "Videodaten werden gelesen")
            rally_detector = RallyDetector()
            rallies = rally_detector.detect_rallies(
                match.file_path,
                use_audio=True,
                progress_callback=None,
                table_points=json.loads(match.table_points) if match.table_points else None,
            )
            await update_progress(65, f"{len(rallies)} Rally-Kandidaten gefunden")

            processor = VideoProcessor(CLIP_STORAGE_PATH)
            
            video_info = processor.get_video_info(match.file_path)
            async with async_session_maker() as db:
                result = await db.execute(select(Match).where(Match.id == match_id))
                current = result.scalar_one_or_none()
                if current:
                    current.duration = video_info['duration']
                    current.progress = 70
                    current.progress_message = "Rally-Clips werden erstellt"
                    await db.commit()

            processed_rallies = []
            total = max(len(rallies), 1)
            for index, rally in enumerate(rallies):
                processed_rallies.extend(
                    processor.create_rally_clips(match.file_path, [rally], match_id)
                )
                await update_progress(70 + (index + 1) / total * 25, f"Clip {index + 1} von {len(rallies)} erstellt")

            await update_progress(99, "Ergebnisse werden gespeichert")
            async with async_session_maker() as db:
                for rally_data in processed_rallies:
                    rally = Rally(
                        match_id=match_id,
                        start_time=rally_data['start_time'],
                        end_time=rally_data['end_time'],
                        duration=rally_data['duration'],
                        clip_filename=rally_data.get('clip_filename'),
                        clip_path=rally_data.get('clip_path'),
                        highlight_score=rally_data.get('score', 0.0),
                        is_highlight=rally_data.get('score', 0.0) > 0.5
                        ,validation_status=rally_data.get('validation_status', 'review')
                        ,confidence=rally_data.get('confidence', 0.0)
                        ,impact_count=rally_data.get('impact_count', 0)
                    )
                    db.add(rally)

                result = await db.execute(select(Match).where(Match.id == match_id))
                match = result.scalar_one_or_none()
                if not match:
                    return
                match.status = "completed"
                match.progress = 100
                match.progress_message = f"Fertig: {len(processed_rallies)} Rallys"
                await db.commit()

            print(f"[OK] Match {match_id} erfolgreich verarbeitet: {len(processed_rallies)} Rallys")

        except Exception as e:
            print(f"[FEHLER] Fehler bei der Verarbeitung von Match {match_id}: {e}")
            async with async_session_maker() as db:
                result = await db.execute(select(Match).where(Match.id == match_id))
                match = result.scalar_one_or_none()
                if match:
                    match.status = "failed"
                    match.progress_message = "Analyse fehlgeschlagen"
                    match.error_message = str(e)
                    await db.commit()
    
    asyncio.run(process())


@app.get("/api/matches", response_model=List[MatchResponse])
async def get_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).order_by(Match.upload_date.desc()))
    matches = result.scalars().all()
    return matches


@app.get("/api/matches/{match_id}", response_model=MatchResponse)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")
    
    return match


@app.patch("/api/matches/{match_id}", response_model=MatchResponse)
async def update_match(match_id: int, payload: MatchUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")

    if payload.result not in {None, "win", "loss", "draw", "unknown"}:
        raise HTTPException(status_code=400, detail="Ungültiges Ergebnis")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(match, field, value)
    await db.commit()
    await db.refresh(match)
    return match


@app.patch("/api/rallies/{rally_id}", response_model=RallyResponse)
async def update_rally(
    rally_id: int,
    update_data: RallyUpdate,
    db: AsyncSession = Depends(get_db)
):
    if update_data.validation_status and update_data.validation_status not in {"accepted", "review", "rejected"}:
        raise HTTPException(status_code=400, detail="Ungültiger Rally-Status")
    result = await db.execute(select(Rally).where(Rally.id == rally_id))
    rally = result.scalar_one_or_none()
    if not rally:
        raise HTTPException(status_code=404, detail="Rally nicht gefunden")
    if update_data.validation_status:
        rally.validation_status = update_data.validation_status
    if update_data.user_marked_highlight is not None:
        rally.user_marked_highlight = update_data.user_marked_highlight
        rally.is_highlight = update_data.user_marked_highlight
    if update_data.notes is not None:
        rally.notes = update_data.notes
    await db.commit()
    await db.refresh(rally)
    return rally


@app.get("/api/matches/{match_id}/export-highlights")
async def export_highlights(match_id: int, db: AsyncSession = Depends(get_db)):
    """Returns list of accepted rallies with user-marked highlights first."""
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")
    
    rally_result = await db.execute(
        select(Rally)
        .where(Rally.match_id == match_id, Rally.validation_status == "accepted")
        .order_by(Rally.user_marked_highlight.desc(), Rally.start_time)
    )
    rallies = rally_result.scalars().all()
    return {"match_id": match_id, "rallies": rallies, "total": len(rallies)}


@app.post("/api/matches/{match_id}/analyze", response_model=dict)
async def start_analysis(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")
    
    if match.status in ["processing", "completed"]:
        return {"message": "Analyse läuft bereits oder ist abgeschlossen"}

    if not match.table_points:
        raise HTTPException(status_code=400, detail="Bitte zuerst die vier Tischecken markieren")
    
    match.status = "pending"
    match.progress = 0
    match.progress_message = "Analyse wird gestartet"
    match.error_message = None
    await db.commit()
    start_analysis_job(match_id)
    
    return {"message": "Analyse gestartet", "match_id": match_id}


@app.get("/api/matches/{match_id}/rallies", response_model=RallyDetectionResponse)
async def get_match_rallies(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")

    rally_result = await db.execute(
        select(Rally)
        .where(Rally.match_id == match_id)
        .order_by(Rally.start_time)
    )
    rallies = rally_result.scalars().all()

    return {
        "match_id": match_id,
        "rallies": rallies,
        "total_rallies": len(rallies)
    }


@app.get("/api/matches/{match_id}/status", response_model=ProcessingStatus)
async def get_processing_status(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")

    rally_result = await db.execute(
        select(Rally).where(Rally.match_id == match_id)
    )
    rallies_count = len(rally_result.scalars().all())

    return {
        "match_id": match_id,
        "status": match.status,
        "progress": match.progress,
        "progress_message": match.progress_message,
        "rallies_count": rallies_count
    }


@app.get("/api/clips/{clip_filename}")
async def get_clip(clip_filename: str):
    clip_path = os.path.join(CLIP_STORAGE_PATH, clip_filename)
    
    if not os.path.exists(clip_path):
        raise HTTPException(status_code=404, detail="Clip nicht gefunden")
    
    return FileResponse(clip_path, media_type="video/mp4")


@app.get("/api/videos/{video_filename}")
async def get_video(video_filename: str):
    video_path = os.path.join(VIDEO_STORAGE_PATH, video_filename)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video nicht gefunden")
    
    return FileResponse(video_path, media_type="video/mp4")


@app.delete("/api/matches/{match_id}")
async def delete_match(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")

    if match.file_path and os.path.exists(match.file_path):
        os.remove(match.file_path)

    rally_result = await db.execute(
        select(Rally).where(Rally.match_id == match_id)
    )
    rallies = rally_result.scalars().all()
    
    for rally in rallies:
        if rally.clip_path and os.path.exists(rally.clip_path):
            os.remove(rally.clip_path)

    for rally in rallies:
        await db.delete(rally)
    
    await db.delete(match)
    await db.commit()

    return {"message": "Match erfolgreich gelöscht"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
