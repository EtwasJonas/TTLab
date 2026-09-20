export type AnalysisMode = "background" | "performance";

export interface Match {
  id: number;
  filename: string;
  original_filename: string;
  duration: number | null;
  upload_date: string;
  status: string;
  error_message: string | null;
  progress: number;
  progress_message: string | null;
  match_date: string | null;
  player_name: string | null;
  opponent_name: string | null;
  result: string | null;
  score: string | null;
  notes: string | null;
  table_points: string | null;
  custom_title: string | null;
}

export interface Rally {
  id: number;
  match_id: number;
  start_time: number;
  end_time: number;
  duration: number;
  clip_filename: string | null;
  is_highlight: boolean;
  highlight_score: number;
  validation_status: "accepted" | "review" | "rejected";
  confidence: number;
  impact_count: number;
  user_marked_highlight: boolean;
  notes: string | null;
}

// --- V0.6: Labeling tool ---

export interface DatasetStats {
  name: string;
  total_frames: number;
  frames_with_ball: number;
  frames_without_ball: number;
  exported: boolean;
}

export interface FrameAnnotation {
  match_id: number;
  frame_index: number;
  time_ms: number;
  has_ball: boolean;
  /** YOLO boxes [cx, cy, w, h] normalized 0..1, one per visible ball;
   *  empty array = negative sample (no ball) */
  bboxes: number[][];
  labeled_at: string;
}

export interface VideoInfo {
  match_id: number;
  duration: number;
  fps: number;
  frame_count: number;
  width: number;
  height: number;
  codec: string;
  /** Clockwise display rotation in degrees (0/90/180/270) */
  rotation: number;
}

/** Bounding box in normalized [x, y, w, h] form (top-left based, for rendering) */
export interface NormalizedBox {
  x: number;
  y: number;
  w: number;
  h: number;
}
