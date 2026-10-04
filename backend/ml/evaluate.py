#!/usr/bin/env python3
"""Evaluate the ball detectors (heuristic vs. ML) against the user ground truth.

Compares full rally detection runs against the manually validated rallies in
the DB (rallies.validation_status: accepted = real rally, rejected = not a
rally). For every (detector, play-zone factor) combination it reports
TP/FP/FN, precision, recall, F1 - the same match rule as the play-zone
measurement (time overlap >= 20% of the shorter window).

Runs on the TTLab server (needs the backend venv: cv2, librosa, onnxruntime).
Motion + audio are extracted ONCE per video and cached in the system temp
dir, so switching detectors/factors is cheap afterwards.

Examples:
    python evaluate.py --match 5 --detectors heuristic --factors 0.0
    python evaluate.py --match 2 --detectors heuristic,ml --factors 0.0,0.5,1.0
    python evaluate.py --match 2 --detectors ml --factors 0.0,0.5,1.0,1.5
"""

import argparse
import json
import os
import sqlite3
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.rally_detection import RallyDetector  # noqa: E402
from app.ball_detector import create_ball_detector, find_model_file  # noqa: E402
from scipy import signal  # noqa: E402

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB = os.path.join(PROJECT_ROOT, "data", "db", "ttlab.db")
CACHE_DIR = os.path.join(
    os.environ.get("TEMP", os.environ.get("TMP", "/tmp")), "ttlab_evaluate_cache"
)
OVERLAP_RATIO = 0.2


def load_match(match_id: int):
    """Video path (display-oriented absolute), table points and ground truth."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    row = con.execute(
        "SELECT file_path, table_points FROM matches WHERE id=?", (match_id,)
    ).fetchone()
    rows = con.execute(
        "SELECT start_time, end_time, validation_status, impact_count "
        "FROM rallies WHERE match_id=? ORDER BY start_time",
        (match_id,),
    ).fetchall()
    con.close()
    if row is None:
        raise SystemExit(f"Match {match_id} existiert nicht in {DB}")
    video_path = os.path.normpath(
        os.path.join(os.path.join(PROJECT_ROOT, "backend"), row[0])
    )
    points = json.loads(row[1]) if row[1] else None
    gt = {
        "accepted": [(r[0], r[1], r[3]) for r in rows if r[2] == "accepted"],
        "rejected": [(r[0], r[1]) for r in rows if r[2] == "rejected"],
    }
    return video_path, points, gt


def extract_motion_audio_once(detector: RallyDetector, video_path: str, tag: str):
    """Motion + audio features once per video, cached across runs."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    mfile = os.path.join(CACHE_DIR, f"{tag}_motion.npy")
    afile = os.path.join(CACHE_DIR, f"{tag}_audio.npz")
    if os.path.exists(mfile) and os.path.exists(afile):
        motion = np.load(mfile)
        fps = float(np.load(mfile + ".fps.npy")[0])
        audio = np.load(afile)
        print(f"  [Cache] Motion+Audio geladen ({len(motion)} Frames)")
        return motion, fps, audio["onset"], audio["times"]

    workers = max(1, (os.cpu_count() or 4) - 1)
    t0 = time.time()
    motion, fps = detector.extract_motion_features(video_path, frame_step=1, max_workers=workers)
    onset, times, _ = detector.extract_audio_features(video_path)
    print(f"  [Motion+Audio: {time.time() - t0:.0f}s, {len(motion)} Frames, fps={fps:.2f}]")
    np.save(mfile, motion)
    np.save(mfile + ".fps.npy", np.array([fps]))
    np.savez(afile, onset=onset, times=times)
    return motion, fps, onset, times


def find_audio_peaks(detector, motion, fps, onset, times):
    """Peak extraction identical to RallyDetector.detect_rallies."""
    time_resolution = times[1] - times[0] if len(times) > 1 else 0.1
    motion_resampled = detector._resample_motion(motion, fps, times)
    combined = detector._combine_scores(motion_resampled, onset)
    audio_norm = detector._normalize(onset)
    peak_idx, props = signal.find_peaks(
        audio_norm,
        height=float(np.percentile(audio_norm, 75)),
        prominence=0.12,
        distance=max(1, int(0.12 / time_resolution)),
    )
    return times[peak_idx], np.asarray(props["peak_heights"], dtype=float), combined, time_resolution


