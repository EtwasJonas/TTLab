#!/usr/bin/env python3
"""Train the TTLab ball-detection model (YOLOv8n) on the labeled dataset.

Runs on the TRAINING machine (Linux Mint desktop with GTX 1050), NOT on
the TTLab server. The backend itself never needs torch/ultralytics - it
only consumes the exported ONNX model (see export_onnx.py).

Workflow (see README.md in this folder for the full guide):
  1. Label frames in the TTLab UI (frontend route /labeling)
  2. Click "Trainings-Export erstellen" (creates <dataset>/yolo/ + data.yaml)
  3. Copy the dataset folder to the training machine
  4. Run this script:
         python train_yolo.py --dataset baelle_v1
  5. Export the best weights to ONNX:
         python export_onnx.py

Hardware notes for the GTX 1050 (2 GB VRAM):
  - batch=8 and imgsz=640 fit into 2 GB with AMP (mixed precision) enabled
  - if CUDA runs out of memory: reduce --batch to 4 or --imgsz to 512
  - 500-1000 labeled frames need roughly 50-100 epochs; training takes
    about 2-4 hours on a GTX 1050
"""

import argparse
import os
import sys
import tempfile

# Repo-Layout: data/ liegt am Projektstamm (TTLab/data/datasets), das Skript
# in backend/ml/ - daher zwei Ebenen hoch.
DEFAULT_DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "datasets")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dataset",
        required=True,
        help="Name des Datensatzes (Ordner unter data/datasets/, z.B. baelle_v1)",
    )
    parser.add_argument(
        "--datasets-dir",
        default=DEFAULT_DATASETS_DIR,
        help="Basis-Ordner der Datensätze (Default: ../data/datasets relativ zu diesem Skript)",
    )
    parser.add_argument("--epochs", type=int, default=100, help="Anzahl Trainingsepochen (Default: 100)")
    parser.add_argument("--batch", type=int, default=8, help="Batch-Größe (Default: 8; bei CUDA-OOM auf 4 senken)")
    parser.add_argument("--imgsz", type=int, default=640, help="Bildgröße (Default: 640)")
    parser.add_argument("--device", default="0", help="Gerät: '0' für GPU (Default), 'cpu' für CPU-Training")
    parser.add_argument("--workers", type=int, default=4, help="Data-Loader-Worker (Default: 4)")
    parser.add_argument(
        "--name", default="ball_yolov8n", help="Name des Trainings-Laufs (Ergebnis unter runs/<name>)"
    )
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[FEHLER] ultralytics ist nicht installiert.")
        print("         Auf dem Trainings-Rechner ausführen:")
        print("           python -m venv venv-ml && source venv-ml/bin/activate")
        print("           pip install ultralytics")
        return 1

    # Sanity check: CUDA available when a GPU was requested?
    if str(args.device) not in ("cpu", "-1"):
        try:
            import torch

            if torch.cuda.is_available():
                print(f"[OK] CUDA verfügbar: {torch.cuda.get_device_name(0)}")
            else:
                print("[WARNUNG] CUDA ist NICHT verfügbar - Training läuft auf der CPU (sehr langsam)!")
                print("          PyTorch ggf. mit CUDA-Support neu installieren (siehe README.md).")
        except Exception as e:  # noqa: BLE001 - torch diagnostics must not crash the run
            print(f"[WARNUNG] CUDA-Prüfung fehlgeschlagen: {e}")

    yolo_dir = os.path.abspath(os.path.join(args.datasets_dir, args.dataset, "yolo"))
    data_yaml = os.path.join(yolo_dir, "data.yaml")
    if not os.path.isfile(data_yaml):
        print(f"[FEHLER] {data_yaml} nicht gefunden.")
        print("         Zuerst im TTLab-Labeling-Tool den Trainings-Export erstellen")
        print("         (Button 'Trainings-Export erstellen') und den Datensatz-Ordner")
        print("         auf diesen Rechner kopieren.")
        return 1

    print(f"[OK] Datensatz: {yolo_dir}")

    # Ultralytics 8.x resolves a RELATIVE 'path' in data.yaml against the
    # CURRENT WORKING DIRECTORY, not against the yaml file - training from
    # backend/ml would look for images in the wrong place. We therefore
    # write a temporary yaml with the ABSOLUTE dataset dir. The exported
    # data.yaml stays untouched (it remains portable in the ZIP).
    import yaml

    with open(data_yaml, encoding="utf-8-sig") as f:
        data_cfg = yaml.safe_load(f) or {}
    data_cfg["path"] = yolo_dir
    tmp_fd, tmp_yaml = tempfile.mkstemp(prefix="ttlab_data_", suffix=".yaml")
    with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(data_cfg, f, allow_unicode=True, sort_keys=False)
    print(f"[OK] Pfad absolutisiert (temporäre YAML: {tmp_yaml})")

    model = YOLO("yolov8n.pt")  # nano variant: smallest, fastest, enough for one class
    results = model.train(
        data=tmp_yaml,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        workers=args.workers,
        project=os.path.join(os.path.dirname(__file__), "runs"),
        name=args.name,
        # 2 GB VRAM tips: AMP is on by default and essential; do not cache
        # images on the GPU (cache=False keeps VRAM free for activations).
        cache=False,
        amp=True,
        # Small dataset -> augmentations help generalization across
        # lighting conditions and camera angles.
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=2.0,
        translate=0.1,
        scale=0.3,
        flipud=0.0,   # no vertical flips: the ball moves in a real scene
        fliplr=0.5,
        mosaic=0.5,
    )

    best = os.path.join(str(results.save_dir), "weights", "best.pt")
    print("\n[OK] Training abgeschlossen.")
    print(f"     Beste Gewichte: {best}")
    print("     Nächster Schritt: python export_onnx.py --weights " + best)
    return 0


if __name__ == "__main__":
    sys.exit(main())
