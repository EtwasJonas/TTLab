"""Ball detection for the rally analysis (V0.6 Phase 2).

Two interchangeable detectors with the SAME interface:

- ``HeuristicBallDetector``: the proven brightness/movement heuristic from
  V0.1-V0.5 (moved 1:1 from ``RallyDetector._is_ball_candidate``). It stays
  the permanent fallback - TTLab works without any model file.
- ``MLBallDetector``: YOLOv8n ONNX inference via onnxruntime (CPU only, no
  torch in the backend). Uses the model trained with the labeling tool
  (backend/ml/train_yolo.py + export_onnx.py).

``create_ball_detector()`` picks one automatically:
``data/models/*.onnx`` present -> ML, otherwise -> heuristic. The choice can
be forced with the environment variable ``TTLAB_BALL_DETECTION``
(``auto`` (default) / ``ml`` / ``heuristic``). A model that fails to load
falls back to the heuristic with a warning instead of breaking an analysis.

Coordinate system: ALL frames passed in here are already rotated to display
orientation (see video_processor.get_display_rotation) - the same
orientation the browser, the labeling tool and the table calibration use.
The heuristic is bit-identical to V0.5 for unrotated videos because
rotate_frame() returns the unchanged array for 0°.
"""

import glob
import os
import threading
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.video_processor import get_display_rotation

# Search path for ONNX models (relative to the backend working directory,
# consistent with the other data/ paths in main.py).
MODELS_DIR = os.getenv("TTLAB_MODELS_DIR", "../data/models")

HEURISTIC_MODEL_VERSION = "heuristic_v0.5"

# MLBallDetector configuration. The confidence threshold is deliberately
# low-ish: the pipeline confirms candidates with audio + motion anyway, so
# recall matters more than precision at this stage.
ML_CONFIDENCE_THRESHOLD = 0.30
ML_INPUT_SIZE = 640


