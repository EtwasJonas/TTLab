"""One-off migration: re-encode 10-bit (Hi10P) rally clips to 8-bit yuv420p.

Clips created before V0.5.1 were encoded without an explicit pixel format.
For 10-bit sources (HEVC Main 10, e.g. iPhone .mov files) ffmpeg picked
H.264 High 10 (Hi10P, yuv420p10le). Windows Media Player cannot decode
that profile ("unsupported codec settings", error 0x80004005).

This script re-encodes every affected clip in place (video only, audio is
stream-copied). CRF 18 keeps the generational loss minimal since this is
already the second encode. Stale export files (highlights_*.mp4 /
all_rallies_*.mp4) are deleted - they are regenerated on the next download.

Usage (from the backend directory):
    python reencode_clips.py [clips_dir]
"""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_CLIPS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "clips")
)
WORKERS = 6
CLIP_GLOB = "match_"  # files starting with this are rally clips
EXPORT_PREFIXES = ("highlights_", "all_rallies_")


def probe_pix_fmt(path: str) -> str:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=pix_fmt", "-of", "default=nw=1:nk=1",
            path,
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def reencode(path: str) -> float:
    tmp_path = path + ".tmp.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", path,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            "-threads", "2",
            tmp_path,
        ],
        check=True,
        capture_output=True,
    )
    size_before = os.path.getsize(path)
    os.replace(tmp_path, path)
    return size_before


def main() -> None:
    clips_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CLIPS_DIR
    if not os.path.isdir(clips_dir):
        print(f"Clips-Verzeichnis nicht gefunden: {clips_dir}")
        sys.exit(1)

    for name in os.listdir(clips_dir):
        if name.startswith(EXPORT_PREFIXES):
            full = os.path.join(clips_dir, name)
            os.remove(full)
            print(f"Veralteten Export gelöscht: {name}")

    candidates = sorted(
        name for name in os.listdir(clips_dir)
        if name.startswith(CLIP_GLOB) and name.endswith(".mp4")
    )
    todo = []
    for name in candidates:
        full = os.path.join(clips_dir, name)
        if probe_pix_fmt(full) != "yuv420p":
            todo.append(full)
    print(f"{len(candidates)} Clips gefunden, {len(todo)} werden neu encodiert...")

    done = 0
    failed = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(reencode, path): path for path in todo}
        for future in as_completed(futures):
            path = futures[future]
            try:
                future.result()
                done += 1
                print(f"[{done}/{len(todo)}] {os.path.basename(path)}")
            except Exception as exc:  # noqa: BLE001 - report and continue
                failed.append(path)
                print(f"FEHLER bei {os.path.basename(path)}: {exc}")

    if failed:
        print(f"\n{len(failed)} Clips fehlgeschlagen:")
        for path in failed:
            print(f"  {path}")
        sys.exit(1)
    print("Fertig - alle Clips sind jetzt 8-bit yuv420p (Windows Media Player kompatibel).")


if __name__ == "__main__":
    main()
