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