class HeuristicBallDetector:
    """Brightness + movement heuristic (V0.1-V0.5 behaviour, unchanged).

    Detects a white, moving object inside the table area. This class is the
    canonical home of that logic now; ``RallyDetector`` no longer carries
    its own copy.
    """

    model_version = HEURISTIC_MODEL_VERSION
    # The heuristic returns only a yes/no decision - no ball center. The
    # rally gate (see rally_detection.rally_gate_flag) therefore stays
    # inactive with this detector.
    provides_positions = False

    def is_ball_candidate(
        self,
        before: np.ndarray,
        mid: np.ndarray,
        after: np.ndarray,
        mask: np.ndarray,
    ) -> bool:
        """Detect a white, moving object inside the table area."""
        before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        mid_gray = cv2.cvtColor(mid, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

        move1 = cv2.absdiff(before_gray, mid_gray)
        move2 = cv2.absdiff(mid_gray, after_gray)
        movement = cv2.addWeighted(move1, 0.5, move2, 0.5, 0)
        _, movement_thresh = cv2.threshold(movement, 25, 255, cv2.THRESH_BINARY)

        bright = cv2.inRange(after, np.array([180, 180, 180]), np.array([255, 255, 255]))

        candidate_mask = cv2.bitwise_and(movement_thresh, bright)
        candidate_mask = cv2.bitwise_and(candidate_mask, mask)
        candidate_mask = cv2.morphologyEx(candidate_mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        candidate_mask = cv2.dilate(candidate_mask, np.ones((3, 3), np.uint8), iterations=1)

        contours, _ = cv2.findContours(candidate_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return any(3 <= cv2.contourArea(contour) <= 250 for contour in contours)


class MLBallDetector:
    """YOLOv8n ball detection via onnxruntime (CPU, no torch required).

    The session is thread-safe: all ball validation workers share ONE
    session, which keeps memory low and lets onnxruntime parallelize
    internally. Preprocessing mirrors the ultralytics letterbox pipeline
    exactly, because the model was trained on the labeling tool's images.
    """

    provides_positions = True

    def __init__(self, model_path: str, confidence: float = ML_CONFIDENCE_THRESHOLD):
        import onnxruntime as ort

        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Modell nicht gefunden: {model_path}")

        self.model_path = model_path
        self.confidence = confidence
        self.model_version = os.path.splitext(os.path.basename(model_path))[0]

        # CPU only - the backend must never require a GPU (and the whole
        # point of ONNX here is portability for the future .exe).
        self.session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        input_shape = self.session.get_inputs()[0].shape  # e.g. [?, 3, 640, 640]
        self.input_size = ML_INPUT_SIZE
        if isinstance(input_shape[2], int) and input_shape[2] > 0:
            self.input_size = int(input_shape[2])

        # Lock around session.run: run() itself is thread-safe, but the
        # lock keeps CPU usage predictable when many workers fire at once.
        self._lock = threading.Lock()

    def _letterbox(self, frame: np.ndarray):
        """Ultralytics-style letterbox: scale + pad to input_size, value 114."""
        size = self.input_size
        h, w = frame.shape[:2]
        scale = min(size / h, size / w)
        new_w, new_h = round(w * scale), round(h * scale)
        pad_x = (size - new_w) / 2.0
        pad_y = (size - new_h) / 2.0

        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((size, size, 3), 114, dtype=np.uint8)
        x0, y0 = int(round(pad_x)), int(round(pad_y))
        canvas[y0:y0 + new_h, x0:x0 + new_w] = resized
        return canvas, scale, pad_x, pad_y

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        canvas, _scale, _px, _py = self._letterbox(frame)
        # BGR -> RGB, HWC -> CHW, 0..255 -> 0..1 (ultralytics convention)
        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        chw = np.transpose(rgb, (2, 0, 1))
        blob = (chw.astype(np.float32) / 255.0)[None, ...]
        return np.ascontiguousarray(blob)

    def detect(self, frame: np.ndarray) -> List[List[float]]:
        """Return all detections above the confidence threshold as
        [cx, cy, w, h, conf] in ORIGINAL frame pixel coordinates."""
        blob = self._preprocess(frame)
        with self._lock:
            outputs = self.session.run(None, {self.input_name: blob})
        preds = outputs[0]

        # Ultralytics YOLOv8 export: shape (batch, 4 + nc, N) with nc=1
        # -> (batch, 5, N): rows are cx, cy, w, h (input coords), conf.
        if preds.ndim == 3 and preds.shape[1] == 5:
            detections = preds[0].T  # (N, 5)
        elif preds.ndim == 3 and preds.shape[-1] == 5:
            detections = preds[0]  # already (N, 5)
        else:
            raise ValueError(f"Unerwartetes Modell-Output-Format: {preds.shape}")

        keep = detections[:, 4] >= self.confidence
        detections = detections[keep]
        if len(detections) == 0:
            return []

        # Undo the letterbox to get original pixel coordinates.
        h, w = frame.shape[:2]
        scale = min(self.input_size / h, self.input_size / w)
        pad_x = (self.input_size - round(w * scale)) / 2.0
        pad_y = (self.input_size - round(h * scale)) / 2.0

        result = []
        for cx, cy, bw, bh, conf in detections:
            result.append([
                (float(cx) - pad_x) / scale,
                (float(cy) - pad_y) / scale,
                float(bw) / scale,
                float(bh) / scale,
                float(conf),
            ])
        return result

    def is_ball_candidate(
        self,
        before: np.ndarray,
        mid: np.ndarray,
        after: np.ndarray,
        mask: np.ndarray,
    ) -> bool:
        """True if the model finds a ball inside the table area."""
        hit, _center = self.is_ball_candidate_pos(before, mid, after, mask)
        return hit

    def is_ball_candidate_pos(
        self,
        before: np.ndarray,
        mid: np.ndarray,
        after: np.ndarray,
        mask: np.ndarray,
    ) -> Tuple[bool, Optional[Tuple[float, float]]]:
        """Like is_ball_candidate, but also returns the ball center.

        The center is normalized to the mask (display-frame) coordinates
        (cx/mask_w, cy/mask_h) or None. The rally gate uses these positions
        to tell a real rally (ball flying across the table) from pure ball
        handling like hopping or throwing (ball stays local).
        """
        try:
            detections = self.detect(mid)
        except Exception as e:  # noqa: BLE001 - never crash an analysis
            print(f"[WARNUNG] ML-Ballerkennung fehlgeschlagen ({e}) - Peak gilt als ohne Ball")
            return False, None

        mask_h, mask_w = mask.shape[:2]
        best = None
        for cx, cy, _bw, _bh, conf in detections:
            x, y = int(round(cx)), int(round(cy))
            if 0 <= x < mask_w and 0 <= y < mask_h and mask[y, x] == 255:
                if best is None or conf > best[2]:
                    best = (cx, cy, conf)
        if best is None:
            return False, None
        return True, (best[0] / mask_w, best[1] / mask_h)


def find_model_file() -> Optional[str]:
    """Newest .onnx in the models directory, or None."""
    if not os.path.isdir(MODELS_DIR):
        return None
    candidates = glob.glob(os.path.join(MODELS_DIR, "*.onnx"))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def create_ball_detector() -> "object":
    """Pick the ball detector (see module docstring for the rules)."""
    mode = os.getenv("TTLAB_BALL_DETECTION", "auto").lower()
    if mode not in {"auto", "ml", "heuristic"}:
        print(f"[WARNUNG] Ungültiger TTLAB_BALL_DETECTION={mode!r} - verwende 'auto'")
        mode = "auto"

    if mode in {"auto", "ml"}:
        model_path = find_model_file()
        if model_path:
            try:
                detector = MLBallDetector(model_path)
                print(
                    f"[OK] ML-Ballerkennung aktiv: {os.path.basename(model_path)} "
                    f"(Confidence >= {detector.confidence})"
                )
                return detector
            except Exception as e:  # noqa: BLE001 - fall back, never break
                print(
                    f"[WARNUNG] ML-Modell konnte nicht geladen werden ({e}) - "
                    f"weiche auf die Heuristik aus"
                )
        elif mode == "ml":
            print("[WARNUNG] TTLAB_BALL_DETECTION=ml, aber kein Modell in "
                  f"{os.path.abspath(MODELS_DIR)} gefunden - verwende Heuristik")

    return HeuristicBallDetector()
