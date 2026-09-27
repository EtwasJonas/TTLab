import cv2
import numpy as np
import librosa
from scipy import signal
from typing import Callable, List, Tuple, Optional, Tuple
import os
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.ball_detector import HeuristicBallDetector, create_ball_detector
from app.video_processor import get_display_rotation, rotate_frame


def play_zone_polygon(polygon: np.ndarray, factor: float) -> np.ndarray:
    """Expand a table polygon (pixel coords) upward into the play zone.

    factor 0.0 = the table surface itself (V0.5 behaviour, bit-identical).
    factor 1.0 = additionally the airspace one table height ABOVE the
    surface - the ball flies there between hits, so ball validation must
    see it (the table-plate-only mask catches the ball only at bounce
    points).

    The expansion is the convex hull of the table polygon plus a copy
    shifted straight up by factor * polygon height. This follows the
    table's tilt (camera perspective) instead of assuming a level table
    and never widens the zone sideways beyond the table edges.
    """
    factor = max(0.0, min(3.0, float(factor)))
    if factor <= 0.0:
        return polygon
    poly_height = float(polygon[:, 1].max() - polygon[:, 1].min())
    if poly_height <= 0:
        return polygon
    shifted = polygon.copy()
    shifted[:, 1] -= int(round(factor * poly_height))
    merged = np.vstack([polygon, shifted])
    hull = cv2.convexHull(merged)
    return hull.reshape(-1, 2)


