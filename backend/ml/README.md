# TTLab ML-Training (V0.6: Ball-Erkennung YOLOv8n)

Dieses Verzeichnis enthält die Skripte zum Trainieren des Ball-Tracking-Modells.
Die Skripte laufen **auf dem Trainings-Rechner** (Desktop mit GTX 1050, Linux
Mint) – **nicht** auf dem TTLab-Server. Das Backend benötigt später nur die
exportierte ONNX-Datei und `onnxruntime` (kein PyTorch!).

## Dateien

| Datei | Zweck |
|-------|-------|
| `train_yolo.py` | Trainiert YOLOv8n auf einem exportierten Datensatz |
| `export_onnx.py` | Konvertiert die trainierten Gewichte nach ONNX |

## Kompletter Workflow

### 1. Frames labeln (auf dem Laptop mit TTLab)

1. TTLab starten, oben rechts **Labeling** öffnen
2. Datensatz erstellen (z.B. `baelle_v1`) und Video wählen
3. Frames durchgehen: Rechteck um den Ball ziehen (Auto-Speichern speichert
   und springt weiter) oder **N** für "kein Ball sichtbar"
4. Ziel: 500–1000 Frames aus verschiedenen Videos/Beleuchtungen;
   auch Negativ-Frames (Gehen, Aufschlag-Vorbereitung) sind wertvoll!

### 2. Trainings-Export erstellen (in TTLab)

In der Labeling-Ansicht des Datensatzes auf **„Trainings-Export erstellen"**
klicken. Es entsteht `data/datasets/<name>/yolo/` mit `images/train`,
`images/val`, `labels/...` und `data.yaml` (80/20-Split, deterministisch).

### 3. Datensatz auf den Trainings-Rechner kopieren

```bash
# z.B. per USB-Stick oder scp – der Ordner reicht aus:
data/datasets/baelle_v1/
```

Der Trainings-Rechner braucht nur diesen Ordner + die beiden Skripte aus
`backend/ml/` (gleiche relative Struktur: `<projekt>/data/datasets/...`).

### 4. Umgebung einrichten (einmalig, Linux Mint)

```bash
sudo apt update && sudo apt install python3-venv
cd ttlab/backend/ml
python3 -m venv venv-ml
source venv-ml/bin/activate
pip install ultralytics
```

> `ultralytics` zieht PyTorch inkl. CUDA-Unterstützung (~2,5 GB Download).
> Die GTX 1050 (Pascal, compute 6.1) wird von aktuellen Torch-Builds
> unterstützt.

CUDA prüfen:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# Erwartet: True NVIDIA GeForce GTX 1050
```

Falls `False`: NVIDIA-Treiber prüfen (`nvidia-smi`) und ggf. die
CUDA-Variante von PyTorch installieren (siehe pytorch.org-Anleitung).

### 5. Training starten

```bash
python train_yolo.py --dataset baelle_v1
```

Empfohlene Standardwerte sind bereits gesetzt (`batch=8`, `imgsz=640`,
`epochs=100`, AMP an) und auf **2 GB VRAM** ausgelegt.

- **CUDA out of memory** → `--batch 4` oder `--imgsz 512`
- Dauer: ca. 2–4 Stunden für 500–1000 Frames
- Ergebnisse landen in `runs/ball_yolov8n/` (beste Gewichte:
  `runs/ball_yolov8n/weights/best.pt`, Metriken in `results.png`)

### 6. Nach ONNX exportieren

```bash
python export_onnx.py
# oder mit explizitem Pfad:
python export_onnx.py --weights runs/ball_yolov8n/weights/best.pt
```

### 7. Modell in TTLab einbinden

Die Datei `ball_yolov8n.onnx` auf den TTLab-Rechner kopieren nach:

```
data/models/ball_yolov8n.onnx
```

Sobald die Datei existiert, nutzt die Ball-Erkennung das ML-Modell
(V0.6-Integration). **Fehlt die Datei, greift automatisch die bisherige
Helligkeits-Heuristik** – TTLab funktioniert also jederzeit ohne Modell.

## Qualität prüfen

Nach dem Training in `runs/ball_yolov8n/`:

- `results.png`: Verlauf von Precision/Recall/mAP – mAP50 sollte für den
  Start **> 0.7** erreichen (Ball ist ein einfaches, einzelnes Objekt)
- `confusion_matrix.png`: FALSE-Positive-Rate
- Liefert das Modell zu viele Fehlalarme: mehr Negativ-Frames labeln
  (Frames ohne Ball aus Szenen mit Bewegung/weißen Objekten)

## Häufige Probleme

| Problem | Lösung |
|---------|--------|
| `CUDA out of memory` | `--batch 4`, `--imgsz 512` |
| `torch.cuda.is_available() == False` | `nvidia-smi` prüfen, Treiber aktualisieren |
| Training sehr langsam (CPU) | `--device 0` explizit setzen; sonst läuft CPU |
| mAP zu niedrig | Mehr/diversere Frames labeln, Negativ-Frames ergänzen, mehr Epochs |