def detect_with(detector, ball_detector, video_path, points, peaks, factor):
    """Ball validation + rally assembly for one (detector, factor) variant."""
    detector.play_zone_factor = factor
    peak_times, peak_heights, combined, tres = peaks
    workers = max(1, (os.cpu_count() or 4) - 1)
    t0 = time.time()
    candidates = detector._rallies_from_audio_peaks(
        peak_times, peak_heights, combined, tres,
        video_path, points, workers, None, ball_detector,
    )
    rallies = []
    for cand in candidates:
        start, end, score = cand[:3]
        impact = int(cand[3]) if len(cand) > 3 else 0
        duration = end - start
        if duration > detector.max_rally_duration:
            end = start + detector.max_rally_duration
            duration = detector.max_rally_duration
        if duration >= detector.min_rally_duration:
            rallies.append((start, end, impact))
    print(f"    {time.time() - t0:.0f}s -> {len(rallies)} Rallys")
    return rallies


def _overlap(a_s, a_e, b_s, b_e):
    return max(0.0, min(a_e, b_e) - max(a_s, b_s))


def evaluate(detected, gt):
    """Match detected rally windows against the validated ground truth."""
    accepted = gt["accepted"]
    rejected = gt["rejected"]
    matched_accepted = set()
    tp, fp, matched_rejected = 0, 0, 0
    for start, end, _impact in detected:
        best_ratio, best_i = 0.0, -1
        for i, (g_s, g_e, _imp) in enumerate(accepted):
            ov = _overlap(start, end, g_s, g_e)
            if ov > 0:
                ratio = ov / min(end - start, g_e - g_s)
                if ratio > best_ratio:
                    best_ratio, best_i = ratio, i
        if best_i >= 0 and best_ratio >= OVERLAP_RATIO:
            tp += 1
            matched_accepted.add(best_i)
        else:
            fp += 1
            if any(
                _overlap(start, end, r_s, r_e) >= OVERLAP_RATIO * min(end - start, r_e - r_s)
                for r_s, r_e in rejected
            ):
                matched_rejected += 1
    fn = len(accepted) - len(matched_accepted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "detected": len(detected),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "fp_on_rejected": matched_rejected,
    }


def make_ball_detector(name: str):
    """heuristic or ml, independent of the ambient TTLAB_BALL_DETECTION."""
    os.environ["TTLAB_BALL_DETECTION"] = name
    if name == "ml" and find_model_file() is None:
        raise SystemExit(
            "Kein ONNX-Modell in data/models/ - zuerst export_onnx.py auf dem "
            "Trainings-PC ausfuehren und die Datei nach data/models/ kopieren."
        )
    return create_ball_detector()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--match", type=int, default=2, help="Match-ID mit validierten Rallys (Default: 2)")
    parser.add_argument("--detectors", default="heuristic,ml", help="Kommasepariert: heuristic und/oder ml")
    parser.add_argument("--factors", default="0.0,0.5,1.0", help="Kommaseparierte TTLAB_PLAY_ZONE-Faktoren")
    args = parser.parse_args()

    factors = [float(f) for f in args.factors.split(",") if f.strip()]
    detector_names = [d.strip() for d in args.detectors.split(",") if d.strip()]

    detector = RallyDetector()
    video_path, points, gt = load_match(args.match)
    print(f"Match {args.match}: {video_path}")
    print(f"  Ground-Truth: {len(gt['accepted'])} accepted / {len(gt['rejected'])} rejected")

    motion, fps, onset, times = extract_motion_audio_once(detector, video_path, f"match{args.match}")
    peaks = find_audio_peaks(detector, motion, fps, onset, times)
    print(f"  Audio-Peaks: {len(peaks[0])}")

    results = {"match": args.match, "variants": {}}
    print(f"\n{'Variante':<22}{'P':>7}{'R':>7}{'F1':>7}{'TP':>5}{'FP':>5}{'FN':>5}{'FP-auf-rej':>12}")
    for name in detector_names:
        try:
            ball_detector = make_ball_detector(name)
        except SystemExit as e:
            print(f"  [SKIP] {name}: {e}")
            continue
        model_version = getattr(ball_detector, "model_version", "heuristic_v0.5")
        for factor in factors:
            key = f"{name} (zone={factor})"
            detected = detect_with(detector, ball_detector, video_path, points, peaks, factor)
            metrics = evaluate(detected, gt)
            results["variants"][key] = {"model_version": model_version, **metrics}
            print(
                f"{key:<22}{metrics['precision']:>7}{metrics['recall']:>7}{metrics['f1']:>7}"
                f"{metrics['tp']:>5}{metrics['fp']:>5}{metrics['fn']:>5}{metrics['fp_on_rejected']:>12}"
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluate_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nErgebnisse: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
