"""Labeling backend for the V0.6 ball-tracking dataset (YOLOv8n).

This module powers the integrated labeling tool (frontend route /labeling).
The browser cannot decode the training videos itself (many are HEVC Main 10
from iPhones), so frames are extracted SERVER-SIDE with OpenCV and sent to
the frontend as JPEG.

Storage layout per dataset (data/datasets/<name>/):

    raw/
        images/   m<match_id>_f<frame_index>.jpg   (full resolution!)
        labels/   m<match_id>_f<frame_index>.txt   (YOLO format, may be empty)
    annotations.json                             (source of truth for the UI)
    yolo/                                          (created by export_dataset)
        images/train/, images/val/
        labels/train/, labels/val/
        data.yaml

Conventions:
- Frame navigation is FRAME-INDEX based, not time based. POS_MSEC seeking
  suffers from rounding mismatches between calls; a frame index maps to
  exactly one image both in the UI and in the stored dataset.
- Bounding boxes are stored in YOLO format (class cx cy w h, normalized
  0..1) so the frontend resolution never matters for training data quality.
  A frame can contain SEVERAL boxes (one per visible ball, e.g. multiple
  balls lying on the floor); the label file then has one line per ball.
- Frames WITHOUT a ball get an EMPTY label file. Ultralytics uses these as
  background/negative images, which teaches the model what is NOT a ball
  (the main source of the current false positives).
- annotations.json holds one entry per labeled frame (match_id, frame_index,
  bboxes, labeled_at) and drives the progress display. The label .txt files
  are always regenerated deterministically from it.
"""

import json
import os
import random
import re
import shutil
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.video_processor import (
    VideoProcessor,
    get_display_rotation,
    rotate_frame,
)

DATASETS_PATH = os.getenv("DATASETS_PATH", "../data/datasets")

# Quality/size trade-off for the JPEG frames sent to the labeling UI.
# Training images are ALWAYS saved at full resolution regardless of this.
DISPLAY_MAX_WIDTH = 1280
JPEG_QUALITY = 85

# Dataset names become directory names - restrict to a safe charset
# (prevents path traversal via "../" and similar).
DATASET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

# LRU capacity for decoded display frames. 100 frames at ~150 KB JPEG
# is ~15 MB RAM - plenty for back/forward navigation in the tool.
FRAME_CACHE_SIZE = 100


class _VideoReaderCache:
    """One persistent VideoCapture per video file, guarded by a lock.

    VideoCapture is NOT thread-safe and opening a capture (especially for
    HEVC) is expensive. The labeling UI navigates frame by frame through
    the same video, so a persistent capture makes seeking much faster.
    """

    def __init__(self) -> None:
        self._readers: Dict[str, Tuple[cv2.VideoCapture, threading.Lock]] = {}
        self._registry_lock = threading.Lock()

    def read_frame(self, video_path: str, frame_index: int) -> np.ndarray:
        """Return the full-resolution frame at frame_index (or raise ValueError)."""
        with self._registry_lock:
            entry = self._readers.get(video_path)
            if entry is None:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise ValueError(f"Cannot open video: {video_path}")
                entry = (cap, threading.Lock())
                self._readers[video_path] = entry

        cap, lock = entry
        with lock:
            # Seeking by frame index is exact, unlike CAP_PROP_POS_MSEC.
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
            if not ok or frame is None:
                raise ValueError(f"Cannot read frame {frame_index} from {video_path}")
            # Rotate to display orientation (phone videos record with a
            # display-matrix rotation that OpenCV ignores - see
            # get_display_rotation). Both the downscaled preview AND the
            # saved full-res training image use this path, so normalized
            # bbox coordinates always match the stored dataset.
            return rotate_frame(frame, get_display_rotation(video_path))

    def close_video(self, video_path: str) -> None:
        with self._registry_lock:
            entry = self._readers.pop(video_path, None)
        if entry:
            entry[0].release()


_readers = _VideoReaderCache()

# In-memory LRU cache for downscaled display JPEGs.
_frame_cache: Dict[Tuple[str, int, int], bytes] = {}
_frame_cache_lock = threading.Lock()

# ffprobe metadata per video (duration/fps do not change between calls).
_video_info_cache: Dict[str, dict] = {}
_video_info_lock = threading.Lock()

# Display rotation per video: handled by the shared helpers in
# video_processor.py (get_display_rotation / rotate_frame) so the labeling
# tool and the rally analysis always agree on the coordinate system.
__all__ = [
    "get_display_rotation",
    "rotate_frame",
    "get_video_info",
    "get_frame_jpeg",
    "validate_dataset_name",
    "create_dataset",
    "list_datasets",
    "dataset_stats",
    "get_annotations",
    "save_annotation",
    "delete_annotation",
    "export_dataset",
    "DATASETS_PATH",
    "DISPLAY_MAX_WIDTH",
]


