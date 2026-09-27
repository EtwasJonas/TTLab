"""Phase 2 verification: run AFTER the changes, compare with baseline.

1. Bit-identity on the UNROTATED mp4 (match 5): motion scores and ball
   validation hits must be EXACTLY equal to the baseline (V0.5 behaviour).
2. Rotation fix on the 180° iPhone mov (match 2): ball hits should be >=
   baseline (the table mask now sits on the actual table).
3. Fallback behaviour of create_ball_detector (auto/heuristic/ml, broken
   model file).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\Jonas\Documents\OpenCode\ttlab\backend")
from app.rally_detection import RallyDetector  # noqa: E402
from app.ball_detector import HeuristicBallDetector, MLBallDetector, find_model_file  # noqa: E402

OUT_DIR = r"C:\Users\Jonas\AppData\Local\Temp\opencode\phase2-verify"
DB = r"C:\Users\Jonas\Documents\OpenCode\ttlab\data\db\ttlab.db"

import sqlite3


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


with open(f"{OUT_DIR}\\baseline_ball_hits.json", encoding="utf-8") as f:
    baseline = json.load(f)

detector = RallyDetector()
all_ok = True

# --- 1a. Motion bit-identity (match 5, mp4) ---
path5, points5, _ = load_match(5)
motion_after, fps = detector.extract_motion_features(path5, frame_step=1, max_workers=1)
motion_before = np.load(f"{OUT_DIR}\\motion_match5_before.npy")
identical = motion_before.shape == motion_after.shape and bool(np.array_equal(motion_before, motion_after))
print(f"[1a] Motion Bit-Identitaet (MP4): {'PASS' if identical else 'FAIL'} "
      f"({len(motion_after)} Werte, exakt gleich: {identical})")
all_ok &= identical

# --- 1b. Ball validation bit-identity (match 5) ---
hits5 = detector._validate_ball_hits(path5, baseline["match5_groups"], points5, max_workers=1)
same = hits5 == baseline["match5_hits"]
print(f"[1b] Ball-Validierung Bit-Identitaet (MP4): {'PASS' if same else 'FAIL'} "
      f"(vorher {baseline['match5_hits']} / nachher {hits5})")
all_ok &= same

# --- 2. Rotation fix (match 2, 180-Grad iPhone-MOV) ---
path2, points2, _ = load_match(2)
hits2 = detector._validate_ball_hits(path2, baseline["match2_groups"], points2, max_workers=1)
before_sum = sum(baseline["match2_hits"])
after_sum = sum(hits2)
print(f"[2]  Rotations-Fix (MOV, 180 Grad): vorher Summe {before_sum} / nachher Summe {after_sum} "
      f"{'PASS (gleich oder besser)' if after_sum >= before_sum else 'CHECK'}")
print(f"    vorher: {baseline['match2_hits']}")
print(f"    nachher: {hits2}")

# --- 3. Fallback-Verhalten ---
print(f"[3a] Modell-Datei vorhanden: {find_model_file()!r} (erwartet: None)")
d = None
from app import ball_detector as bd_module
det = None
os.environ.pop("TTLAB_BALL_DETECTION", None)
det = bd_module.create_ball_detector()
is_heur = isinstance(det, HeuristicBallDetector)
print(f"[3b] auto-Modus ohne Modell -> Heuristik: {'PASS' if is_heur else 'FAIL'} "
      f"(model_version={det.model_version})")
all_ok &= is_heur

os.environ["TTLAB_BALL_DETECTION"] = "heuristic"
det = bd_module.create_ball_detector()
print(f"[3c] Erzwungene Heuristik: {'PASS' if isinstance(det, HeuristicBallDetector) else 'FAIL'}")
all_ok &= isinstance(det, HeuristicBallDetector)

# Kaputtes Modell-Datei simulieren (Muell-Bytes) im auto-Modus
os.makedirs(bd_module.MODELS_DIR, exist_ok=True)
broken = os.path.join(bd_module.MODELS_DIR, "zz_broken_test.onnx")
with open(broken, "wb") as f:
    f.write(b"not an onnx model")
try:
    os.environ["TTLAB_BALL_DETECTION"] = "auto"
    det = bd_module.create_ball_detector()
    print(f"[3d] Kaputtes Modell -> Rueckfall auf Heuristik: "
          f"{'PASS' if isinstance(det, HeuristicBallDetector) else 'FAIL'}")
    all_ok &= isinstance(det, HeuristicBallDetector)
finally:
    os.remove(broken)
    os.environ.pop("TTLAB_BALL_DETECTION", None)

print()
print("GESAMTERGEBNIS:", "ALLE KRITISCHEN TESTS BESTANDEN" if all_ok else "FEHLER - nicht committen!")
