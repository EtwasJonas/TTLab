import ffmpeg
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional


def _parse_frame_rate(value: str) -> float:
    """Safely parse an ffprobe frame rate like '30000/1001' (no eval)."""
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            num, den = float(numerator), float(denominator)
            return num / den if den else 30.0
        return float(value)
    except (ValueError, ZeroDivisionError):
        return 30.0


class VideoProcessor:
    def __init__(self, clip_storage_path: str):
        self.clip_storage_path = clip_storage_path
        os.makedirs(clip_storage_path, exist_ok=True)

    def create_rally_clips(
        self,
        video_path: str,
        rallies: List[dict],
        match_id: int,
        max_workers: int = 1,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[dict]:
        """Extract one clip per rally.

        With max_workers > 1 several FFmpeg processes run in parallel (each
        one is a separate OS process, so this scales with the CPU cores).
        The returned list keeps the input order.
        """
        if not rallies:
            return []

        total = len(rallies)
        processed: List[Optional[dict]] = [None] * total
        # With many parallel FFmpeg processes, cap the encoder threads per
        # process so they don't oversubscribe each other.
        ffmpeg_threads = 2 if max_workers > 2 else 0

        def extract_at(index: int, rally: dict) -> None:
            clip_filename = f"match_{match_id}_rally_{rally['id']:03d}.mp4"
            clip_path = os.path.join(self.clip_storage_path, clip_filename)
            try:
                self._extract_clip(
                    video_path,
                    clip_path,
                    rally['start_time'],
                    rally['end_time'],
                    ffmpeg_threads,
                )
                rally['clip_filename'] = clip_filename
                rally['clip_path'] = clip_path
                print(f"Clip erstellt: {clip_filename}")
            except Exception as e:
                print(f"Fehler beim Erstellen von Clip {rally['id']}: {e}")
                rally['clip_filename'] = None
                rally['clip_path'] = None
            processed[index] = rally

        if max_workers <= 1:
            for index, rally in enumerate(rallies):
                extract_at(index, rally)
                if progress_callback:
                    progress_callback(
                        72 + (index + 1) / total * 25,
                        f"Clip {index + 1} von {total} erstellt",
                    )
        else:
            done = 0
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(extract_at, index, rally) for index, rally in enumerate(rallies)]
                for _ in as_completed(futures):
                    done += 1
                    if progress_callback:
                        progress_callback(
                            72 + done / total * 25,
                            f"Clip {done} von {total} erstellt",
                        )

        return [rally for rally in processed if rally is not None]

    def _extract_clip(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        ffmpeg_threads: int = 0,
    ):
        duration = end_time - start_time

        # yuv420p (8-bit) is required so clips play in Windows Media Player:
        # 10-bit sources (HEVC Main 10 from phones) would otherwise be
        # encoded as H.264 High 10 (Hi10P), which WMP cannot decode
        # (error 0x80004005). faststart improves seeking in the browser.
        output_kwargs = {
            "vcodec": "libx264",
            "acodec": "aac",
            "preset": "veryfast",
            "pix_fmt": "yuv420p",
            "movflags": "+faststart",
        }
        if ffmpeg_threads > 0:
            output_kwargs["threads"] = ffmpeg_threads
        (
            ffmpeg
            .input(input_path, ss=start_time, t=duration)
            .output(output_path, **output_kwargs)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

    def get_video_info(self, video_path: str) -> dict:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        if not video_stream:
            raise ValueError("No video stream found")

        duration = float(video_stream.get('duration', 0))
        if not duration:
            duration = float(probe['format'].get('duration', 0))

        return {
            "duration": duration,
            "width": int(video_stream.get('width', 0)),
            "height": int(video_stream.get('height', 0)),
            "fps": _parse_frame_rate(video_stream.get('r_frame_rate', '30/1')),
            "codec": video_stream.get('codec_name', 'unknown')
        }
