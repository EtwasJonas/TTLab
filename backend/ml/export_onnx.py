#!/usr/bin/env python3
"""Export the trained ball-detection model to ONNX for the TTLab backend.

The TTLab backend uses ONNX Runtime (CPU) for ball detection - it does NOT
need torch or ultralytics installed. This script converts the trained
PyTorch weights into a portable ONNX file:

    python export_onnx.py --weights runs/ball_yolov8n/weights/best.pt

The exported model is copied to data/models/ball_yolov8n.onnx (relative to
the project root). Copy that file to the same path on the machine running
the TTLab backend - the V0.6 integration picks it up automatically and
falls back to the old heuristic ball detection when it is missing.
"""

import argparse
import os
import shutil
import sys

DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), "runs", "ball_yolov8n", "weights", "best.pt")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "models", "ball_yolov8n.onnx")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weights", default=DEFAULT_WEIGHTS, help="Pfad zu best.pt (Default: runs/ball_yolov8n/weights/best.pt)")
    parser.add_argument("--imgsz", type=int, default=640, help="Bildgröße des Exports (Default: 640, muss dem Training entsprechen)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Zielpfad der ONNX-Datei (Default: data/models/ball_yolov8n.onnx)")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[FEHLER] ultralytics ist nicht installiert (pip install ultralytics).")
        return 1

    if not os.path.isfile(args.weights):
        print(f"[FEHLER] Gewichte nicht gefunden: {args.weights}")
        print("         Zuerst train_yolo.py ausführen oder --weights anpassen.")
        return 1

    print(f"[OK] Lade Gewichte: {args.weights}")
    model = YOLO(args.weights)

    # dynamic=True keeps the batch dimension flexible so the backend can
    # later score single frames or small frame groups in one inference.
    # opset 12 is supported by all current onnxruntime builds.
    export_path = model.export(
        format="onnx",
        imgsz=args.imgsz,
        opset=12,
        dynamic=True,
        simplify=True,
    )

    target = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copy2(export_path, target)
    print(f"[OK] ONNX-Modell exportiert: {target}")
    print("     Auf dem TTLab-Rechner in den Ordner data/models/ kopieren -")
    print("     dort wird es von der Ball-Erkennung (V0.6) automatisch verwendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
