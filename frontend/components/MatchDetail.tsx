"use client";

import { useEffect, useRef, useState } from "react";
import { useLanguage } from "../lib/LanguageContext";
import { t } from "../lib/translations";

interface Match {
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

interface Rally {
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

interface MatchDetailProps {
  match: Match;
  rallies: Rally[];
  loading: boolean;
  onRefresh: () => void;
  onStartAnalysis?: () => void;
  lastUpdated?: Date;
  isPlayingClip?: boolean;
  onClipPlayStart?: () => void;
  onClipPlayEnd?: () => void;
}

interface MatchDetailProps {
  match: Match;
  rallies: Rally[];
  loading: boolean;
  onRefresh: () => void;
  onStartAnalysis?: () => void;
  lastUpdated?: Date;
  isPlayingClip?: boolean;
  onClipPlayStart?: () => void;
  onClipPlayEnd?: () => void;
}

const ACCEPTED_RALLIES_ONLY = false;

function TableSetup({ match, onRefresh }: { match: Match; onRefresh: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [points, setPoints] = useState<[number, number][]>(() => {
    if (!match.table_points) return [];
    try {
      return JSON.parse(match.table_points);
    } catch {
      return [];
    }
  });
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [saving, setSaving] = useState(false);

  const formatVideoTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remaining = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${minutes}:${remaining}`;
  };

  const handleVideoClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (points.length >= 4) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width));
    const y = Math.max(0, Math.min(1, (event.clientY - bounds.top) / bounds.height));
    setPoints((current) => [...current, [Number(x.toFixed(5)), Number(y.toFixed(5))]]);
  };

  const togglePlayback = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
    } else {
      videoRef.current.pause();
    }
  };

  const savePoints = async () => {
    if (points.length !== 4) return;
    setSaving(true);
    try {
      const response = await fetch(`http://localhost:8000/api/matches/${match.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ table_points: JSON.stringify(points) }),
      });
      if (response.ok) onRefresh();
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="rounded-2xl border border-blue-400/20 bg-blue-500/[0.06] p-5">
      <p className="text-xs uppercase tracking-widest text-blue-300">V0.3 Setup</p>
      <h3 className="mt-1 text-lg font-semibold">{t(language, 'table_setup.title')}</h3>
      <p className="mt-2 text-sm text-slate-400">{t(language, 'table_setup.description')}</p>

