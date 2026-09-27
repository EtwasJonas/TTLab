"""Baseline capture BEFORE the Phase 2 changes (bit-identity reference).

Captures for the UNROTATED mp4 (match 5):
  - motion scores (frame_step=1, 1 worker, full resolution -> the
    documented bit-identity configuration)
  - ball validation hits for rally peak groups
And for the ROTATED iPhone mov (match 2):
  - ball validation hits (expected to improve after the rotation fix)

Results are stored as .npy/.json next to this script for the after-compare.
"""
import json
import sqlite3
import sys
import time

import numpy as np

sys.path.insert(0, r"C:\Users\Jonas\Documents\OpenCode\ttlab\backend")
from app.rally_detection import RallyDetector  # noqa: E402

OUT_DIR = r"C:\Users\Jonas\AppData\Local\Temp\opencode\phase2-verify"

DB = r"C:\Users\Jonas\Documents\OpenCode\ttlab\data\db\ttlab.db"


def load_match(match_id):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    row = con.execute(
        "SELECT file_path, table_points FROM matches WHERE id=?", (match_id,)
    ).fetchone()
    rallies = con.execute(
        "SELECT start_time, end_time FROM rallies WHERE match_id=? ORDER BY start_time",
        (match_id,),
    ).fetchall()
    con.close()
    return row[0], json.loads(row[1]) if row[1] else None, rallies


def peak_groups_from_rallies(rallies, max_groups=8, peaks_per_group=5):
    """Synthetic peak times inside real rally intervals for ball validation."""
    groups = []
    for start, end in rallies[:max_groups]:
        span = end - start
        step = max(0.15, (span * 0.6) / peaks_per_group)
        base = start + span * 0.2
        groups.append([round(base + i * step, 3) for i in range(peaks_per_group)])
    return groups


detector = RallyDetector()

# --- Match 5 (mp4, unrotated): motion + ball validation baseline ---
path5, points5, rallies5 = load_match(5)
print(f"Match 5: {len(rallies5)} Rallys, Tischpunkte: {bool(points5)}")

t0 = time.time()
motion_scores, fps = detector.extract_motion_features(path5, frame_step=1, max_workers=1)
print(f"Motion: {len(motion_scores)} Werte in {time.time()-t0:.1f}s (fps={fps})")
np.save(f"{OUT_DIR}\\motion_match5_before.npy", motion_scores)

groups5 = peak_groups_from_rallies(rallies5)
t0 = time.time()
hits5 = detector._validate_ball_hits(path5, groups5, points5, max_workers=1)
print(f"Ball-Validierung Match 5: {hits5} in {time.time()-t0:.1f}s")

# --- Match 2 (iPhone mov, 180 Grad): ball validation baseline ---
path2, points2, rallies2 = load_match(2)
print(f"\nMatch 2: {len(rallies2)} Rallys, Tischpunkte: {bool(points2)}")
groups2 = peak_groups_from_rallies(rallies2)
t0 = time.time()
hits2 = detector._validate_ball_hits(path2, groups2, points2, max_workers=1)
print(f"Ball-Validierung Match 2 (VORHER, Rotation noch nicht gefixt): {hits2} in {time.time()-t0:.1f}s")

with open(f"{OUT_DIR}\\baseline_ball_hits.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "match5_groups": groups5,
            "match5_hits": hits5,
            "match2_groups": groups2,
            "match2_hits": hits2,
        },
        f,
        indent=2,
    )
print("\nBaseline gespeichert.")
