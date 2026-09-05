from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func, or_, select
from typing import List, Tuple
import os
import uuid
import json
import time
import subprocess
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

UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB chunks so large videos don't fill RAM


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield


app = FastAPI(title="TTLab API", version="0.1.0", lifespan=lifespan)

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


@app.post("/api/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="Ungültiges Videoformat")

    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = os.path.join(VIDEO_STORAGE_PATH, safe_filename)

    # Stream to disk in chunks instead of loading the whole video into memory
    async with aiofiles.open(file_path, 'wb') as out_file:
        while chunk := await file.read(UPLOAD_CHUNK_SIZE):
            await out_file.write(chunk)

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
        "message": "Video uploaded. Mark table corners and start analysis."
    }


def start_analysis_job(match_id: int, mode: str = "background"):
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, process_match_background_sync, match_id, mode)


def process_match_background_sync(match_id: int, mode: str = "background"):
    cpu_count = os.cpu_count() or 4
    if mode == "performance":
        # Full power: all cores minus one, every frame at full resolution.
        # The detection result is identical to the single-threaded analysis.
        workers = max(1, cpu_count - 1)
        frame_step = 1
        motion_max_width = None
    else:
        # Background: a bit less than half the cores, reduced motion
        # analysis (half resolution, every second frame) so the PC stays
        # usable for other work.
        workers = max(1, cpu_count // 2 - 1)
        frame_step = 2
        motion_max_width = 960

    async def update_progress(value: float, message: str):
        async with async_session_maker() as progress_db:
            result = await progress_db.execute(select(Match).where(Match.id == match_id))
            current = result.scalar_one_or_none()
            if current:
                current.progress = value
                current.progress_message = message
                await progress_db.commit()

    async def process():
        loop = asyncio.get_running_loop()

        # Called from worker threads: schedule the DB update on
        # this event loop instead of blocking the worker.
        def progress_callback(progress: float, message: str):
            asyncio.run_coroutine_threadsafe(update_progress(progress, message), loop)

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

            await update_progress(2, "Videodaten werden gelesen")
            rally_detector = RallyDetector()
            # Run blocking detection in a worker thread so the loop stays free
            # to process the live progress updates scheduled by the callback.
            rallies = await asyncio.to_thread(
                rally_detector.detect_rallies,
                match.file_path,
                use_audio=True,
                progress_callback=progress_callback,
                table_points=json.loads(match.table_points) if match.table_points else None,
                frame_step=frame_step,
                motion_workers=workers,
                ball_workers=workers,
                motion_max_width=motion_max_width,
            )
            await update_progress(70, f"{len(rallies)} Rally-Kandidaten gefunden")

            processor = VideoProcessor(CLIP_STORAGE_PATH)
            
            video_info = processor.get_video_info(match.file_path)
            async with async_session_maker() as db:
                result = await db.execute(select(Match).where(Match.id == match_id))
                current = result.scalar_one_or_none()
                if current:
                    current.duration = video_info['duration']
                    current.progress = 72
                    current.progress_message = "Rally-Clips werden erstellt"
                    await db.commit()

            # Clip extraction runs in a thread pool with parallel FFmpeg
            # processes; progress updates arrive via progress_callback.
            t_clips = time.time()
            processed_rallies = await asyncio.to_thread(
                processor.create_rally_clips,
                match.file_path,
                rallies,
                match_id,
                workers,
                progress_callback,
            )
            print(f"Clip-Phase: {time.time() - t_clips:.1f}s ({len(processed_rallies)} Clips, {workers} Worker)")

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
                        highlight_score=rally_data.get('highlight_score', 0.0),
                        is_highlight=rally_data.get('is_highlight', False),
                        validation_status=rally_data.get('validation_status', 'accepted'),
                        confidence=rally_data.get('confidence', 0.0),
                        impact_count=rally_data.get('impact_count', 0),
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


def _run_ffmpeg_concat(list_file: str, output_path: str, fast: bool) -> None:
    """Concatenate the clips listed in list_file into output_path."""
    command = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file]
    if fast:
        # Fast copy mode (no re-encoding, ~2 seconds)
        command += ['-c', 'copy']
    else:
        # Compatible mode (re-encoded, works everywhere)
        command += [
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p',
        ]
    command.append(output_path)
    subprocess.run(command, check=True, capture_output=True, text=True)


async def _export_match_video(
    match_id: int,
    db: AsyncSession,
    highlights_only: bool,
    fast: bool,
) -> FileResponse:
    """Shared implementation for the highlights/all-rallies video export."""
    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")

    query = select(Rally).where(
        Rally.match_id == match_id,
        Rally.clip_filename.isnot(None),
    )
    if highlights_only:
        # Mirror the frontend isMarked logic (user_marked_highlight ||
        # is_highlight) so every rally shown as highlight is exported.
        query = query.where(or_(Rally.is_highlight == True, Rally.user_marked_highlight == True))
    rallies = (await db.execute(query.order_by(Rally.start_time))).scalars().all()

    if not rallies:
        raise HTTPException(
            status_code=404,
            detail="Keine Highlights verfügbar" if highlights_only else "Keine Clips verfügbar",
        )

    prefix = "highlights" if highlights_only else "all_rallies"
    output_filename = f"{prefix}_{match_id}.mp4"
    output_path = os.path.join(CLIP_STORAGE_PATH, output_filename)

    # Create list file for FFmpeg concat (absolute paths with forward slashes)
    list_file = os.path.join(CLIP_STORAGE_PATH, f"{prefix}_{match_id}.txt")
    with open(list_file, 'w', encoding='utf-8') as f:
        for rally in rallies:
            clip_path = os.path.abspath(os.path.join(CLIP_STORAGE_PATH, rally.clip_filename)).replace('\\', '/')
            f.write(f"file '{clip_path}'\n")

    try:
        _run_ffmpeg_concat(list_file, output_path, fast)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {e.stderr}")
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)

    return FileResponse(output_path, media_type='video/mp4', filename=output_filename)