      <div className="mt-4 overflow-hidden rounded-xl border border-white/10 bg-black">
        <div
          className="relative aspect-video cursor-crosshair select-none"
          onClick={handleVideoClick}
        >
          <video
            ref={videoRef}
            src={`http://localhost:8000/api/videos/${match.filename}`}
            className="h-full w-full object-contain"
            preload="metadata"
            onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)}
            onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />
          <div className="pointer-events-none absolute inset-0">
            {points.map(([x, y], index) => (
              <span
                key={`${x}-${y}`}
                className="absolute flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-white bg-blue-500 text-xs font-bold text-white shadow-lg"
                style={{ left: `${x * 100}%`, top: `${y * 100}%` }}
              >
                {index + 1}
              </span>
            ))}
            {points.length === 4 && (
              <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="none">
                <polygon points={points.map(([x, y]) => `${x * 100},${y * 100}`).join(" ")} fill="rgba(59,130,246,0.12)" stroke="rgb(96,165,250)" strokeWidth="0.35" vectorEffect="non-scaling-stroke" />
              </svg>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 border-t border-white/10 px-3 py-2">
          <button onClick={togglePlayback} className="rounded-md bg-white/[0.1] px-3 py-1.5 text-sm text-white hover:bg-white/[0.18]">
            {isPlaying ? "⏸" : "▶"}
          </button>
          <span className="w-12 text-xs tabular-nums text-slate-400">{formatVideoTime(currentTime)}</span>
          <input
            type="range"
            min="0"
            max={duration || 0}
            step="0.01"
            value={currentTime}
            onChange={(event) => {
              const value = Number(event.target.value);
              if (videoRef.current) videoRef.current.currentTime = value;
              setCurrentTime(value);
            }}
            className="h-1 flex-1 accent-blue-400"
          />
          <span className="w-12 text-right text-xs tabular-nums text-slate-400">{formatVideoTime(duration)}</span>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-sm">
        <span className={points.length === 4 ? "text-emerald-300" : "text-amber-300"}>
          {t(language, 'table_setup.points_set', { count: points.length })}
        </span>
        <button onClick={() => setPoints([])} className="text-slate-400 hover:text-white">{t(language, 'table_setup.reset')}</button>
      </div>
      <button disabled={points.length !== 4 || saving} onClick={savePoints} className="mt-3 w-full rounded-lg bg-blue-500 px-4 py-2 font-semibold text-white hover:bg-blue-400 disabled:opacity-50">{saving ? t(language, 'table_setup.saving') : t(language, 'table_setup.save')}</button>
    </section>
  );
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 100);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`;
};

export default function MatchDetail({ match, rallies, loading, onRefresh, onStartAnalysis, lastUpdated, isPlayingClip, onClipPlayStart, onClipPlayEnd }: MatchDetailProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentRally, setCurrentRally] = useState<Rally | null>(null);
  const { language } = useLanguage();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [autoPlayQueue, setAutoPlayQueue] = useState(false);
  const [filterMode, setFilterMode] = useState<"all" | "highlights" | "accepted" | "rejected">("all");
  const [form, setForm] = useState({
    custom_title: match.custom_title || "",
    match_date: match.match_date?.slice(0, 10) || "",
    player_name: match.player_name || "",
    opponent_name: match.opponent_name || "",
    result: match.result || "unknown",
    score: match.score || "",
    notes: match.notes || "",
  });

  // Treat legacy rallies without a status as accepted. Also show "review" rallies for manual checking.
  const allRallies = rallies.filter(r => {
    const vs = r.validation_status as string | null | undefined;
    return vs == null || vs === "" || vs === "accepted" || vs === "review" || vs === "rejected";
  });
  
  const displayedRallies = (() => {
    switch (filterMode) {
      case "highlights":
        return allRallies.filter(r => r.user_marked_highlight);
      case "accepted":
        return allRallies.filter(r => r.validation_status === "accepted" || r.validation_status === "review");
      case "rejected":
        return allRallies.filter(r => r.validation_status === "rejected");
      default:
        return allRallies;
    }
  })();

  const progress = Math.max(0, Math.min(100, match.progress ?? 0));

  const handleStartAnalysis = async () => {
    if (onStartAnalysis) {
      onStartAnalysis();
    } else {
      try {
        const response = await fetch(`http://localhost:8000/api/matches/${match.id}/analyze`, { method: "POST" });
        if (response.ok) {
          onRefresh();
        }
      } catch (error) {
        console.error("Fehler beim Starten der Analyse:", error);
      }
    }
  };

  const handleRallyClick = (rally: Rally) => {
    setCurrentRally(rally);
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!currentRally || !videoRef.current) return;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        stepVideo(-0.1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        stepVideo(0.1);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentRally]);

  const saveMetadata = async () => {
    setSaving(true);
    try {
      const response = await fetch(`http://localhost:8000/api/matches/${match.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, match_date: form.match_date || null }),
      });
      if (response.ok) {
        setEditing(false);
        onRefresh();
      }
    } finally {
      setSaving(false);
    }
  };

  const updateRallyStatus = async (rallyId: number, status: string) => {
    const response = await fetch(`http://localhost:8000/api/rallies/${rallyId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ validation_status: status }),
    });
    if (response.ok) onRefresh();
  };

  const toggleHighlight = async (rallyId: number, current: boolean) => {
    const response = await fetch(`http://localhost:8000/api/rallies/${rallyId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_marked_highlight: !current }),
    });
    if (response.ok) onRefresh();
  };

  const updateRallyNotes = async (rallyId: number, newNotes: string) => {
    // Don't refresh immediately - just save in background to avoid video reset
    try {
      await fetch(`http://localhost:8000/api/rallies/${rallyId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: newNotes }),
      });
    } catch (error) {
      console.error("Failed to save notes:", error);
    }
  };

  const stepVideo = (seconds: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = Math.max(0, Math.min(videoRef.current.duration, videoRef.current.currentTime + seconds));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{match.original_filename}</h2>
          <p className="text-gray-400 text-sm mt-1">
            Status: {match.status} | Dauer: {match.duration ? `${Math.floor(match.duration)}s` : "-"}
          </p>
        </div>
        
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm"
        >
          🔄 Aktualisieren
        </button>
      </div>

      <section className="rounded-2xl border border-white/10 bg-white/[0.06] p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-blue-300">Match details</p>
            <h3 className="mt-1 text-lg font-semibold">Match-Metadaten</h3>
          </div>
          <button onClick={() => setEditing(!editing)} className="rounded-lg bg-white/[0.08] px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.14]">
            {editing ? "Abbrechen" : "Bearbeiten"}
          </button>
        </div>
        {editing ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-sm text-slate-400 sm:col-span-2">
              <span className="block mb-1">Titel (optional)</span>
              <input 
                type="text" 
                value={form.custom_title} 
                onChange={(event) => setForm({ ...form, custom_title: event.target.value })} 
                className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white outline-none focus:border-blue-400" 
                placeholder="z.B. Training vs. Roboter oder Turnierfinale 2026"
              />
            </label>
            {[["match_date", "Datum", "date"], ["player_name", "Eigener Name", "text"], ["opponent_name", "Gegner", "text"], ["score", "Spielstand", "text"]].map(([key, label, type]) => (
              <label key={key} className="text-sm text-slate-400">
                <span className="block mb-1">{label}</span>
                <input type={type} value={form[key as keyof typeof form]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white outline-none focus:border-blue-400" />
              </label>
            ))}
            <label className="text-sm text-slate-400">
              <span className="block mb-1">Resultat</span>
              <select value={form.result} onChange={(event) => setForm({ ...form, result: event.target.value })} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white">
                <option value="unknown">Unbekannt</option><option value="win">Sieg</option><option value="loss">Niederlage</option><option value="draw">Unentschieden</option>
              </select>
            </label>
            <label className="text-sm text-slate-400 sm:col-span-2">
              <span className="block mb-1">Notizen</span>
              <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} rows={3} className="mt-1 w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white outline-none focus:border-blue-400" />
            </label>
            <button onClick={saveMetadata} disabled={saving} className="rounded-lg bg-blue-500 px-4 py-2 font-semibold text-white hover:bg-blue-400 disabled:opacity-50 sm:col-span-2">{saving ? "Speichere..." : "Metadaten speichern"}</button>
          </div>
        ) : (
          <div className="mt-4 space-y-2">
            {match.custom_title && (
              <div className="text-lg font-semibold text-white">{match.custom_title}</div>
            )}
            <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-4">
              <span><b className="block text-xs text-slate-500">Spieler</b>{match.player_name || "-"}</span>
              <span><b className="block text-xs text-slate-500">Gegner</b>{match.opponent_name || "-"}</span>
              <span><b className="block text-xs text-slate-500">Resultat</b>{match.result === "win" ? "🟢 Sieg" : match.result === "loss" ? "🔴 Niederlage" : match.result === "draw" ? "🟡 Unentschieden" : "-"}</span>
              <span><b className="block text-xs text-slate-500">Spielstand</b>{match.score || "-"}</span>
            </div>
          </div>
        )}
      </section>

      {match.status === "pending" && (
        <div className="space-y-4">
          {!match.table_points && <TableSetup match={match} onRefresh={onRefresh} />}
          <div className="bg-gray-800 border border-blue-700 rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-blue-400 text-xl">⏸️</span>
            <div>
              <h3 className="text-lg font-semibold text-blue-300">{t(language, 'analysis.pending.title')}</h3>
              <p className="text-sm text-gray-400">
                {t(language, 'analysis.pending.description')}
              </p>
            </div>
          </div>
          
          <button
            onClick={handleStartAnalysis}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded text-white font-semibold transition-colors"
          >
            {t(language, 'analysis.pending.start')}
          </button>
          </div>
        </div>
      )}

      {match.status === "processing" && (
        <div className="rounded-2xl bg-white/[0.06] border border-amber-400/30 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-yellow-400 text-xl">⏳</span>
              <div>
                <h3 className="text-lg font-semibold text-yellow-300">{t(language, 'analysis.processing.title')}</h3>
                <p className="text-sm text-gray-400">
                  {match.progress_message || t(language, 'analysis.processing.message')}
                </p>
              </div>
            </div>
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-yellow-700 hover:bg-yellow-600 rounded text-sm text-white transition-colors"
            >
              {t(language, 'common.refresh')}
            </button>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">{t(language, 'analysis.progress')}</span>
              <span className="text-yellow-300">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-yellow-600 to-yellow-400 h-full rounded-full transition-all duration-500 animate-pulse"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="bg-white/[0.05] rounded-xl p-3">
              <p className="text-xs text-gray-400">{t(language, 'analysis.detected_rallies')}</p>
              <p className="text-2xl font-bold text-white">{rallies.length}</p>
            </div>
            <div className="bg-white/[0.05] rounded-xl p-3">
              <p className="text-xs text-gray-400">{t(language, 'analysis.highlights')}</p>
              <p className="text-2xl font-bold text-yellow-400">
                {rallies.filter(r => r.is_highlight).length}
              </p>
            </div>
          </div>

          {lastUpdated && (
            <p className="text-xs text-gray-500 text-center pt-2">
              {t(language, 'common.last_updated')}: {lastUpdated.toLocaleTimeString()}
            </p>
          )}

          <div className="bg-blue-900/20 border border-blue-700 rounded p-3 text-sm text-blue-300">
            💡 <strong>{t(language, 'common.tip')}:</strong> {t(language, 'analysis.tip')}
          </div>
        </div>
      )}

      {match.status === "failed" && (
        <div className="bg-red-900/30 border border-red-700 rounded p-4 text-red-300">
          ❌ {t(language, 'analysis.failed')} {match.error_message}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-400">{t(language, 'common.loading')}...</div>
      ) : rallies.length === 0 && match.status === "completed" ? (
        <div className="text-center py-8 text-gray-400">{t(language, 'rally.no_rallies_detected')}</div>
      ) : (
        <>
          {currentRally && currentRally.clip_filename && (
            <div className="rounded-2xl bg-white/[0.06] p-4 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">
                  Rally {currentRally.id} ({formatTime(currentRally.duration)})
                </h3>
                <button
                  onClick={() => toggleHighlight(currentRally.id, currentRally.user_marked_highlight)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                    currentRally.user_marked_highlight 
                      ? "bg-yellow-500 text-black hover:bg-yellow-400" 
                      : "bg-white/[0.08] text-slate-300 hover:bg-white/[0.14]"
                  }`}
                >
                  {currentRally.user_marked_highlight ? t(language, 'rally.highlight.set') : t(language, 'rally.highlight.mark')}
                </button>
              </div>
              <video
                ref={videoRef}
                src={`http://localhost:8000/api/clips/${currentRally.clip_filename}`}
                controls
                autoPlay
                className="w-full max-h-96 rounded"
                onPlay={() => onClipPlayStart?.()}
                onPause={() => onClipPlayEnd?.()}
                onEnded={() => {
                  onClipPlayEnd?.();
                  if (autoPlayQueue) {
                    const currentIndex = displayedRallies.findIndex(r => r.id === currentRally.id);
                    const nextRally = displayedRallies[currentIndex + 1];
                    if (nextRally) handleRallyClick(nextRally);
                  }
                }}
                onLoadedMetadata={(e) => {
                  const video = e.currentTarget;
                  video.playbackRate = 1.0;
                }}
              />
              <div className="mt-3 flex items-center gap-2">
                <button onClick={() => stepVideo(-0.1)} className="rounded bg-white/[0.08] px-3 py-1.5 text-xs text-slate-300 hover:bg-white/[0.14]">{t(language, 'rally.step_back')}</button>
                <button onClick={() => stepVideo(0.1)} className="rounded bg-white/[0.08] px-3 py-1.5 text-xs text-slate-300 hover:bg-white/[0.14]">{t(language, 'rally.step_forward')}</button>
                <span className="ml-auto text-xs text-slate-500">{t(language, 'rally.keyboard_tip')}</span>
              </div>
              
              <div className="mt-4">
                <label className="text-sm text-slate-400 block mb-2">
                  📝 {t(language, 'match.detail.notes')}
                </label>
                <textarea
                  value={currentRally.notes || ""}
                  onChange={(e) => {
                    e.stopPropagation();
                    const newNotes = e.target.value;
                    setCurrentRally({ ...currentRally, notes: newNotes });
                    updateRallyNotes(currentRally.id, newNotes);
                  }}
                  placeholder={language === 'de' ? "z.B. Rückhand zu spät, Aufschlag gut platziert..." : "e.g. Backhand too late, serve well placed..."}
                  rows={3}
                  className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white outline-none focus:border-blue-400 resize-none"
                />
              </div>
            </div>
          )}

          <div className="rounded-2xl bg-white/[0.06] border border-white/10 overflow-hidden">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{t(language, 'rally.timeline.title')}</h3>
                <p className="text-xs text-slate-400 mt-1">{t(language, 'rally.timeline.displayed', { current: displayedRallies.length, total: allRallies.length })}</p>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={filterMode}
                  onChange={(e) => setFilterMode(e.target.value as typeof filterMode)}
                  className="rounded-lg bg-white/[0.08] px-3 py-1.5 text-xs text-slate-300 outline-none focus:ring-1 focus:ring-blue-400"
                >
                  <option value="all">{t(language, 'rally.filter.all')}</option>
                  <option value="highlights">{t(language, 'rally.filter.highlights')}</option>
                  <option value="accepted">{t(language, 'rally.filter.accepted')}</option>
                  <option value="rejected">{t(language, 'rally.filter.rejected')}</option>
                </select>
                <button
                  onClick={() => { setAutoPlayQueue(!autoPlayQueue); if (!autoPlayQueue && currentRally) { const video = document.querySelector("video"); if (video) video.play(); }}}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${autoPlayQueue ? "bg-emerald-500 text-black" : "bg-white/[0.08] text-slate-300 hover:bg-white/[0.14]"}`}
                >
                  {autoPlayQueue ? t(language, 'rally.auto_play.on') : t(language, 'rally.auto_play.off')}
                </button>
              </div>
            </div>
            
            <div className="max-h-96 overflow-y-auto">
              {displayedRallies.map((rally, index) => (
                <div
                  key={rally.id}
                  onClick={() => handleRallyClick(rally)}
                  className={`p-3 border-b border-gray-700 cursor-pointer transition-colors
                    ${currentRally?.id === rally.id ? "bg-blue-900/30" : "hover:bg-gray-700"}
                    ${rally.is_highlight ? "bg-yellow-900/10" : ""}
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <span className="font-mono text-sm text-gray-400 w-16 shrink-0">
                        {formatTime(rally.start_time)}
                      </span>
                      <span className="font-semibold text-white min-w-[80px] text-center">
                        Rally {rally.id}
                      </span>
                      <span className="text-sm text-gray-500 min-w-[60px] text-center">
                        {formatTime(rally.duration)}
                      </span>
                      <div className="flex items-center gap-1.5">
                        {rally.user_marked_highlight && (
                          <span className="inline-flex items-center gap-1 rounded-md bg-yellow-500/10 px-2 py-0.5 text-xs font-medium text-yellow-400 whitespace-nowrap">
                            {t(language, 'rally.highlight')}
                          </span>
                        )}
                        <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap ${
                          rally.validation_status === "accepted" 
                            ? "bg-emerald-500/10 text-emerald-400" 
                            : rally.validation_status === "rejected" 
                            ? "bg-red-500/10 text-red-400" 
                            : "bg-amber-500/10 text-amber-400"
                        }`}>
                          {rally.validation_status === "accepted" ? t(language, 'rally.status.accepted') : rally.validation_status === "rejected" ? t(language, 'rally.status.rejected') : t(language, 'rally.status.review')}
                        </span>
                      </div>
                    </div>
                    
                    {rally.clip_filename ? (
                      <div className="flex items-center gap-3">
                        <button className="text-blue-400 hover:text-blue-300 text-sm">{t(language, 'rally.play')}</button>
                        <button 
                          onClick={(event) => { 
                            event.stopPropagation(); 
                            const newStatus = rally.validation_status === "rejected" ? "accepted" : "rejected";
                            updateRallyStatus(rally.id, newStatus);
                          }} 
                          className={`text-xs px-2 py-1 rounded transition ${
                            rally.validation_status === "rejected" 
                              ? "bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30" 
                              : "bg-red-500/20 text-red-300 hover:bg-red-500/30"
                          }`}
                        >
                          {rally.validation_status === "rejected" ? t(language, 'rally.keep') : t(language, 'rally.reject')}
                        </button>
                        {rally.notes && (
                          <span className="text-xs text-slate-500" title={rally.notes}>📝</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-500 text-sm">{t(language, 'rally.no_clip')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
