import ffmpeg
import os
from typing import List


class VideoProcessor:
    def __init__(self, clip_storage_path: str):
        self.clip_storage_path = clip_storage_path
        os.makedirs(clip_storage_path, exist_ok=True)

    def create_rally_clips(
        self, 
        video_path: str, 
        rallies: List[dict], 
        match_id: int
    ) -> List[dict]:
        processed_rallies = []

        for rally in rallies:
            clip_filename = f"match_{match_id}_rally_{rally['id']:03d}.mp4"
            clip_path = os.path.join(self.clip_storage_path, clip_filename)

            try:
                self._extract_clip(
                    video_path, 
                    clip_path, 
                    rally['start_time'], 
                    rally['end_time']
                )
                
                rally['clip_filename'] = clip_filename
                rally['clip_path'] = clip_path
                processed_rallies.append(rally)
                
                print(f"Clip erstellt: {clip_filename}")
                
            except Exception as e:
                print(f"Fehler beim Erstellen von Clip {rally['id']}: {e}")
                rally['clip_filename'] = None
                rally['clip_path'] = None
                processed_rallies.append(rally)

        return processed_rallies

    def _extract_clip(
        self, 
        input_path: str, 
        output_path: str, 
        start_time: float, 
        end_time: float
    ):
        duration = end_time - start_time
        
        # Re-encode clips so the requested 1.5 second pre-roll is accurate.
        (
            ffmpeg
            .input(input_path, ss=start_time, t=duration)
            .output(output_path, vcodec='libx264', acodec='aac', preset='veryfast')
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
            "fps": eval(video_stream.get('r_frame_rate', '30/1')),
            "codec": video_stream.get('codec_name', 'unknown')
        }
