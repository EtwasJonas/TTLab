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

### 3. Datensatz auf den Trainings-Rechner übertragen

Nach dem Klick auf **„Trainings-Export erstellen"** wird der Export erstellt und
**automatisch als ZIP heruntergeladen** (alternativ später per Button
„⬇ ZIP erneut herunterladen"). Die ZIP enthält den fertigen Export:

```
v1-ml-training_yolo/
├── data.yaml          (portabel: relativer Pfad, train_yolo.py absolutisiert zur Laufzeit)
├── images/train/  +  images/val/
└── labels/train/  +  labels/val/
```

**Ablageort (wichtig):** ZIP entpacken, den Ordner `v1-ml-training_yolo` in
`yolo` umbenennen und unter `<projekt>/data/datasets/v1-ml-training/` ablegen:

```bash
cd <projekt>
mkdir -p data/datasets/v1-ml-training
mv ~/v1-ml-training_yolo data/datasets/v1-ml-training/yolo
ls data/datasets/v1-ml-training/yolo/data.yaml   # muss existieren
```

`train_yolo.py` sucht per Default genau dort (`data/datasets` am Projektstamm).

### 4. Umgebung einrichten (einmalig, Linux Mint)

**Achtung GTX 1050 (Pascal, sm_61):** aktuelle PyTorch-Builds (CUDA 12.6/13.0)
enthalten **keine Kernels mehr für sm_61** – `pip install ultralytics` zieht
trotzdem einen solchen Build und das Training stürzt mit „no kernel image
available" ab. Deshalb zuerst ultralytics, dann Torch **explizit als cu118-Build**
(die letzte Wheel-Generation mit Pascal-Support) drüber installieren:

```bash
sudo apt update && sudo apt install python3-venv
cd ttlab/backend/ml
python3 -m venv venv-ml
source venv-ml/bin/activate
pip install ultralytics
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu118
```

CUDA-Kernels prüfen – **sm_61 muss in der Liste stehen**, und der echte
Kernel-Test muss eine Zahl ausgeben:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.get_arch_list())"
python -c "import torch; x = torch.randn(8, 8, device='cuda'); print((x @ x).sum().item())"
# Erwartet: 2.5.1+cu118 [... 'sm_61' ...] und eine Zahl
```

Falls sm_61 fehlt oder der Kernel-Test abstürzt: Treiber prüfen (`nvidia-smi`).

### 5. Training starten

```bash
python train_yolo.py --dataset v1-ml-training
```

(Default `--datasets-dir` ist `data/datasets` am Projektstamm; abweichende
Ablageorte per `--datasets-dir` angeben.)

**Keine manuellen Pfad-Anpassungen nötig:** Ultralytics löst ein relatives
`path:` in data.yaml gegen das Arbeitsverzeichnis auf (nicht gegen die YAML) –
das Skript schreibt deshalb vor dem Training automatisch eine temporäre YAML
mit absolutem Pfad. Das exportierte `data.yaml` bleibt unverändert portabel.

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

Nach dem Training in `runs/<name>/`:

- `results.png`: Verlauf von Precision/Recall/mAP – mAP50 sollte für den
  Start **> 0.7** erreichen (Ball ist ein einfaches, einzelnes Objekt)
- `confusion_matrix.png`: FALSE-Positive-Rate
- Liefert das Modell zu viele Fehlalarme: mehr Negativ-Frames labeln
  (Frames ohne Ball aus Szenen mit Bewegung/weißen Objekten)

## Evaluation gegen die Ground-Truth (auf dem TTLab-Rechner)

`evaluate.py` läuft **im Backend-venv** (nicht im venv-ml – es braucht cv2/
librosa/onnxruntime, kein torch) und vergleicht komplette Erkennungsläufe
gegen die manuell validierten Rallys in der DB (accepted = echt, rejected =
kein Rally). Motion+Audio werden pro Video einmal berechnet und im Temp-
Ordner gecacht – Wechsel zwischen Detektoren/Faktoren sind danach billig:

```bash
cd ttlab/backend
python ml/evaluate.py --match 5 --detectors heuristic --factors 0.0        # schnell
python ml/evaluate.py --match 2 --detectors heuristic,ml --factors 0.0,0.5,1.0
```

Voraussetzung für `--detectors ml`: `data/models/*.onnx` auf diesem Rechner.
Ergebnisse landen in `ml/evaluate_results.json` (nicht eingecheckt).

## Häufige Probleme

| Problem | Lösung |
|---------|--------|
| `no kernel image is available for execution on the device` | Falscher Torch-Build für GTX 1050 (sm_61): `pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu118` (siehe Schritt 4) |
| `CUDA out of memory` | `--batch 4`, `--imgsz 512` |
| `torch.cuda.is_available() == False` | `nvidia-smi` prüfen, Treiber aktualisieren |
| `Dataset '...' images not found, missing path '.../images/val'` | Training aus einem Ordner mit relativem `path: .` in data.yaml gestartet – aktuellen `train_yolo.py` nutzen (absolutisiert automatisch) oder Skript aus dem yolo-Ordner heraus starten |
| Training sehr langsam (CPU) | `--device 0` explizit setzen; sonst läuft CPU |
| mAP zu niedrig | Mehr/diversere Frames labeln, Negativ-Frames ergänzen, mehr Epochs |
