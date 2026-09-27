# Phase-2-Verifikation (Bit-Identität & Rotations-Fix)

Diese Skripte sind die **Vorlage/Vorarbeit** aus der V0.6-Phase-2-Sitzung und
prüfen Dinge, die echte Videodateien aus `data/` brauchen (nicht als pytest
automatisierbar). Sie werden **nicht** vom pytest-Lauf eingesammelt
(kein `test_`-Präfix).

## Inhalt

| Datei | Zweck |
|-------|-------|
| `capture_baseline.py` | VOR einer Pipeline-Änderung ausführen: speichert Motion-Scores (`.npy`) + Ball-Hits (`.json`) als Bit-Identitäts-Referenz für Match 5 (unrotiertes MP4) und Match 2 (180°-iPhone-MOV) |
| `verify_after.py` | NACH der Änderung ausführen: vergelt Motion/Ball-Hits exakt gegen die Baseline, prüft Rotations-Verhalten + Detektor-Fallback (auto/heuristic/kaputtes Modell) |
| `baseline_ball_hits.json` | Baseline vom 20.09.2026 (V0.6 Phase 2). `motion_match5_before.npy` (72 KB) liegt noch in `%TEMP%\opencode\phase2-verify\` und ist zu groß/beispielgebunden fürs Repo – bei einer neuen Baseline neu erzeugen. |
| (Referenz) `motion_match5_before.npy` | s. o. |

## Nutzung bei Pipeline-Änderungen

1. Pfade in `capture_baseline.py` anpassen (`OUT_DIR`, `DB`, Match-IDs)
2. Auf dem Stand VOR der Änderung: `python capture_baseline.py`
3. Änderung durchführen
4. `python verify_after.py` – Bit-Identität muss PASS sein

## Ergebnis vom 20.09.2026 (Phase 2)

- Bit-Identität Match 5 (MP4, unrotiert): **PASS** (9015 Motion-Werte + Ball-Hits exakt gleich)
- Rotations-Fix Match 2 (MOV, 180°): Ball-Hits 21 → 12 (offene Masken-Frage,
  siehe PROJEKTUEBERGABE.md „OFFENE FRAGE")
- Fallback-Tests (auto/heuristic/kaputtes ONNX): PASS
