import cv2
import numpy as np
import librosa
from scipy import signal
from typing import Callable, List, Tuple, Optional
import os
from typing import Any


class RallyDetector:
    def __init__(self, motion_threshold: float = 15.0, audio_threshold: float = 0.3):
        self.motion_threshold = motion_threshold
        self.audio_threshold = audio_threshold
        self.min_rally_duration = 3.5
        self.min_pause_duration = 0.7
        self.rally_buffer_start = 1.2
        self.rally_buffer_end = 0.5
        self.max_rally_duration = 15.0
        self.min_impact_count = 4

    def extract_motion_features(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[np.ndarray, float]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        motion_scores = []
        prev_gray = None

        processed = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if prev_gray is not None:
                frame_diff = cv2.absdiff(prev_gray, gray)
                thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
                motion_score = np.sum(thresh > 0) / thresh.size
                motion_scores.append(motion_score)

            prev_gray = gray
            processed += 1
            if progress_callback and frame_count and processed % max(int(fps * 2), 1) == 0:
                progress_callback(
                    10 + min(processed / frame_count, 1.0) * 25,
                    f"Bildbewegung: {processed}/{frame_count} Frames",
                )

        cap.release()
        return np.array(motion_scores), fps

    def extract_audio_features(self, video_path: str) -> Tuple[np.ndarray, float]:
        y, sr = librosa.load(video_path, sr=None, mono=True)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        
        tempo = 0
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        except:
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
    ) -> List[dict]:
        print(f"Analysiere Video: {video_path}")
        
        motion_scores, fps = self.extract_motion_features(video_path, progress_callback)
        if progress_callback:
            progress_callback(35, "Bildbewegung analysiert")
        print(f"Motion-Extraktion abgeschlossen. {len(motion_scores)} Frames analysiert.")

        rally_candidates = []
        
        if use_audio and os.path.exists(video_path):
            try:
                onset_env, audio_times, tempo = self.extract_audio_features(video_path)
                if progress_callback:
                    progress_callback(55, "Audio analysiert")
                print(f"Audio-Extraktion abgeschlossen. Tempo: {tempo}")
                
                time_resolution = audio_times[1] - audio_times[0] if len(audio_times) > 1 else 0.1
                motion_resampled = self._resample_motion(motion_scores, fps, audio_times)
                
                combined_scores = self._combine_scores(motion_resampled, onset_env)
                audio_norm = self._normalize(onset_env)
                peak_indices, _ = signal.find_peaks(
                    audio_norm,
                    height=float(np.percentile(audio_norm, 75)),
                    prominence=0.12,
                    distance=max(1, int(0.12 / time_resolution)),
                )
                rally_candidates = self._rallies_from_audio_peaks(
                    audio_times[peak_indices],
                    combined_scores,
                    time_resolution,
                    video_path,
                    table_points,
                )
                
            except Exception as e:
                print(f"Audio-Analyse fehlgeschlagen: {e}. Verwende nur Motion-Detection.")
                time_per_frame = 1.0 / fps
                rally_candidates = self._find_rally_segments(motion_scores, time_per_frame)
        else:
            time_per_frame = 1.0 / fps
            rally_candidates = self._find_rally_segments(motion_scores, time_per_frame)

        if progress_callback:
            progress_callback(65, "Rally-Kandidaten ermittelt")

        rallies = []
        for i, candidate in enumerate(rally_candidates):
            start, end, score = candidate[:3]
            impact_count = int(candidate[3]) if len(candidate) > 3 else 0
            duration = end - start
            if duration >= self.min_rally_duration:
                rallies.append({
                    "id": i + 1,
                    "start_time": round(start, 2),
                    "end_time": round(end, 2),
                    "duration": round(duration, 2),
                    "score": round(score, 3),
                    "impact_count": impact_count,
                    "confidence": round(min(1.0, score), 3),
                    "validation_status": "accepted" if score >= 0.48 and impact_count >= 2 else "review",
                })

        print(f"{len(rallies)} Rallys erkannt.")
        return rallies

    def _rallies_from_audio_peaks(
        self,
        peak_times: np.ndarray,
        combined_scores: np.ndarray,
        time_resolution: float,
        video_path: str,
        table_points: Optional[List[Tuple[float, float]]],
    ) -> List[Tuple[float, float, float]]:
        """Group table-tennis impact sounds into points instead of motion blobs."""
        if len(peak_times) < 2:
            return []

        groups = []
        group = [float(peak_times[0])]
        for current in peak_times[1:]:
            current = float(current)
            if current - group[-1] <= 1.25:
                group.append(current)
            else:
                groups.append(group)
                group = [current]
        groups.append(group)

        candidates = []
        for group in groups:
            # A serve plus return already gives two impacts. Single peaks are
            # commonly footsteps, camera noise, or a player picking up a ball.
            if len(group) < 2 or group[-1] - group[0] < 0.15:
                continue

            start = max(0.0, group[0] - self.rally_buffer_start)
            end = group[-1] + self.rally_buffer_end
            if end - start > self.max_rally_duration:
                continue

            start_index = max(0, int(start / time_resolution))
            end_index = min(len(combined_scores), int(end / time_resolution) + 1)
            score = float(np.mean(combined_scores[start_index:end_index]))
            ball_hits = self._count_ball_candidates(video_path, group, table_points)
            if table_points and ball_hits < 2:
                continue
            candidates.append((start, end, score, len(group), ball_hits))

        return candidates

    def _count_ball_candidates(
        self,
        video_path: str,
        peak_times: List[float],
        table_points: Optional[List[Tuple[float, float]]],
    ) -> int:
        """Detect white table tennis balls using motion + brightness.

        This is intentionally a candidate detector, not a trained ball tracker.
        It rejects many walking clips without pretending to identify every ball.
        """
        if not table_points or len(table_points) != 4:
            return 0

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        polygon = np.array(
            [[int(x * width), int(y * height)] for x, y in table_points],
            dtype=np.int32,
        )
        hits = 0

        for timestamp in peak_times:
            cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp - 0.1) * 1000)
            before_ok, before = cap.read()
            cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp - 0.02) * 1000)
            mid_ok, mid = cap.read()
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            after_ok, after = cap.read()
            if not before_ok or not after_ok:
                continue

            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.fillPoly(mask, [polygon], 255)

            before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
            mid_gray = cv2.cvtColor(mid, cv2.COLOR_BGR2GRAY) if mid_ok else before_gray
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
            if any(3 <= cv2.contourArea(contour) <= 250 for contour in contours):
                hits += 1

        cap.release()
        return hits

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
        event_times: Optional[np.ndarray] = None,
        require_audio_evidence: bool = False,
    ) -> List[Tuple[float, float, float]]:
        if len(scores) < 15:
            return []

        window_length = min(11, len(scores) if len(scores) % 2 else len(scores) - 1)
        smoothed = signal.savgol_filter(scores, window_length, 3)
        
        threshold = np.mean(smoothed) + 0.5 * np.std(smoothed)
        above_threshold = smoothed > threshold
        
        segments = []
        in_segment = False
        segment_start = 0
        segment_scores = []

        for i, is_active in enumerate(above_threshold):
            current_time = i * time_resolution
            
            if is_active and not in_segment:
                in_segment = True
                segment_start = current_time
                segment_scores = [smoothed[i]]
            elif is_active and in_segment:
                segment_scores.append(smoothed[i])
            elif not is_active and in_segment:
                in_segment = False
                segment_end = current_time
                avg_score = np.mean(segment_scores)
                segments.append((segment_start, segment_end, avg_score))

        if in_segment:
            segment_end = len(scores) * time_resolution
            avg_score = np.mean(segment_scores)
            segments.append((segment_start, segment_end, avg_score))

        if require_audio_evidence and event_times is not None:
            segments = [
                segment
                for segment in segments
                if np.count_nonzero(
                    (event_times >= segment[0]) & (event_times <= segment[1])
                ) >= 2
            ]

        return self._add_buffers_and_filter(segments)

    def _add_buffers_and_filter(
        self,
        segments: List[Tuple[float, float, float]],
    ) -> List[Tuple[float, float, float]]:
        buffered_segments = []
        for start, end, score in self._merge_close_segments(segments):
            raw_duration = end - start

            # A long uninterrupted motion phase is usually walking/setup, not one rally.
            # Do not manufacture fake rallies by slicing it into arbitrary time windows.
            if raw_duration > self.max_rally_duration:
                continue

            buffered_start = max(0, start - self.rally_buffer_start)
            buffered_end = end + self.rally_buffer_end
            buffered_segments.append((buffered_start, buffered_end, score))

        return buffered_segments

    def _merge_close_segments(
        self, 
        segments: List[Tuple[float, float, float]]
    ) -> List[Tuple[float, float, float]]:
        if not segments:
            return []

        merged = [segments[0]]
        
        for start, end, score in segments[1:]:
            prev_start, prev_end, prev_score = merged[-1]
            
            gap = start - prev_end
            
            if gap < self.min_pause_duration:
                new_end = end
                new_score = (prev_score * (prev_end - prev_start) + score * (end - start)) / (new_end - prev_start)
                merged[-1] = (prev_start, new_end, new_score)
            else:
                merged.append((start, end, score))

        return merged