@app.get("/api/matches/{match_id}/export-highlights-video")
async def export_highlights_video(match_id: int, fast: bool = False, db: AsyncSession = Depends(get_db)):
    """Export all highlights as a single concatenated video file."""
    return await _export_match_video(match_id, db, highlights_only=True, fast=fast)


@app.get("/api/matches/{match_id}/export-all-rallies-video")
async def export_all_rallies_video(match_id: int, fast: bool = False, db: AsyncSession = Depends(get_db)):
    """Export all rallies as a single concatenated video file."""
    return await _export_match_video(match_id, db, highlights_only=False, fast=fast)


def _clip_payload(rally: Rally, base_url: str) -> dict:
    return {
        "id": rally.id,
        "start_time": rally.start_time,
        "end_time": rally.end_time,
        "url": f"{base_url}/api/clips/{rally.clip_filename}",
        "duration": rally.duration,
    }


async def _collect_rally_clips(
    match_id: int,
    db: AsyncSession,
    highlights_only: bool,
) -> Tuple[Match, List[Rally]]:
    """Shared implementation for the clip URL listing endpoints."""
    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")

    query = select(Rally).where(
        Rally.match_id == match_id,
        Rally.clip_filename.isnot(None),
    )
    if highlights_only:
        # Mirror the frontend isMarked logic (user_marked_highlight ||
        # is_highlight) so every rally shown as highlight is exported.
        query = query.where(or_(Rally.is_highlight == True, Rally.user_marked_highlight == True))
    rallies = (await db.execute(query.order_by(Rally.start_time))).scalars().all()

    if not rallies:
        raise HTTPException(
            status_code=404,
            detail="Keine Highlights verfügbar" if highlights_only else "Keine Clips verfügbar",
        )
    return match, rallies


@app.get("/api/matches/{match_id}/download-all-rallies")
async def download_all_rallies(match_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Download all rallies as individual clips or combined video."""
    match, rallies = await _collect_rally_clips(match_id, db, highlights_only=False)
    base_url = str(request.base_url).rstrip('/')
    return {
        "match_id": match_id,
        "filename": match.original_filename,
        "clips": [_clip_payload(rally, base_url) for rally in rallies],
        "total": len(rallies),
    }


@app.get("/api/matches/{match_id}/download-highlights")
async def download_highlights(match_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Download only highlighted rallies."""
    match, rallies = await _collect_rally_clips(match_id, db, highlights_only=True)
    base_url = str(request.base_url).rstrip('/')
    return {
        "match_id": match_id,
        "filename": match.original_filename,
        "highlights": [_clip_payload(rally, base_url) for rally in rallies],
        "total": len(rallies),
    }


@app.post("/api/matches/{match_id}/analyze", response_model=dict)
async def start_analysis(match_id: int, mode: str = "background", db: AsyncSession = Depends(get_db)):
    if mode not in {"background", "performance"}:
        raise HTTPException(status_code=400, detail="Ungültiger Analyse-Modus")

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
    start_analysis_job(match_id, mode)

    return {"message": "Analyse gestartet", "match_id": match_id}


@app.post("/api/matches/{match_id}/reevaluate-highlights", response_model=dict)
async def reevaluate_highlights(match_id: int, db: AsyncSession = Depends(get_db)):
    """Re-apply the current highlight heuristics to an existing analysis.

    Reclassifies all rallies of a match from their stored duration/impact/
    score values without re-analysing the video. Manual user markings
    (user_marked_highlight) are never touched and always keep the rally
    a highlight, so re-evaluation can never drop them from exports.
    """
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match nicht gefunden")

    rally_result = await db.execute(
        select(Rally).where(Rally.match_id == match_id).order_by(Rally.start_time)
    )
    rallies = rally_result.scalars().all()
    if not rallies:
        raise HTTPException(status_code=404, detail="Keine Rallys vorhanden")

    max_score = max((r.confidence or 0.0 for r in rallies), default=0.0)
    detector = RallyDetector()
    updated = 0
    for rally in rallies:
        is_highlight, highlight_score = detector.classify_highlight(
            rally.duration,
            rally.impact_count or 0,
            rally.confidence or 0.0,
            max_score,
        )
        # Manual markings always win over the heuristic.
        if rally.user_marked_highlight:
            is_highlight = True
        if rally.is_highlight != is_highlight or abs((rally.highlight_score or 0.0) - highlight_score) > 1e-9:
            rally.is_highlight = is_highlight
            rally.highlight_score = highlight_score
            updated += 1
    await db.commit()

    highlights = sum(1 for r in rallies if r.is_highlight)
    return {
        "message": "Highlights neu bewertet",
        "highlights": highlights,
        "updated": updated,
        "total_rallies": len(rallies),
    }


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

    count_result = await db.execute(
        select(func.count()).select_from(Rally).where(Rally.match_id == match_id)
    )
    rallies_count = count_result.scalar_one()

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
    
    # Bulk delete rallies instead of one DELETE per row
    await db.execute(delete(Rally).where(Rally.match_id == match_id))
    await db.delete(match)
    await db.commit()

    return {"message": "Match erfolgreich gelöscht"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