class RallyDetector:
    def __init__(self, motion_threshold: float = 15.0, audio_threshold: float = 0.3):
        self.motion_threshold = motion_threshold
        self.audio_threshold = audio_threshold
        self.min_rally_duration = 2.5  # Reduced from 3.5 to catch shorter rallies
        self.min_pause_duration = 0.7
        self.rally_buffer_start = 0.8  # Reduced from 1.2
        self.rally_buffer_end = 0.3  # Reduced from 0.5
        self.max_rally_duration = 12.0  # Reduced from 15.0
        self.min_impact_count = 3  # Reduced from 4
        self.serve_detection_window = 2.0  # Window for serve detection
        self.table_roi_weight = 0.8  # Weight for table ROI in motion detection
        self.group_gap = 1.25  # Max gap between impacts within one rally
        # A freely bouncing ball (picked up and thrown over the table, or
        # bouncing out after the last hit) produces impacts with shrinking
        # gaps AND shrinking loudness. A real rally keeps steady gaps and
        # alternating loudness (hit loud, bounce quiet, hit loud, ...).
        self.bounce_height_decay = 0.95
        self.bounce_interval_decay = 0.85
        self.bounce_entry_ratio = 0.9
        # Highlight heuristics: impact sounds include both the hit and the
        # table bounce (~2 sounds per ball contact), so "many impacts" means
        # roughly 2x the number of hits. The thresholds are deliberately
        # strict so that only the top ~10-15% of rallies are highlighted:
        # 10s+ marathon rallies, ~12+ real hits (24 sounds), or a combined
        # score close to the best rally of the same video. The score
        # threshold is relative because the absolute score scale varies
        # per recording.
        self.highlight_min_duration = 10.0
        self.highlight_min_impacts = 24
        self.highlight_score_ratio = 0.9
        # How the ball validation reads frames at a peak time: "single"
        # seeks once and reads forward (fast), "triple" seeks three times
        # (previous behaviour). Kept switchable so the equivalence test can
        # fall back to "triple" if frame selection ever differs.
        self.ball_seek_mode = "single"
        # V0.6 play zone: how far the ball-validation mask extends above the
        # table surface, in table heights (TTLAB_PLAY_ZONE, default 0.0 =
        # table plate only = bit-identical V0.5 behaviour). The value is
        # validated against the user's ground truth - see PROJEKTUEBERGABE.
        self.play_zone_factor = max(0.0, min(3.0, float(os.getenv("TTLAB_PLAY_ZONE", "0.0"))))

    def classify_highlight(
        self,
        duration: float,
        impact_count: int,
        score: float,
        max_score: float,
    ) -> Tuple[bool, float]:
        """Classify a rally as highlight based on duration, impact count and
        its combined score relative to the best rally of the same video."""
        is_highlight = False
        highlight_score = 0.0

        if duration >= self.highlight_min_duration:
            is_highlight = True
            highlight_score = max(highlight_score, min(1.0, duration / 15.0))

        if impact_count >= self.highlight_min_impacts:
            is_highlight = True
            highlight_score = max(highlight_score, min(1.0, impact_count / 30.0))

        if max_score > 0.0 and score >= self.highlight_score_ratio * max_score:
            is_highlight = True
            highlight_score = max(highlight_score, min(1.0, score / max_score))

        return is_highlight, round(highlight_score, 3)

    def extract_motion_features(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        table_points: Optional[List[Tuple[float, float]]] = None,
        frame_step: int = 1,
        max_workers: int = 1,
        max_width: Optional[int] = None,
    ) -> Tuple[np.ndarray, float]:
        """Extract a motion score per analysed frame.

        frame_step > 1 analyses only every n-th frame (cheaper, slightly
        coarser motion trace). max_width downscales frames before analysis
        (background mode). With frame_step=1, max_workers=1 and no
        max_width the result is bit-identical to the original single-threaded
        implementation. With max_workers > 1 the video is decoded in
        parallel time segments (one VideoCapture per worker), which is also
        bit-identical because every frame is decoded by the same decoder.
        The returned fps is the effective fps (fps/frame_step).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        # Analyze frames in DISPLAY orientation (phone videos record with a
        # display-matrix rotation that OpenCV ignores). The table points
        # were calibrated on the rotated browser view, so the mask only
        # matches when frames are rotated the same way. rotate_frame() is
        # a no-op for 0° (no copy) - unrotated videos stay bit-identical.
        rotation = get_display_rotation(video_path)
        if rotation in (90, 270):
            width, height = height, width

        if max_width and width > max_width:
            scale = max_width / width
            proc_width = max_width
            proc_height = max(1, int(round(height * scale)))
            blur_k = max(5, int(round(21 * scale)) | 1)
        else:
            scale = 1.0
            proc_width, proc_height = width, height
            blur_k = 21

        # Prepare table mask and areas ONCE (identical math to recomputing
        # them per frame, without the per-frame allocation overhead).
        table_mask = None
        inv_mask = None
        table_area = 1
        outside_area = 1
        if table_points and len(table_points) == 4:
            polygon = np.array(
                [[int(x * proc_width), int(y * proc_height)] for x, y in table_points],
                dtype=np.int32,
            )
            table_mask = np.zeros((proc_height, proc_width), dtype=np.uint8)
            cv2.fillPoly(table_mask, [polygon], 255)
            inv_mask = cv2.bitwise_not(table_mask)
            table_area = max(int(cv2.countNonZero(table_mask)), 1)
            outside_area = max(int(cv2.countNonZero(inv_mask)), 1)

        def to_gray(frame: np.ndarray) -> np.ndarray:
            frame = rotate_frame(frame, rotation)
            if scale != 1.0:
                frame = cv2.resize(frame, (proc_width, proc_height), interpolation=cv2.INTER_AREA)
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        def blur_gray(gray: np.ndarray) -> np.ndarray:
            return cv2.GaussianBlur(gray, (blur_k, blur_k), 0)

        def motion_score(prev_blur: np.ndarray, cur_blur: np.ndarray) -> float:
            frame_diff = cv2.absdiff(prev_blur, cur_blur)
            if table_mask is not None:
                table_motion = cv2.bitwise_and(frame_diff, frame_diff, mask=table_mask)
                outside_motion = cv2.bitwise_and(frame_diff, frame_diff, mask=inv_mask)
                table_score = cv2.countNonZero(
                    cv2.threshold(table_motion, 25, 255, cv2.THRESH_BINARY)[1]
                ) / table_area
                outside_score = cv2.countNonZero(
                    cv2.threshold(outside_motion, 25, 255, cv2.THRESH_BINARY)[1]
                ) / outside_area
                return self.table_roi_weight * table_score + (1 - self.table_roi_weight) * outside_score
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
            return cv2.countNonZero(thresh) / thresh.size

        def read_next(cap: "cv2.VideoCapture") -> Optional[np.ndarray]:
            if frame_step > 1:
                for _ in range(frame_step - 1):
                    if not cap.grab():
                        return None
            ret, frame = cap.read()
            return frame if ret else None

        progress_every = max(int(fps * 2 / max(frame_step, 1)), 1)
        est_total = frame_count / max(frame_step, 1) if frame_count else 0

        analyzed_counter = [0]
        progress_lock = threading.Lock()

        def report_frame() -> None:
            with progress_lock:
                analyzed_counter[0] += 1
                analyzed = analyzed_counter[0]
            if progress_callback and frame_count and analyzed % progress_every == 0:
                progress_callback(
                    2 + min(analyzed / est_total, 1.0) * 38,
                    f"Bildbewegung: {analyzed}/{int(est_total)} Frames",
                )

        # Analysed frames are 0, s, 2s, ... with s = frame_step; motion
        # scores are computed for consecutive pairs of analysed frames.
        s = max(frame_step, 1)
        est_pairs = (frame_count // s - 1) if frame_count > 0 else 0
        use_segments = max_workers > 1 and est_pairs >= 100

        if not use_segments:
            motion_scores: List[float] = []
            cap = cv2.VideoCapture(video_path)
            try:
                if not cap.isOpened():
                    raise ValueError(f"Cannot open video: {video_path}")
                prev_blur = None
                while True:
                    frame = read_next(cap)
                    if frame is None:
                        break
                    gray = blur_gray(to_gray(frame))
                    if prev_blur is not None:
                        motion_scores.append(motion_score(prev_blur, gray))
                    prev_blur = gray
                    report_frame()
            finally:
                cap.release()
            return np.array(motion_scores), fps / max(frame_step, 1)

        # Segment-parallel decoding: each worker owns a VideoCapture, seeks
        # to its segment start and decodes+scores its part of the video.
        # Chunk boundaries sit on the frame-step grid so every worker sees
        # the same frame pairs as the sequential pass; the last chunk runs
        # open-ended so a wrong frame_count metadata cannot truncate pairs.
        workers = max(1, min(max_workers, est_pairs // 100))
        chunk_size = est_pairs // workers

        def scan_segment(pair_start: int, pair_end: Optional[int]) -> dict:
            local: dict = {}
            cap = cv2.VideoCapture(video_path)
            try:
                if not cap.isOpened():
                    return local
                cap.set(cv2.CAP_PROP_POS_FRAMES, (pair_start - 1) * s)
                ret, first = cap.read()
                if not ret:
                    return local
                prev_blur = blur_gray(to_gray(first))
                report_frame()
                j = pair_start
                while pair_end is None or j <= pair_end:
                    frame = read_next(cap)
                    if frame is None:
                        break
                    cur_blur = blur_gray(to_gray(frame))
                    local[j] = motion_score(prev_blur, cur_blur)
                    prev_blur = cur_blur
                    j += 1
                    report_frame()
                return local
            finally:
                cap.release()

        pool = ThreadPoolExecutor(max_workers=workers)
        try:
            futures = []
            for i in range(workers):
                pair_start = 1 + i * chunk_size
                pair_end = None if i == workers - 1 else pair_start + chunk_size - 1
                futures.append(pool.submit(scan_segment, pair_start, pair_end))
            merged: dict = {}
            for fut in futures:
                merged.update(fut.result())
        finally:
            pool.shutdown(wait=True)

        motion_scores = [merged[k] for k in sorted(merged.keys())]
        return np.array(motion_scores), fps / max(frame_step, 1)

    def extract_audio_features(self, video_path: str) -> Tuple[np.ndarray, np.ndarray, float]:
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)

        try:
            y, sr = librosa.load(video_path, sr=None, mono=True)
        except Exception as e:
            print(f"PySoundFile failed: {e}. Trying audioread instead.")
            import audioread
            with audioread.audio_open(video_path) as f:
                sr = f.samplerate
                samples = []
                for buf in f:
                    samples.extend(np.frombuffer(buf, dtype=np.float32))
                y = np.array(samples)

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        tempo = 0.0
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        except Exception:
            pass

        hop_length = 512
        times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr, hop_length=hop_length)

        return onset_env, times, float(tempo) if isinstance(tempo, np.ndarray) else tempo

    def detect_rallies(
        self,
        video_path: str,
        use_audio: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        table_points: Optional[List[Tuple[float, float]]] = None,
        frame_step: int = 1,
        motion_workers: int = 1,
        ball_workers: int = 1,
        motion_max_width: Optional[int] = None,
    ) -> List[dict]:
        print(f"Analysiere Video: {video_path}")
        t_total = time.time()

        # Motion and audio run in parallel: audio decoding happens in a
        # subprocess and barely competes for CPU with the motion pipeline.
        # The ball detector is created ONCE per analysis so every worker
        # shares it (ML: one thread-safe ONNX session; heuristic: stateless).
        ball_detector = create_ball_detector()
        model_version = getattr(ball_detector, "model_version", "unknown")
        print(f"Ball-Erkennung: {model_version}")

        pool = ThreadPoolExecutor(max_workers=2)
        try:
            t_motion = time.time()
            motion_fut = pool.submit(
                self.extract_motion_features,
                video_path,
                progress_callback,
                table_points,
                frame_step=frame_step,
                max_workers=motion_workers,
                max_width=motion_max_width,
            )
            audio_fut = None
            if use_audio and os.path.exists(video_path):

                def timed_audio():
                    t0 = time.time()
                    result = self.extract_audio_features(video_path)
                    return result, time.time() - t0

                audio_fut = pool.submit(timed_audio)

            motion_scores, fps = motion_fut.result()
            print(f"Motion-Phase: {time.time() - t_motion:.1f}s ({len(motion_scores)} Frames)")
            if progress_callback:
                progress_callback(42, "Bildbewegung analysiert")

            rally_candidates = []
            audio_ok = False
            if audio_fut is not None:
                if not audio_fut.done() and progress_callback:
                    progress_callback(45, "Audio wird analysiert...")
                try:
                    (onset_env, audio_times, tempo), audio_duration = audio_fut.result()
                    if progress_callback:
                        progress_callback(48, "Audio analysiert")
                    print(f"Audio-Phase: {audio_duration:.1f}s (parallel zur Bildanalyse)")

                    time_resolution = audio_times[1] - audio_times[0] if len(audio_times) > 1 else 0.1
                    motion_resampled = self._resample_motion(motion_scores, fps, audio_times)

                    combined_scores = self._combine_scores(motion_resampled, onset_env)
                    audio_norm = self._normalize(onset_env)
                    peak_indices, peak_props = signal.find_peaks(
                        audio_norm,
                        height=float(np.percentile(audio_norm, 75)),
                        prominence=0.12,
                        distance=max(1, int(0.12 / time_resolution)),
                    )
                    t_ball = time.time()
                    rally_candidates = self._rallies_from_audio_peaks(
                        audio_times[peak_indices],
                        np.asarray(peak_props["peak_heights"], dtype=float),
                        combined_scores,
                        time_resolution,
                        video_path,
                        table_points,
                        ball_workers,
                        progress_callback,
                        ball_detector,
                    )
                    print(f"Ball-Validierung: {time.time() - t_ball:.1f}s")
                    audio_ok = True
                except Exception as e:
                    print(f"Audio-Analyse fehlgeschlagen: {e}. Verwende nur Motion-Detection.")

            if not audio_ok:
                time_per_frame = 1.0 / fps
                rally_candidates = self._find_rally_segments(motion_scores, time_per_frame)
        finally:
            pool.shutdown(wait=True)

        if progress_callback:
            progress_callback(65, "Rally-Kandidaten ermittelt")

        # Step 3: Filter and validate rallies, then classify highlights
        # relative to the best rally of this video.
        accepted = []
        for i, candidate in enumerate(rally_candidates):
            start, end, score = candidate[:3]
            impact_count = int(candidate[3]) if len(candidate) > 3 else 0
            ball_hits = int(candidate[4]) if len(candidate) > 4 else 0

            # Dynamic duration check - don't artificially extend short rallies
            actual_duration = end - start
            if actual_duration > self.max_rally_duration:
                end = start + self.max_rally_duration
                actual_duration = self.max_rally_duration

            # Only accept rallies with minimum duration
            if actual_duration >= self.min_rally_duration:
                # Validation status - be more lenient, only mark uncertain ones as "review"
                validation_status = "accepted"
                if score < 0.35 and impact_count < 3 and (table_points and ball_hits == 0):
                    validation_status = "review"

                accepted.append({
                    "id": i + 1,
                    "start_time": round(start, 2),
                    "end_time": round(end, 2),
                    "duration": round(actual_duration, 2),
                    "score": round(score, 3),
                    "impact_count": impact_count,
                    "confidence": round(min(1.0, score), 3),
                    "validation_status": validation_status,
                    "ball_hits": ball_hits,
                    # Which ball detector produced this result (V0.6):
                    # "heuristic_v0.5" or the ONNX model file name.
                    "model_version": model_version,
                })

        max_score = max((r["score"] for r in accepted), default=0.0)
        rallies = []
        for r in accepted:
            is_highlight, highlight_score = self.classify_highlight(
                r["duration"], r["impact_count"], r["score"], max_score
            )
            r["is_highlight"] = is_highlight
            r["highlight_score"] = highlight_score
            rallies.append(r)

        print(f"{len(rallies)} Rallys erkannt ({sum(1 for r in rallies if r['is_highlight'])} Highlights). Gesamt: {time.time() - t_total:.1f}s")
        return rallies

    def _strip_bounce_tail(
        self,
        times: List[float],
        heights: List[float],
    ) -> Tuple[List[float], List[float], bool]:
        """Strip a "ball bouncing out" pattern from the END of a peak group.

        When a ball is picked up and thrown over the table, or bounces out
        after the final hit, impact gaps and loudness both shrink with every
        bounce (energy loss). A real rally keeps steady gaps and alternating
        loudness (hit loud, table bounce quiet, hit loud, ...), so it never
        matches this pattern.

        Returns (times, heights, trimmed). If the whole group matches, the
        returned lists are empty (the group was only a bouncing ball, not
        a rally).
        """
        n = len(times)

        def is_bounce_run(start: int) -> bool:
            """[start..end] shows shrinking gaps AND shrinking loudness."""
            tail_h = heights[start:]
            if any(
                tail_h[i + 1] > self.bounce_height_decay * tail_h[i]
                for i in range(len(tail_h) - 1)
            ):
                return False
            tail_t = times[start:]
            intervals = [tail_t[i + 1] - tail_t[i] for i in range(len(tail_t) - 1)]
            return all(
                intervals[i + 1] <= self.bounce_interval_decay * intervals[i]
                for i in range(len(intervals) - 1)
            )

        # A bounce tail needs at least 3 impacts (2 shrinking gaps).
        for start in range(0, n - 2):
            if not is_bounce_run(start):
                continue
            if start == 0:
                # The whole group is just a ball bouncing out (picked up /
                # thrown over the table) - not a rally.
                return [], [], True
            if heights[start] <= self.bounce_entry_ratio * heights[start - 1]:
                # Clear drop in loudness: the tail starts here.
                return times[:start], heights[:start], True
            if heights[start + 1] <= self.bounce_entry_ratio * heights[start]:
                # The pattern starts with a (loud) hit: that hit still
                # belongs to the rally, only the bounces after it are cut.
                return times[:start + 1], heights[:start + 1], True
        return times, heights, False

    def _rallies_from_audio_peaks(
        self,
        peak_times: np.ndarray,
        peak_heights: np.ndarray,
        combined_scores: np.ndarray,
        time_resolution: float,
        video_path: str,
        table_points: Optional[List[Tuple[float, float]]],
        ball_workers: int = 1,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        ball_detector=None,
    ) -> List[Tuple[float, float, float, int, int]]:
        """Group table-tennis impact sounds into points instead of motion blobs."""
        if len(peak_times) < 2:
            return []

        groups: List[Tuple[List[float], List[float]]] = []
        times: List[float] = [float(peak_times[0])]
        heights: List[float] = [float(peak_heights[0])]
        for idx in range(1, len(peak_times)):
            current = float(peak_times[idx])
            if current - times[-1] <= self.group_gap:
                times.append(current)
                heights.append(float(peak_heights[idx]))
            else:
                groups.append((times, heights))
                times = [current]
                heights = [float(peak_heights[idx])]
        groups.append((times, heights))

        # Phase 1: basic gates + bounce filter -> pending groups
        pending: List[List[float]] = []
        trimmed_groups = 0
        discarded_groups = 0
        for group_times, group_heights in groups:
            # A serve plus return already gives two impacts. Single peaks are
            # commonly footsteps, camera noise, or a player picking up a ball.
            if len(group_times) < 2 or group_times[-1] - group_times[0] < 0.15:
                continue

            group_times, group_heights, was_trimmed = self._strip_bounce_tail(group_times, group_heights)
            if was_trimmed:
                if len(group_times) < 2 or group_times[-1] - group_times[0] < 0.15:
                    discarded_groups += 1
                    continue
                trimmed_groups += 1
            pending.append(group_times)

        # Phase 2: ball validation, parallel ACROSS groups (a group only has
        # a handful of peaks, so parallelizing within one group barely helps)
        ball_hits_list = self._validate_ball_hits(
            video_path,
            pending,
            table_points,
            max_workers=ball_workers,
            progress_callback=progress_callback,
            ball_detector=ball_detector,
        )

        # Phase 3: assemble candidates in the original group order
        candidates = []
        for group_times, ball_hits in zip(pending, ball_hits_list):
            if table_points and ball_hits < 2:
                continue

            # Reduced buffer times to avoid artificially long clips
            start = max(0.0, group_times[0] - self.rally_buffer_start)
            end = group_times[-1] + self.rally_buffer_end

            # Cap at max duration
            if end - start > self.max_rally_duration:
                end = start + self.max_rally_duration

            start_index = max(0, int(start / time_resolution))
            end_index = min(len(combined_scores), int(end / time_resolution) + 1)
            score = float(np.mean(combined_scores[start_index:end_index]))

            candidates.append((start, end, score, len(group_times), ball_hits))

        if trimmed_groups or discarded_groups:
            print(
                f"Bounce-Filter: {trimmed_groups} Ballwechsel gekürzt, "
                f"{discarded_groups} Kandidaten verworfen (Ball wurde nur gehalten/geworfen)."
            )
        return candidates

    def _validate_ball_hits(
        self,
        video_path: str,
        peak_groups: List[List[float]],
        table_points: Optional[List[Tuple[float, float]]],
        max_workers: int = 1,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        ball_detector=None,
    ) -> List[int]:
        """Validate ball visibility for all rally groups.

        Groups are validated in parallel (one persistent VideoCapture per
        worker pulling groups from a queue) instead of sequentially, with a
        live progress report per finished group. ``ball_detector`` decides
        between the ML model and the classic heuristic (see ball_detector.py);
        the heuristic keeps V0.5 behaviour bit-identically.
        """
        n = len(peak_groups)
        if n == 0:
            return []
        if not table_points or len(table_points) != 4:
            return [0] * n

        if ball_detector is None:
            ball_detector = create_ball_detector()

        results = [0] * n
        total_done = [0]
        lock = threading.Lock()

        def report_done() -> None:
            with lock:
                total_done[0] += 1
                done = total_done[0]
            if progress_callback:
                progress_callback(
                    50 + min(done / max(n, 1), 1.0) * 12,
                    f"Ballwechsel {done}/{n} geprüft",
                )

        workers = max(1, min(max_workers, n))
        if workers == 1:
            release, scan = self._ball_scanner(video_path, table_points, ball_detector)
            if scan is None:
                return [0] * n
            try:
                for i in range(n):
                    results[i] = scan(peak_groups[i])
                    report_done()
            finally:
                release()
            return results

        index_queue: "queue.Queue[int]" = queue.Queue()
        for i in range(n):
            index_queue.put(i)

        def worker() -> None:
            release, scan = self._ball_scanner(video_path, table_points, ball_detector)
            if scan is None:
                return
            try:
                while True:
                    try:
                        i = index_queue.get_nowait()
                    except queue.Empty:
                        break
                    results[i] = scan(peak_groups[i])
                    report_done()
            finally:
                release()

        threads = [threading.Thread(target=worker) for _ in range(workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return results

    def _ball_scanner(
        self,
        video_path: str,
        table_points: List[Tuple[float, float]],
        ball_detector=None,
    ) -> Tuple[Optional[Callable[[], None]], Optional[Callable[[List[float]], int]]]:
        """Create a reusable ball scanner with its own VideoCapture."""
        if ball_detector is None:
            ball_detector = create_ball_detector()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None, None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Frames are validated in DISPLAY orientation, matching the table
        # calibration (browser view) and the ML training images from the
        # labeling tool. For 90°/270° videos the rotated dims are swapped.
        rotation = get_display_rotation(video_path)
        mask_w, mask_h = (height, width) if rotation in (90, 270) else (width, height)
        polygon = np.array(
            [[int(x * mask_w), int(y * mask_h)] for x, y in table_points],
            dtype=np.int32,
        )
        # Build the ball-validation mask once per scanner instead of once
        # per peak. TTLAB_PLAY_ZONE expands the table polygon into the play
        # zone (airspace above the table) so the ball is validated during
        # its flight too, not only at bounce points.
        mask = np.zeros((mask_h, mask_w), dtype=np.uint8)
        cv2.fillPoly(mask, [play_zone_polygon(polygon, self.play_zone_factor)], 255)

        def scan(peak_times: List[float]) -> int:
            hits = 0
            for timestamp in peak_times:
                if self.ball_seek_mode == "single":
                    before_ok, before, mid_ok, mid, after_ok, after = self._read_peak_frames_single(cap, timestamp)
                else:
                    before_ok, before, mid_ok, mid, after_ok, after = self._read_peak_frames_triple(cap, timestamp)
                if not before_ok or not after_ok:
                    continue
                before = rotate_frame(before, rotation)
                mid = rotate_frame(mid, rotation) if mid_ok else before
                after = rotate_frame(after, rotation)
                if ball_detector.is_ball_candidate(before, mid, after, mask):
                    hits += 1
            return hits

        def release() -> None:
            cap.release()

        return release, scan

    def _read_peak_frames_triple(
        self,
        cap: "cv2.VideoCapture",
        timestamp: float,
    ) -> Tuple[bool, Optional[np.ndarray], bool, Optional[np.ndarray], bool, Optional[np.ndarray]]:
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp - 0.1) * 1000)
        before_ok, before = cap.read()
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp - 0.02) * 1000)
        mid_ok, mid = cap.read()
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        after_ok, after = cap.read()
        return before_ok, before, mid_ok, mid, after_ok, after

    def _read_peak_frames_single(
        self,
        cap: "cv2.VideoCapture",
        timestamp: float,
    ) -> Tuple[bool, Optional[np.ndarray], bool, Optional[np.ndarray], bool, Optional[np.ndarray]]:
        """One seek per peak: seek to t-0.1s, then read forward until the
        frames at t-0.02s and t are reached (avoids decoding the same GOP
        three times)."""
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp - 0.1) * 1000)
        before_ok, before = cap.read()
        if not before_ok:
            return False, None, False, None, False, None

        mid = None
        mid_ok = False
        for target_ms in (max(0.0, timestamp - 0.02) * 1000.0, timestamp * 1000.0):
            frame = None
            while True:
                ok, f = cap.read()
                if not ok:
                    return before_ok, before, mid_ok, mid, False, None
                if cap.get(cv2.CAP_PROP_POS_MSEC) >= target_ms:
                    frame = f
                    break
            if not mid_ok:
                mid, mid_ok = frame, True
            else:
                return before_ok, before, mid_ok, mid, True, frame
        return before_ok, before, mid_ok, mid, False, None

    def _is_ball_candidate(
        self,
        before: np.ndarray,
        mid: np.ndarray,
        after: np.ndarray,
        mask: np.ndarray,
    ) -> bool:
        """Backward-compatible delegate to the heuristic ball detector.

        The logic itself now lives in ball_detector.HeuristicBallDetector
        (V0.6 Phase 2) so heuristic and ML detection share one interface.
        """
        return HeuristicBallDetector().is_ball_candidate(before, mid, after, mask)

    def _resample_motion(self, motion_scores: np.ndarray, fps: float, target_times: np.ndarray) -> np.ndarray:
        motion_times = np.arange(len(motion_scores)) / fps
        motion_resampled = np.interp(target_times, motion_times, motion_scores)
        return motion_resampled

    def _combine_scores(self, motion_scores: np.ndarray, audio_scores: np.ndarray) -> np.ndarray:
        motion_norm = self._normalize(motion_scores)
        audio_norm = self._normalize(audio_scores)

        if len(motion_norm) > len(audio_norm):
            audio_norm = np.pad(audio_norm, (0, len(motion_norm) - len(audio_norm)), mode='edge')
        elif len(audio_norm) > len(motion_norm):
            motion_norm = np.pad(motion_norm, (0, len(audio_norm) - len(motion_norm)), mode='edge')

        combined = 0.6 * motion_norm + 0.4 * audio_norm
        return combined

    def _normalize(self, arr: np.ndarray) -> np.ndarray:
        min_val, max_val = arr.min(), arr.max()
        if max_val - min_val < 1e-8:
            return np.zeros_like(arr)
        return (arr - min_val) / (max_val - min_val)

    def _find_rally_segments(
        self,
        scores: np.ndarray,
        time_resolution: float,
    ) -> List[Tuple[float, float, float]]:
        if len(scores) < 15:
            return []

        window_length = min(11, len(scores) if len(scores) % 2 else len(scores) - 1)
        smoothed = signal.savgol_filter(scores, window_length, 3)

        threshold = np.mean(smoothed) + 0.5 * np.std(smoothed)
        above_threshold = smoothed > threshold

        rally_segments = []
        in_rally = False
        rally_start = 0

        for i, is_above in enumerate(above_threshold):
            if is_above and not in_rally:
                rally_start = i * time_resolution
                in_rally = True
            elif not is_above and in_rally:
                rally_end = i * time_resolution
                duration = rally_end - rally_start

                # Don't artificially extend - use actual duration
                if duration >= self.min_rally_duration and duration <= self.max_rally_duration:
                    avg_score = float(np.mean(smoothed[int(rally_start/time_resolution):int(rally_end/time_resolution)]))
                    rally_segments.append((rally_start, rally_end, avg_score, 0))

                in_rally = False

        # Handle rally that extends to end of video
        if in_rally:
            rally_end = len(scores) * time_resolution
            duration = rally_end - rally_start
            if duration >= self.min_rally_duration and duration <= self.max_rally_duration:
                avg_score = float(np.mean(smoothed[int(rally_start/time_resolution):]))
                rally_segments.append((rally_start, rally_end, avg_score, 0))

        return rally_segments
