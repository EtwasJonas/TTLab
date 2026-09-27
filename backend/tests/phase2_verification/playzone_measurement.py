"""Schritt 3: Ground-Truth-Messung der Spielzonen-Faktoren.

Fuer Match 2 (180-Grad-iPhone-MOV, Hauptmessung) und Match 5 (unrotiertes
MP4, Kontrolle):
  1. Motion + Audio ONCE (frame_step=1, volle Aufloesung, motion parallel)
     -> identisch zur Performance-Analyse, Ergebnisse werden gecacht
  2. Pro Faktor [0.0, 0.5, 1.0, 1.5]: nur Ball-Validierung + Rally-
     Zusammenbau mit detector.play_zone_factor = faktor
  3. Vergleich gegen die User-Ground-Truth (rallies.validation_status):
     accepted = echter Ballwechsel, rejected = kein Ballwechsel.
     Match-Regel: Zeit-Ueberlappung >= 20% des kuerzeren Fensters.

Ausgabe pro Faktor: TP/FP/FN, Precision/Recall/F1, erkannte abgelehnte
Rallys (je weniger desto besser), Mittelwerte impact_count.
"""
import json
import os
import sqlite3
import sys
import time

import numpy as np

sys.path.insert(0, r"C:\Users\Jonas\Documents\OpenCode\ttlab\backend")
from app.rally_detection import RallyDetector  # noqa: E402
from app.ball_detector import HeuristicBallDetector  # noqa: E402
from scipy import signal  # noqa: E402

DB = r"C:\Users\Jonas\Documents\OpenCode\ttlab\data\db\ttlab.db"
CACHE = r"C:\Users\Jonas\AppData\Local\Temp\opencode\playzone_cache"
FACTORS = [0.0, 0.5, 1.0, 1.5]
OVERLAP_RATIO = 0.2
os.makedirs(CACHE, exist_ok=True)


def load_match(match_id):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    path, points = con.execute(
        "SELECT file_path, table_points FROM matches WHERE id=?", (match_id,)
    ).fetchone()
    rows = con.execute(
        "SELECT start_time, end_time, validation_status, impact_count "
        "FROM rallies WHERE match_id=? ORDER BY start_time",
        (match_id,),
    ).fetchall()
    con.close()
    rel_video = os.path.normpath(os.path.join(r"C:\Users\Jonas\Documents\OpenCode\ttlab\backend", path))
    gt = {
        "accepted": [(r[0], r[1], r[3]) for r in rows if r[2] == "accepted"],
        "rejected": [(r[0], r[1]) for r in rows if r[2] == "rejected"],
        "review":   [(r[0], r[1]) for r in rows if r[2] == "review"],
    }
    return rel_video, json.loads(points) if points else None, gt


def motion_audio_once(detector, video_path, tag):
    """Motion+Audio einmal berechnen (und im Temp-Cache ablegen)."""
    mfile = os.path.join(CACHE, f"{tag}_motion.npy")
    afile = os.path.join(CACHE, f"{tag}_audio.npz")
    if os.path.exists(mfile) and os.path.exists(afile):
        motion = np.load(mfile)
        fps = float(np.load(mfile + ".fps.npy"))
        a = np.load(afile)
        return motion, fps, a["onset"], a["times"]
    workers = max(1, (os.cpu_count() or 4) - 1)
    t0 = time.time()
    motion, fps = detector.extract_motion_features(video_path, frame_step=1, max_workers=workers)
    onset, times, _ = detector.extract_audio_features(video_path)
    print(f"  [Motion+Audio: {time.time()-t0:.0f}s, {len(motion)} Frames, fps={fps}]")
    np.save(mfile, motion)
    np.save(mfile + ".fps.npy", np.array([fps]))
    np.savez(afile, onset=onset, times=times)
    return motion, fps, onset, times


def peaks_like_pipeline(detector, motion, fps, onset, times):
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


def detect_with_factor(detector, video_path, table_points, peak_times, peak_heights, combined, tres, factor):
    detector.play_zone_factor = factor
    ball_workers = max(1, (os.cpu_count() or 4) - 1)
    t0 = time.time()
    candidates = detector._rallies_from_audio_peaks(
        peak_times, peak_heights, combined, tres,
        video_path, table_points, ball_workers, None, HeuristicBallDetector(),
    )
    # Post-Filter wie in detect_rallies (Dauer-Clamp + Mindestdauer)
    out = []
    for cand in candidates:
        start, end, score = cand[:3]
        impact = int(cand[3]) if len(cand) > 3 else 0
        duration = end - start
        if duration > detector.max_rally_duration:
            end = start + detector.max_rally_duration
            duration = detector.max_rally_duration
        if duration >= detector.min_rally_duration:
            out.append((start, end, impact))
    print(f"    Faktor {factor}: {len(out)} Rallys ({time.time()-t0:.0f}s)")
    return out


def overlap(a_s, a_e, b_s, b_e):
    return max(0.0, min(a_e, b_e) - max(a_s, b_s))


def evaluate(detected, gt):
    acc = gt["accepted"]
    rej = gt["rejected"]
    matched_acc = set()
    tp, fp = 0, 0
    tp_impacts, fp_impacts = [], []
    matched_rej = 0
    for (s, e, imp) in detected:
        best_ratio, best_i = 0.0, -1
        for i, (gs, ge, _) in enumerate(acc):
            ov = overlap(s, e, gs, ge)
            if ov > 0:
                r = ov / min(e - s, ge - gs)
                if r > best_ratio:
                    best_ratio, best_i = r, i
        if best_i >= 0 and best_ratio >= OVERLAP_RATIO:
            tp += 1
            matched_acc.add(best_i)
            tp_impacts.append(imp)
        else:
            fp += 1
            fp_impacts.append(imp)
            if any(overlap(s, e, rs, re_) >= OVERLAP_RATIO * min(e - s, re_ - rs) for rs, re_ in rej):
                matched_rej += 1
    fn = len(acc) - len(matched_acc)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "detected": len(detected), "tp": tp, "fp": fp, "fn": fn,
        "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
        "matched_rejected": matched_rej,
        "tp_impact_mean": round(float(np.mean(tp_impacts)), 1) if tp_impacts else None,
        "fp_impact_mean": round(float(np.mean(fp_impacts)), 1) if fp_impacts else None,
    }


detector = RallyDetector()
results = {}
for match_id, tag in ((2, "match2"), (5, "match5")):
    video, points, gt = load_match(match_id)
    print(f"\n=== Match {match_id} ({tag}) ===")
    print(f"  Ground-Truth: {len(gt['accepted'])} accepted, {len(gt['rejected'])} rejected")
    motion, fps, onset, times = motion_audio_once(detector, video, tag)
    peak_times, peak_heights, combined, tres = peaks_like_pipeline(detector, motion, fps, onset, times)
    print(f"  Audio-Peaks: {len(peak_times)}")
    results[tag] = {"gt_accepted": len(gt["accepted"]), "gt_rejected": len(gt["rejected"]), "factors": {}}
    for factor in FACTORS:
        detected = detect_with_factor(detector, video, points, peak_times, peak_heights, combined, tres, factor)
        metrics = evaluate(detected, gt)
        results[tag]["factors"][str(factor)] = metrics
        print(f"    -> P={metrics['precision']} R={metrics['recall']} F1={metrics['f1']} "
              f"(FP={metrics['fp']}, davon auf abgelehnten Rallys: {metrics['matched_rejected']})")

out_path = os.path.join(CACHE, "results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nErgebnisse: {out_path}")