def get_video_info(video_path: str) -> dict:
    """Video metadata (duration, fps, frame_count, ...) with an in-memory cache.

    Uses ffprobe (same source of truth as the analysis pipeline) and adds
    the OpenCV frame count so the UI can navigate to the last frame.
    """
    with _video_info_lock:
        cached = _video_info_cache.get(video_path)
    if cached:
        return cached

    info = VideoProcessor(clip_storage_path=".").get_video_info(video_path)
    cap = cv2.VideoCapture(video_path)
    try:
        info["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    finally:
        cap.release()
    info["rotation"] = get_display_rotation(video_path)

    with _video_info_lock:
        _video_info_cache[video_path] = info
    return info


def frame_time_ms(info: dict, frame_index: int) -> float:
    """Exact presentation time of a frame index in milliseconds."""
    fps = info.get("fps") or 30.0
    return round(frame_index / fps * 1000.0, 1)


def get_frame_jpeg(video_path: str, frame_index: int, max_width: int = DISPLAY_MAX_WIDTH) -> bytes:
    """Decoded frame as JPEG, downscaled to max_width for fast UI transfer.

    Results are cached (video, frame, width) so stepping back and forth
    in the tool does not re-decode the same HEVC frame over and over.
    """
    key = (video_path, frame_index, max_width)
    with _frame_cache_lock:
        cached = _frame_cache.get(key)
        if cached is not None:
            # Move to end = "most recently used" for the popitem below.
            _frame_cache[key] = _frame_cache.pop(key)
            return cached

    frame = _readers.read_frame(video_path, frame_index)

    height, width = frame.shape[:2]
    if max_width and width > max_width:
        scale = max_width / width
        frame = cv2.resize(frame, (max_width, max(1, round(height * scale))))

    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if not ok:
        raise ValueError(f"JPEG encoding failed for frame {frame_index}")
    jpeg = buffer.tobytes()

    with _frame_cache_lock:
        _frame_cache[key] = jpeg
        while len(_frame_cache) > FRAME_CACHE_SIZE:
            _frame_cache.popitem(last=False)
    return jpeg


# ---------------------------------------------------------------------------
# Dataset storage
# ---------------------------------------------------------------------------

def validate_dataset_name(name: str) -> str:
    """Validate a dataset name and return it (raises ValueError otherwise)."""
    if not DATASET_NAME_RE.match(name):
        raise ValueError(
            "Ungültiger Datensatz-Name: nur Kleinbuchstaben, Zahlen, - und _ "
            "(max. 64 Zeichen, kein Sonderzeichen)"
        )
    return name


def dataset_dir(name: str) -> str:
    return os.path.join(DATASETS_PATH, validate_dataset_name(name))


def _dataset_images_dir(name: str) -> str:
    return os.path.join(dataset_dir(name), "raw", "images")


def _dataset_labels_dir(name: str) -> str:
    return os.path.join(dataset_dir(name), "raw", "labels")


def _annotations_path(name: str) -> str:
    return os.path.join(dataset_dir(name), "annotations.json")


# annotations.json is read-modify-write; a lock per process keeps the file
# consistent when the UI fires quick successive saves.
_annotations_lock = threading.Lock()


def dataset_exists(name: str) -> bool:
    return os.path.isdir(dataset_dir(name))


def create_dataset(name: str) -> dict:
    """Create the dataset directory structure and an empty annotations.json."""
    validate_dataset_name(name)
    if dataset_exists(name):
        raise ValueError(f"Datensatz '{name}' existiert bereits")
    os.makedirs(_dataset_images_dir(name), exist_ok=True)
    os.makedirs(_dataset_labels_dir(name), exist_ok=True)
    _write_annotations(name, [])
    return dataset_stats(name)


def list_datasets() -> List[dict]:
    """All datasets with their frame statistics (for the dataset picker UI)."""
    if not os.path.isdir(DATASETS_PATH):
        return []
    result = []
    for name in sorted(os.listdir(DATASETS_PATH)):
        if not os.path.isdir(os.path.join(DATASETS_PATH, name)):
            continue
        annotations = _read_annotations(name)
        positives = sum(1 for a in annotations if a["has_ball"])
        exported = os.path.isfile(os.path.join(dataset_dir(name), "yolo", "data.yaml"))
        result.append({
            "name": name,
            "total_frames": len(annotations),
            "frames_with_ball": positives,
            "frames_without_ball": len(annotations) - positives,
            "exported": exported,
        })
    return result


def dataset_stats(name: str) -> dict:
    if not dataset_exists(name):
        raise ValueError(f"Datensatz '{name}' nicht gefunden")
    annotations = _read_annotations(name)
    positives = sum(1 for a in annotations if a["has_ball"])
    return {
        "name": name,
        "total_frames": len(annotations),
        "frames_with_ball": positives,
        "frames_without_ball": len(annotations) - positives,
        "exported": os.path.isfile(os.path.join(dataset_dir(name), "yolo", "data.yaml")),
    }


def get_annotations(name: str) -> List[dict]:
    """All annotations of a dataset, ordered by match and frame index.

    The frontend uses this to show already-labeled frames (green marker)
    when navigating and to display per-match labeling progress.
    """
    if not dataset_exists(name):
        raise ValueError(f"Datensatz '{name}' nicht gefunden")
    annotations = _read_annotations(name)
    annotations.sort(key=lambda a: (a["match_id"], a["frame_index"]))
    return annotations


def _read_annotations(name: str) -> List[dict]:
    """Load annotations.json and normalize entries to the current format.

    Supports the old single-box format ("bbox": [..]) written before
    multi-box labeling existed: such entries are converted to
    "bboxes": [[..]] so all consumers can rely on one shape.
    """
    path = _annotations_path(name)
    if not os.path.isfile(path):
        return []
    # utf-8-sig tolerates a BOM (e.g. from a hand-edited file edited with
    # Windows tools that write UTF-8 with BOM).
    with open(path, "r", encoding="utf-8-sig") as f:
        try:
            annotations = json.load(f)
        except json.JSONDecodeError:
            # A corrupted file (e.g. crash during write) must not brick the
            # whole tool - start over with the files still on disk.
            return []

    for entry in annotations:
        # Migration: single "bbox" (V0.6 Phase 1) -> "bboxes" list
        if "bboxes" not in entry:
            old_bbox = entry.get("bbox")
            entry["bboxes"] = [old_bbox] if old_bbox else []
            entry.pop("bbox", None)
        elif entry["bboxes"] is None:
            entry["bboxes"] = []
        # Keep the derived flag consistent even with hand-edited files.
        entry["has_ball"] = bool(entry["bboxes"])
    return annotations


def _write_annotations(name: str, annotations: List[dict]) -> None:
    path = _annotations_path(name)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _frame_stem(match_id: int, frame_index: int) -> str:
    return f"m{match_id}_f{frame_index}"


def _validate_bbox(bbox: List[float]) -> None:
    """A single bbox must be [cx, cy, w, h] in normalized 0..1 coordinates."""
    if len(bbox) != 4:
        raise ValueError("Jede Bounding-Box muss [cx, cy, w, h] enthalten")
    if any(not isinstance(v, (int, float)) or v < 0 or v > 1 for v in bbox):
        raise ValueError("Bounding-Box-Werte müssen zwischen 0 und 1 liegen")
    cx, cy, w, h = bbox
    if w <= 0.001 or h <= 0.001:
        raise ValueError("Bounding-Box zu klein (mindestens 0.1% der Bildgröße)")
    if cx - w / 2 < 0 or cy - h / 2 < 0 or cx + w / 2 > 1 or cy + h / 2 > 1:
        raise ValueError("Bounding-Box ragt über den Bildrand hinaus")


def save_annotation(
    name: str,
    video_path: str,
    match_id: int,
    frame_index: int,
    bboxes: Optional[List[List[float]]],
) -> dict:
    """Store one labeled frame: full-res image + YOLO labels + annotations.json.

    bboxes contains one YOLO box per visible ball (several balls on the
    floor -> several boxes). An empty list marks a negative sample.
    Saving the same frame again overwrites the previous annotation, so the
    UI can offer "re-label" without a separate update endpoint.
    """
    if not dataset_exists(name):
        raise ValueError(f"Datensatz '{name}' nicht gefunden")

    bboxes = bboxes or []
    for bbox in bboxes:
        _validate_bbox(bbox)

    info = get_video_info(video_path)
    if frame_index < 0 or frame_index >= info["frame_count"]:
        raise ValueError(
            f"Frame-Index {frame_index} außerhalb des Videos (0..{info['frame_count'] - 1})"
        )

    # Full-resolution image: training quality must not depend on the
    # downscaled preview the user drew on (bbox coords are normalized and
    # therefore resolution-independent).
    frame = _readers.read_frame(video_path, frame_index)
    stem = _frame_stem(match_id, frame_index)
    image_path = os.path.join(_dataset_images_dir(name), stem + ".jpg")
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if not ok:
        raise ValueError(f"JPEG-Encoding für Frame {frame_index} fehlgeschlagen")
    with open(image_path, "wb") as f:
        f.write(buffer.tobytes())

    # YOLO label: one line "0 cx cy w h" per visible ball, an EMPTY file
    # for a negative sample (ultralytics treats empty labels as
    # background image - important against false positives).
    label_path = os.path.join(_dataset_labels_dir(name), stem + ".txt")
    with open(label_path, "w", encoding="utf-8") as f:
        for bbox in bboxes:
            cx, cy, w, h = bbox
            f.write(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

    with _annotations_lock:
        annotations = _read_annotations(name)
        annotations = [
            a for a in annotations
            if not (a["match_id"] == match_id and a["frame_index"] == frame_index)
        ]
        annotations.append({
            "match_id": match_id,
            "frame_index": frame_index,
            "time_ms": frame_time_ms(info, frame_index),
            "has_ball": bool(bboxes),
            "bboxes": bboxes,
            "labeled_at": datetime.utcnow().isoformat(),
        })
        _write_annotations(name, annotations)

    return dataset_stats(name)


def delete_annotation(name: str, match_id: int, frame_index: int) -> dict:
    """Remove a labeled frame (image, label file and annotations.json entry)."""
    if not dataset_exists(name):
        raise ValueError(f"Datensatz '{name}' nicht gefunden")

    stem = _frame_stem(match_id, frame_index)
    for path in (
        os.path.join(_dataset_images_dir(name), stem + ".jpg"),
        os.path.join(_dataset_labels_dir(name), stem + ".txt"),
    ):
        if os.path.exists(path):
            os.remove(path)

    with _annotations_lock:
        annotations = _read_annotations(name)
        remaining = [
            a for a in annotations
            if not (a["match_id"] == match_id and a["frame_index"] == frame_index)
        ]
        _write_annotations(name, remaining)

    return dataset_stats(name)


# ---------------------------------------------------------------------------
# Training export (YOLO/Ultralytics layout)
# ---------------------------------------------------------------------------

def export_dataset(name: str, val_ratio: float = 0.2, seed: int = 42) -> dict:
    """Build the ultralytics training layout from the labeled raw frames.

    Creates yolo/images/{train,val} + yolo/labels/{train,val} + data.yaml.
    The split is deterministic for a given seed so re-exporting does not
    silently move frames between train and val.

    Images are hardlinked when the filesystem supports it (NTFS/ext4 do) -
    instant and without doubling disk usage - and copied as a fallback.
    """
    if not dataset_exists(name):
        raise ValueError(f"Datensatz '{name}' nicht gefunden")
    if not 0.0 < val_ratio < 1.0:
        raise ValueError("val_ratio muss zwischen 0 und 1 liegen")

    annotations = _read_annotations(name)
    if len(annotations) < 2:
        raise ValueError("Mindestens 2 gelabelte Frames sind für einen Export nötig")

    stems = sorted(_frame_stem(a["match_id"], a["frame_index"]) for a in annotations)
    rng = random.Random(seed)
    rng.shuffle(stems)
    val_count = max(1, round(len(stems) * val_ratio))
    val_stems = set(stems[:val_count])

    yolo_dir = os.path.join(dataset_dir(name), "yolo")
    for split in ("train", "val"):
        os.makedirs(os.path.join(yolo_dir, "images", split), exist_ok=True)
        os.makedirs(os.path.join(yolo_dir, "labels", split), exist_ok=True)

    for stem in stems:
        split = "val" if stem in val_stems else "train"
        src_image = os.path.join(_dataset_images_dir(name), stem + ".jpg")
        src_label = os.path.join(_dataset_labels_dir(name), stem + ".txt")
        dst_image = os.path.join(yolo_dir, "images", split, stem + ".jpg")
        dst_label = os.path.join(yolo_dir, "labels", split, stem + ".txt")

        _replace_file(src_image, dst_image, link=True)
        _replace_file(src_label, dst_label, link=False)  # tiny text file

    data_yaml_path = os.path.join(yolo_dir, "data.yaml")
    with open(data_yaml_path, "w", encoding="utf-8") as f:
        f.write(
            "# Auto-generated by TTLab labeling export - do not edit manually.\n"
            "# Relative 'path' so the dataset works on any machine it is\n"
            "# copied/zipped to (ultralytics resolves it relative to this file).\n"
            "path: .\n"
            "train: images/train\n"
            "val: images/val\n"
            "nc: 1\n"
            "names: ['ball']\n"
        )

    train_count = len(stems) - val_count
    print(
        f"[OK] Datensatz '{name}' exportiert: {train_count} Trainings- / "
        f"{len(val_stems)} Val-Frames nach {yolo_dir}"
    )
    return {
        "dataset": name,
        "train_frames": train_count,
        "val_frames": len(val_stems),
        "total_frames": len(stems),
        "yolo_dir": os.path.abspath(yolo_dir),
        "seed": seed,
    }


def _replace_file(src: str, dst: str, link: bool) -> None:
    """Copy or hardlink src to dst, replacing an existing destination."""
    if os.path.exists(dst):
        os.remove(dst)
    if link:
        try:
            os.link(src, dst)
            return
        except OSError:
            pass  # cross-device or unsupported FS -> fall back to copy
    shutil.copy2(src, dst)
