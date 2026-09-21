"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useLanguage } from "../lib/LanguageContext";
import { t } from "../lib/translations";
import { API_BASE } from "../lib/api";
import type { Match, Rally, AnalysisMode } from "../lib/types";

interface MatchDetailProps {
  match: Match;
  rallies: Rally[];
  onRefresh: () => void;
  onStartAnalysis?: (mode: AnalysisMode) => void;
  lastUpdated?: Date;
  isPlayingClip?: boolean;
  onClipPlayStart?: () => void;
  onClipPlayEnd?: () => void;
}

function TableSetup({ match, onRefresh }: { match: Match; onRefresh: () => void }) {
  const { language } = useLanguage();
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
      const response = await fetch(`${API_BASE}/api/matches/${match.id}`, {
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
            src={`${API_BASE}/api/videos/${match.filename}`}
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

export default function MatchDetail({ match, rallies, onRefresh, onStartAnalysis, lastUpdated, isPlayingClip, onClipPlayStart, onClipPlayEnd }: MatchDetailProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const notesRef = useRef<HTMLTextAreaElement>(null);
  const [currentRally, setCurrentRally] = useState<Rally | null>(null);
  const { language } = useLanguage();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [autoPlayQueue, setAutoPlayQueue] = useState(false);
  const [filterMode, setFilterMode] = useState<"all" | "highlights" | "accepted" | "rejected">("all");
  const [localRallies, setLocalRallies] = useState<Rally[]>(rallies);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [loopEnabled, setLoopEnabled] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [form, setForm] = useState({
    custom_title: match.custom_title || "",
    match_date: match.match_date?.slice(0, 10) || "",
    player_name: match.player_name || "",
    opponent_name: match.opponent_name || "",
    result: match.result || "unknown",
    score: match.score || "",
    notes: match.notes || "",
  });

  // Only resync the local rally state when the server data actually changed.
  // Background polls deliver new array objects every few seconds; blindly
  // copying them would discard local edits (e.g. notes being typed) and
  // cause needless re-renders.
  const ralliesSignature = useMemo(
    () => rallies
      .map(r => [r.id, r.start_time, r.end_time, r.duration, r.clip_filename ?? '', r.validation_status, r.user_marked_highlight, r.is_highlight, r.notes ?? ''].join(':'))
      .join('|'),
    [rallies]
  );
  const syncedSignature = useRef(ralliesSignature);
  useEffect(() => {
    if (ralliesSignature !== syncedSignature.current) {
      syncedSignature.current = ralliesSignature;
      setLocalRallies(rallies);
    }
  }, [ralliesSignature, rallies]);

  // Compute rally numbers (per match, ordered by start time) once per data
  // change instead of sorting the full list on every rendered row.
  const rallyNumbers = useMemo(() => {
    const map = new Map<number, number>();
    [...localRallies]
      .sort((a, b) => a.start_time - b.start_time)
      .forEach((rally, index) => map.set(rally.id, index + 1));
    return map;
  }, [localRallies]);

  const getRallyNumber = (rallyId: number): number => rallyNumbers.get(rallyId) ?? 0;

  // Treat legacy rallies without a status as accepted. Also show "review" rallies for manual checking.
  const allRallies = useMemo(() => localRallies.filter(r => {
    const vs = r.validation_status as string | null | undefined;
    return vs == null || vs === "" || vs === "accepted" || vs === "review" || vs === "rejected";
  }), [localRallies]);

  // A rally counts as highlight when the user marked it OR the automatic
  // detection classified it as one.
  const isMarked = (r: Rally) => r.user_marked_highlight || r.is_highlight;

  const displayedRallies = useMemo(() => {
    switch (filterMode) {
      case "highlights":
        return allRallies.filter(isMarked);
      case "accepted":
        return allRallies.filter(r => r.validation_status === "accepted" || r.validation_status === "review");
      case "rejected":
        return allRallies.filter(r => r.validation_status === "rejected");
      default:
        return allRallies;
    }
  }, [allRallies, filterMode]);

  const progress = Math.max(0, Math.min(100, match.progress ?? 0));

  const handleStartAnalysis = (mode: AnalysisMode) => {
    if (onStartAnalysis) {
      onStartAnalysis(mode);
      return;
    }
    fetch(`${API_BASE}/api/matches/${match.id}/analyze?mode=${mode}`, { method: "POST" })
      .then((response) => {
        if (response.ok) onRefresh();
      })
      .catch((error) => console.error("Fehler beim Starten der Analyse:", error));
  };

  const handleRallyClick = (rally: Rally, skipScroll: boolean = false) => {
    setCurrentRally(rally);
    // Auto-scroll to video player element (only on manual clicks, not auto-play)
    if (!skipScroll) {
      setTimeout(() => {
        videoRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 50);
    }
  };

  const navigateToRally = (direction: 'prev' | 'next') => {
    if (!currentRally) return;
    
    // First try to find current rally in displayed rallies
    let currentIndex = displayedRallies.findIndex(r => r.id === currentRally.id);
    
    // If not found (e.g., status changed and filtered out), use allRallies for navigation
    if (currentIndex === -1) {
      const sortedAllRallies = [...allRallies].sort((a, b) => a.start_time - b.start_time);
      const currentAllIndex = sortedAllRallies.findIndex(r => r.id === currentRally.id);
      if (currentAllIndex === -1) return;
      
      const newAllIndex = direction === 'prev' ? currentAllIndex - 1 : currentAllIndex + 1;
      if (newAllIndex >= 0 && newAllIndex < sortedAllRallies.length) {
        handleRallyClick(sortedAllRallies[newAllIndex], true);
      }
      return;
    }
    
    const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex >= 0 && newIndex < displayedRallies.length) {
      handleRallyClick(displayedRallies[newIndex], true);
    }
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!currentRally || !videoRef.current) return;
      
      // Don't trigger shortcuts when typing in form fields
      if (event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLInputElement) {
        return;
      }
      
      // Prevent video controls from receiving spacebar
      if (event.key === " ") {
        event.preventDefault();
        event.stopPropagation();
        if (videoRef.current.paused) {
          videoRef.current.play();
        } else {
          videoRef.current.pause();
        }
        return;
      }
      
      // Read handlers from the ref so shortcuts always use the latest
      // filter/navigation state instead of a stale closure.
      const { navigateToRally: navigate, stepVideo: step, toggleHighlight: toggleHl, updateRallyStatus: updateStatus } = shortcutHandlers.current;
      
      switch (event.key) {
        case "ArrowLeft":
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            navigate('prev');
          } else {
            event.preventDefault();
            step(-0.01);
          }
          break;
        case "ArrowRight":
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            navigate('next');
          } else {
            event.preventDefault();
            step(0.01);
          }
          break;
        case "h":
        case "H":
          event.preventDefault();
          toggleHl(currentRally.id, currentRally.user_marked_highlight || currentRally.is_highlight);
          break;
        case "r":
        case "R":
          event.preventDefault();
          updateStatus(currentRally.id, currentRally.validation_status === "rejected" ? "accepted" : "rejected");
          break;
        case "n":
        case "N":
          event.preventDefault();
          notesRef.current?.focus();
          break;
        case "l":
        case "L":
          event.preventDefault();
          setLoopEnabled(prev => !prev);
          break;
        case "1":
        case "2":
        case "3":
        case "4":
          event.preventDefault();
          const speeds: Record<string, number> = { "1": 0.25, "2": 0.5, "3": 1.0, "4": 1.5 };
          const newSpeed = speeds[event.key];
          setPlaybackRate(newSpeed);
          if (videoRef.current) videoRef.current.playbackRate = newSpeed;
          break;
      }
    };
    
    // Use capture phase to intercept before video controls
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [currentRally]);

  const saveMetadata = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/matches/${match.id}`, {
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

  const updateRallyStatus = async (rallyId: number, newStatus: Rally["validation_status"]) => {
    setLocalRallies(prev => prev.map(r => 
      r.id === rallyId ? { ...r, validation_status: newStatus } : r
    ));
    
    if (currentRally?.id === rallyId) {
      setCurrentRally(prev => prev ? { ...prev, validation_status: newStatus } : null);
    }
    
    try {
      await fetch(`${API_BASE}/api/rallies/${rallyId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ validation_status: newStatus }),
      });
    } catch (error) {
      console.error("Failed to save status:", error);
      const revertedStatus = newStatus === "rejected" ? "accepted" : "rejected";
      setLocalRallies(prev => prev.map(r => 
        r.id === rallyId ? { ...r, validation_status: revertedStatus } : r
      ));
      if (currentRally?.id === rallyId) {
        setCurrentRally(prev => prev ? { ...prev, validation_status: revertedStatus } : null);
      }
    }
  };

  const toggleHighlight = async (rallyId: number, current: boolean) => {
    const newHighlightState = !current;
    
    setLocalRallies(prev => prev.map(r => 
      r.id === rallyId ? { ...r, user_marked_highlight: newHighlightState, is_highlight: newHighlightState } : r
    ));
    
    if (currentRally?.id === rallyId) {
      setCurrentRally(prev => prev ? { ...prev, user_marked_highlight: newHighlightState, is_highlight: newHighlightState } : null);
    }
    
    try {
      await fetch(`${API_BASE}/api/rallies/${rallyId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_marked_highlight: newHighlightState }),
      });
    } catch (error) {
      console.error("Failed to save highlight:", error);
      setLocalRallies(prev => prev.map(r => 
        r.id === rallyId ? { ...r, user_marked_highlight: current, is_highlight: current } : r
      ));
    }
  };

  const notesSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const updateRallyNotes = (rallyId: number, newNotes: string) => {
    setLocalRallies(prev => prev.map(r => 
      r.id === rallyId ? { ...r, notes: newNotes } : r
    ));
    
    // Debounce the PATCH request so typing doesn't fire one request per keystroke
    if (notesSaveTimerRef.current) {
      clearTimeout(notesSaveTimerRef.current);
    }
    notesSaveTimerRef.current = setTimeout(() => {
      fetch(`${API_BASE}/api/rallies/${rallyId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: newNotes }),
      }).catch((error) => console.error("Failed to save notes:", error));
    }, 600);
  };

  useEffect(() => {
    return () => {
      if (notesSaveTimerRef.current) clearTimeout(notesSaveTimerRef.current);
    };
  }, []);

  const downloadAllClips = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/matches/${match.id}/export-all-rallies-video?fast=true`);
      if (!response.ok) throw new Error('Fast download failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `all_rallies_${match.id}.mp4`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Fast download failed, trying compatible mode:", error);
      window.open(`${API_BASE}/api/matches/${match.id}/export-all-rallies-video`, '_blank');
    }
  };

  const downloadHighlights = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/matches/${match.id}/export-highlights-video?fast=true`);
      if (!response.ok) throw new Error('Fast download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `highlights_${match.id}.mp4`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Fast download failed, trying compatible mode:", error);
      window.open(`${API_BASE}/api/matches/${match.id}/export-highlights-video`, '_blank');
    }
  };

  const [reevaluating, setReevaluating] = useState(false);

  const reevaluateHighlights = async () => {
    setReevaluating(true);
    try {
      const response = await fetch(`${API_BASE}/api/matches/${match.id}/reevaluate-highlights`, { method: "POST" });
      if (response.ok) {
        onRefresh();
      }
    } catch (error) {
      console.error("Fehler bei der Highlight-Neubewertung:", error);
    } finally {
      setReevaluating(false);
    }
  };

  const stepVideo = (seconds: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = Math.max(0, Math.min(videoRef.current.duration, videoRef.current.currentTime + seconds));
  };

  // Keep the latest handler versions available to the keyboard shortcut
  // listener (which only re-subscribes when the current rally changes).
  const shortcutHandlers = useRef({ navigateToRally, stepVideo, toggleHighlight, updateRallyStatus });
  shortcutHandlers.current = { navigateToRally, stepVideo, toggleHighlight, updateRallyStatus };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{match.original_filename}</h2>
          <p className="text-gray-400 text-sm mt-1">
            {t(language, 'common.status')}: {match.status} | {t(language, 'match.detail.duration')}: {match.duration ? `${Math.floor(match.duration)}s` : "-"}
          </p>
        </div>
        
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm"
        >
          🔄 {t(language, 'common.refresh')}
        </button>
      </div>

      <section className="rounded-2xl border border-white/10 bg-white/[0.06] p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-blue-300">Match details</p>
              <h3 className="mt-1 text-lg font-semibold">{t(language, 'match.detail.metadata')}</h3>
            </div>
            <button onClick={() => setEditing(!editing)} className="rounded-lg bg-white/[0.08] px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.14]">
              {editing ? t(language, 'match.detail.cancel') : t(language, 'match.detail.edit')}
            </button>
          </div>
        {editing ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-sm text-slate-400 sm:col-span-2">
              <span className="block mb-1">{t(language, 'match.detail.title')}</span>
              <input 
                type="text" 
                value={form.custom_title} 
                onChange={(event) => setForm({ ...form, custom_title: event.target.value })} 
                className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white outline-none focus:border-blue-400" 
                placeholder={t(language, 'match.detail.title_placeholder')}
              />
            </label>
            {[["match_date", t(language, 'match.detail.date'), "date"], ["player_name", t(language, 'match.detail.player'), "text"], ["opponent_name", t(language, 'match.detail.opponent'), "text"], ["score", t(language, 'match.detail.score'), "text"]].map(([key, label, type]) => (
              <label key={key} className="text-sm text-slate-400">
                <span className="block mb-1">{label}</span>
                <input type={type} value={form[key as keyof typeof form]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white outline-none focus:border-blue-400" />
              </label>
            ))}
            <label className="text-sm text-slate-400">
              <span className="block mb-1">{t(language, 'match.detail.result_label')}</span>
              <select value={form.result} onChange={(event) => setForm({ ...form, result: event.target.value })} className="mt-1 w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-white">
                <option value="unknown">{language === 'de' ? 'Unbekannt' : 'Unknown'}</option>
                <option value="win">{language === 'de' ? 'Sieg' : 'Win'}</option>
                <option value="loss">{language === 'de' ? 'Niederlage' : 'Loss'}</option>
                <option value="draw">{language === 'de' ? 'Unentschieden' : 'Draw'}</option>
              </select>
            </label>
            <label className="text-sm text-slate-400 sm:col-span-2">
              <span className="block mb-1">{t(language, 'match.detail.notes')}</span>
              <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} rows={3} className="mt-1 w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white outline-none focus:border-blue-400" />
            </label>
            <button onClick={saveMetadata} disabled={saving} className="rounded-lg bg-blue-500 px-4 py-2 font-semibold text-white hover:bg-blue-400 disabled:opacity-50 sm:col-span-2">{saving ? (language === 'de' ? 'Speichere...' : 'Saving...') : t(language, 'match.detail.save')}</button>
          </div>
        ) : (
          <div className="mt-4 space-y-2">
            {match.custom_title && (
              <div className="text-lg font-semibold text-white">{match.custom_title}</div>
            )}
            <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-4">
              <span><b className="block text-xs text-slate-500">{t(language, 'match.detail.player_label')}</b>{match.player_name || "-"}</span>
              <span><b className="block text-xs text-slate-500">{t(language, 'match.detail.opponent_label')}</b>{match.opponent_name || "-"}</span>
              <span><b className="block text-xs text-slate-500">{t(language, 'match.detail.result_label')}</b>{match.result === "win" ? t(language, 'match.detail.win') : match.result === "loss" ? t(language, 'match.detail.loss') : match.result === "draw" ? t(language, 'match.detail.draw') : "-"}</span>
              <span><b className="block text-xs text-slate-500">{t(language, 'match.detail.score_label')}</b>{match.score || "-"}</span>
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
          
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => handleStartAnalysis("performance")}
              className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded text-white font-semibold transition-colors"
              title={language === 'de' ? 'Nutzt alle CPU-Kerne für die schnellste Analyse – identische Erkennungsqualität' : 'Uses all CPU cores for the fastest analysis - identical detection quality'}
            >
              ⚡ {language === 'de' ? 'Analyse mit voller Leistung' : 'Full-speed analysis'}
            </button>
            <button
              onClick={() => handleStartAnalysis("background")}
              className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 rounded text-white font-semibold transition-colors"
              title={language === 'de' ? 'Weniger CPU-Kerne und reduzierte Bewegungsanalyse – der PC bleibt flüssig nutzbar' : 'Fewer CPU cores and reduced motion analysis - keeps your PC responsive'}
            >
              🌙 {language === 'de' ? 'Im Hintergrund analysieren' : 'Analyze in background'}
            </button>
          </div>
          <p className="text-xs text-gray-500 text-center">
            {language === 'de'
              ? 'Volle Leistung nutzt alle Kerne (schnellste Analyse, gleiche Qualität). Der Hintergrund-Modus schonet den PC für andere Aufgaben.'
              : 'Full speed uses all cores (fastest analysis, same quality). Background mode keeps resources free for other tasks.'}
          </p>
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

      {rallies.length === 0 && match.status === "completed" ? (
        <div className="text-center py-8 text-gray-400">{t(language, 'rally.no_rallies_detected')}</div>
      ) : rallies.length === 0 ? (
        // Nothing to show yet (pending/processing/failed) - the status
        // sections above already communicate the current state.
        null
      ) : (
        <>
          {currentRally && currentRally.clip_filename && (
            <div className="rounded-2xl bg-white/[0.06] p-4 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => navigateToRally('prev')}
                    disabled={displayedRallies.findIndex(r => r.id === currentRally.id) === 0}
                    className="rounded-lg bg-white/[0.08] px-3 py-1.5 text-sm text-slate-300 hover:bg-white/[0.14] disabled:opacity-30 disabled:cursor-not-allowed"
                    title={language === 'de' ? 'Vorherige Rally [Strg+←]' : 'Previous rally [Ctrl+Left]'}
                  >
                    ⏮ {language === 'de' ? 'Zurück' : 'Back'}
                  </button>
                  <button
                    onClick={() => navigateToRally('next')}
                    disabled={displayedRallies.findIndex(r => r.id === currentRally.id) === displayedRallies.length - 1}
                    className="rounded-lg bg-white/[0.08] px-3 py-1.5 text-sm text-slate-300 hover:bg-white/[0.14] disabled:opacity-30 disabled:cursor-not-allowed"
                    title={language === 'de' ? 'Nächste Rally [Strg+→]' : 'Next rally [Ctrl+Right]'}
                  >
                    {language === 'de' ? 'Weiter' : 'Next'} ⏭
                  </button>
                </div>
                <h3 className="text-lg font-semibold">
                  Rally {getRallyNumber(currentRally.id)} ({formatTime(currentRally.duration)})
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateRallyStatus(currentRally.id, currentRally.validation_status === "rejected" ? "accepted" : "rejected")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                      currentRally.validation_status === "rejected" 
                        ? "bg-red-500/20 text-red-300 hover:bg-red-500/30" 
                        : "bg-emerald-500 text-black hover:bg-emerald-400"
                    }`}
                    title={language === 'de' ? 'Status ändern: Sicher ↔ Entfernt [R]' : 'Toggle status: Confirm ↔ Reject [R]'}
                  >
                    {currentRally.validation_status === "rejected" 
                      ? (language === 'de' ? '❌ Entfernt' : '❌ Reject') 
                      : (language === 'de' ? '✅ Sicher' : '✅ Confirm')}
                  </button>
                  <button
                    onClick={() => toggleHighlight(currentRally.id, isMarked(currentRally))}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                      isMarked(currentRally)
                        ? "bg-yellow-500 text-black hover:bg-yellow-400"
                        : "bg-white/[0.08] text-slate-300 hover:bg-white/[0.14]"
                    }`}
                    title={language === 'de' ? 'Highlight umschalten [H]' : 'Toggle highlight [H]'}
                  >
                    {isMarked(currentRally) ? t(language, 'rally.highlight.remove') : t(language, 'rally.highlight.mark')}
                  </button>
                </div>
              </div>
              {/* aspect-video reserves the player's space so switching
                  rallies (new clip src) never collapses the layout and
                  shifts the page scroll position. */}
              <video
                ref={videoRef}
                src={`${API_BASE}/api/clips/${currentRally.clip_filename}`}
                controls
                autoPlay
                loop={loopEnabled}
                className="aspect-video w-full max-h-96 rounded object-contain"
                onPlay={() => {
                  onClipPlayStart?.();
                  setIsPlaying(true);
                }}
                onPause={() => {
                  onClipPlayEnd?.();
                  setIsPlaying(false);
                }}
                onEnded={() => {
                  onClipPlayEnd?.();
                  setIsPlaying(false);
                  if (autoPlayQueue && !loopEnabled) {
                    const currentIndex = displayedRallies.findIndex(r => r.id === currentRally.id);
                    const nextRally = displayedRallies[currentIndex + 1];
                    if (nextRally) handleRallyClick(nextRally, true);
                  }
                }}
                onLoadedMetadata={(e) => {
                  const video = e.currentTarget;
                  video.playbackRate = playbackRate;
                }}
              />
              <div className="mt-3 flex items-center gap-2 flex-wrap">
                <button 
                  onClick={() => {
                    if (!videoRef.current) return;
                    if (videoRef.current.paused) {
                      videoRef.current.play();
                    } else {
                      videoRef.current.pause();
                    }
                  }} 
                  className="rounded bg-white/[0.08] px-3 py-1.5 text-xs text-slate-300 hover:bg-white/[0.14]"
                  title={language === 'de' ? 'Wiedergabe starten/pausieren [Leertaste]' : 'Play/Pause video [Space]'}
                >
                  {isPlaying ? "⏸ Pause" : "▶ Play"}
                </button>
                <div className="flex items-center gap-1">
                  {[0.25, 0.5, 1.0, 1.5].map((speed) => (
                    <button
                      key={speed}
                      onClick={() => {
                        setPlaybackRate(speed);
                        if (videoRef.current) videoRef.current.playbackRate = speed;
                      }}
                      className={`rounded px-2.5 py-1.5 text-sm font-medium transition-all ${
                        playbackRate === speed 
                          ? "bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/30 scale-110" 
                          : "bg-white/[0.08] text-slate-400 hover:bg-white/[0.14] hover:text-white"
                      }`}
                      title={`${speed}x ${language === 'de' ? 'Geschwindigkeit' : 'speed'} [${speed === 0.25 ? '1' : speed === 0.5 ? '2' : speed === 1.0 ? '3' : '4'}]`}
                    >
                      {speed === 1.0 ? "1x" : `${speed}x`}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => setLoopEnabled(prev => !prev)}
                  className={`ml-auto rounded px-3 py-1.5 text-xs font-medium transition ${
                    loopEnabled 
                      ? "bg-purple-500 text-black" 
                      : "bg-white/[0.08] text-slate-400 hover:bg-white/[0.14]"
                  }`}
                  title={language === 'de' ? 'Endlosschleife ein/aus [L]' : 'Loop on/off [L]'}
                >
                  🔁 {language === 'de' ? (loopEnabled ? 'Loop AN' : 'Loop AUS') : (loopEnabled ? 'Loop ON' : 'Loop OFF')}
                </button>
              </div>
              
              <div className="mt-4">
                <label className="text-sm text-slate-400 block mb-2">
                  📝 {t(language, 'match.detail.notes')} <span className="text-xs text-slate-500 ml-1">[N]</span>
                </label>
                <textarea
                  ref={notesRef}
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
                  onClick={downloadAllClips}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium transition bg-blue-600 text-white hover:bg-blue-700"
                  title={language === 'de' ? 'Alle Clips herunterladen' : 'Download all clips'}
                >
                  ⬇️ {language === 'de' ? 'Alle Clips' : 'All Clips'}
                </button>
                <button
                  onClick={downloadHighlights}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium transition bg-yellow-600 text-white hover:bg-yellow-700"
                  title={language === 'de' ? 'Nur Highlights herunterladen' : 'Download only highlights'}
                >
                  ⭐ {language === 'de' ? 'Highlights' : 'Highlights'}
                </button>
                <button
                  onClick={reevaluateHighlights}
                  disabled={reevaluating || match.status !== "completed"}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium transition bg-white/[0.08] text-slate-300 hover:bg-white/[0.14] disabled:opacity-40 disabled:cursor-not-allowed"
                  title={language === 'de'
                    ? 'Automatische Highlights anhand der aktuellen Erkennungsregeln neu bewerten (ohne neue Video-Analyse). Manuelle Markierungen bleiben erhalten.'
                    : 'Re-classify automatic highlights with the current detection rules (no video re-analysis). Manual markings are kept.'}
                >
                  {reevaluating ? (language === 'de' ? '⏳ Bewerte...' : '⏳ Evaluating...') : (language === 'de' ? '🔄 Neu bewerten' : '🔄 Re-evaluate')}
                </button>
                <button
                  onClick={() => { setAutoPlayQueue(!autoPlayQueue); if (!autoPlayQueue && currentRally) videoRef.current?.play(); }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${autoPlayQueue ? "bg-emerald-500 text-black" : "bg-white/[0.08] text-slate-300 hover:bg-white/[0.14]"}`}
                >
                  {autoPlayQueue ? t(language, 'rally.auto_play.on') : t(language, 'rally.auto_play.off')}
                </button>
              </div>
            </div>
            
            <div className="max-h-96 overflow-y-auto">
              {displayedRallies.map((rally) => (
                <div
                  key={rally.id}
                  onClick={() => handleRallyClick(rally)}
                  className={`p-3 border-l-4 cursor-pointer transition-colors
                    ${currentRally?.id === rally.id 
                      ? "bg-blue-900/40 border-blue-400" 
                      : "border-transparent hover:bg-gray-700"}
                    ${isMarked(rally) && currentRally?.id !== rally.id ? "bg-yellow-900/10" : ""}
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <span className="font-mono text-sm text-gray-400 w-16 shrink-0">
                        {formatTime(rally.start_time)}
                      </span>
                      <span className="font-semibold text-white min-w-[80px] text-center">
                        Rally {getRallyNumber(rally.id)}
                      </span>
                      <span className="text-sm text-gray-500 min-w-[60px] text-center">
                        {formatTime(rally.duration)}
                      </span>
                      <div className="flex items-center gap-1.5">
                        {isMarked(rally) && (
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
                        <button 
                          className={`text-sm font-medium transition-all ${
                            currentRally?.id === rally.id 
                              ? "text-blue-300 scale-110" 
                              : "text-blue-400"
                          }`}
                        >
                          {t(language, 'rally.play')}
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
