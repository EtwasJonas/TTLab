"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLanguage } from "../lib/LanguageContext";
import { t } from "../lib/translations";
import { apiUrl } from "../lib/api";
import type {
  DatasetStats,
  FrameAnnotation,
  Match,
  NormalizedBox,
  VideoInfo,
} from "../lib/types";

interface FrameLabelerProps {
  dataset: string;
  match: Match;
  annotations: FrameAnnotation[];
  onAnnotationSaved: (stats: DatasetStats) => void;
  onAnnotationDeleted: (stats: DatasetStats) => void;
  onBack: () => void;
}

/** Minimum drag size (normalized) so a stray click doesn't create a box. */
const MIN_BOX_SIZE = 0.004;

/**
 * Auto-save delay after drawing a box (ms). The delay lets the user chain
 * several boxes (multiple balls on the floor) - each new drag cancels the
 * pending save, so saving only happens once the last box is finished.
 */
const AUTO_SAVE_DELAY_MS = 900;

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const rest = (seconds % 60).toFixed(1).padStart(4, "0");
  return `${minutes}:${rest}`;
}

function boxToYolo(box: NormalizedBox): number[] {
  return [
    Number((box.x + box.w / 2).toFixed(6)),
    Number((box.y + box.h / 2).toFixed(6)),
    Number(box.w.toFixed(6)),
    Number(box.h.toFixed(6)),
  ];
}

function yoloToBox(bbox: number[]): NormalizedBox {
  const [cx, cy, w, h] = bbox;
  return { x: cx - w / 2, y: cy - h / 2, w, h };
}

/**
 * Frame-by-frame labeling workbench for one video (V0.6 ball dataset).
 *
 * The backend extracts frames as JPEG (the browser cannot decode HEVC
 * Main 10 videos itself). Boxes are drawn on the downscaled preview but
 * stored as normalized YOLO coordinates, so the saved training image can
 * be full resolution without any coordinate conversion.
 *
 * Multi-box support: a frame can contain several balls (e.g. balls lying
 * on the floor). Each finished drag adds another box; every box has a
 * remove button. Auto-save fires shortly after the LAST drawn box.
 */
export default function FrameLabeler({
  dataset,
  match,
  annotations,
  onAnnotationSaved,
  onAnnotationDeleted,
  onBack,
}: FrameLabelerProps) {
  const { language } = useLanguage();
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [imgLoaded, setImgLoaded] = useState(false);
  const [boxes, setBoxes] = useState<NormalizedBox[]>([]);
  const [drag, setDrag] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);
  const [autoSave, setAutoSave] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const autoSaveTimer = useRef<number | null>(null);
  const [autoSavePending, setAutoSavePending] = useState(false);

  // Annotations of the currently open video, for the progress display and
  // to pre-load boxes when navigating to an already labeled frame.
  const matchAnnotations = useMemo(
    () => annotations.filter((a) => a.match_id === match.id),
    [annotations, match.id]
  );
  const annotationByFrame = useMemo(() => {
    const map = new Map<number, FrameAnnotation>();
    for (const a of matchAnnotations) map.set(a.frame_index, a);
    return map;
  }, [matchAnnotations]);
  const currentAnnotation = annotationByFrame.get(frameIndex) ?? null;

  const frameCount = videoInfo?.frame_count ?? 0;
  const fps = videoInfo?.fps ?? 30;
  // v=2 busts the browser cache after the server-side rotation fix
  // (iPhone MOVs are recorded with a 180° display-matrix rotation that
  // OpenCV ignores - frames were served upside down before the fix).
  const frameUrl = apiUrl(`/api/matches/${match.id}/frame?frame=${frameIndex}&v=2`);
  const nextFrameUrl =
    frameIndex + 1 < frameCount
      ? apiUrl(`/api/matches/${match.id}/frame?frame=${frameIndex + 1}&v=2`)
      : null;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(apiUrl(`/api/matches/${match.id}/video-info`));
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const info: VideoInfo = await response.json();
        if (!cancelled) {
          setVideoInfo(info);
          if (info.frame_count <= 0) setError("Video hat keine lesbaren Frames");
        }
      } catch {
        if (!cancelled) setError("Video-Metadaten konnten nicht geladen werden");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [match.id]);

  const clearAutoSaveTimer = useCallback(() => {
    if (autoSaveTimer.current !== null) {
      window.clearTimeout(autoSaveTimer.current);
      autoSaveTimer.current = null;
    }
    setAutoSavePending(false);
  }, []);

  // When the frame changes, show the existing annotation (if any) and
  // reset the drawing state. A pending auto-save is obsolete on a new frame.
  useEffect(() => {
    setImgLoaded(false);
    clearAutoSaveTimer();
    setBoxes(currentAnnotation?.bboxes ? currentAnnotation.bboxes.map(yoloToBox) : []);
    setDrag(null);
  }, [frameIndex, currentAnnotation, clearAutoSaveTimer]);

  // Never fire a delayed save after unmounting.
  useEffect(() => clearAutoSaveTimer, [clearAutoSaveTimer]);

  const goToFrame = useCallback(
    (index: number) => {
      if (frameCount <= 0) return;
      setFrameIndex(Math.max(0, Math.min(frameCount - 1, index)));
    },
    [frameCount]
  );

  const saveAnnotation = useCallback(
    async (boxesToSave: NormalizedBox[]) => {
      if (saving || !videoInfo) return;
      setSaving(true);
      setError(null);
      try {
        const response = await fetch(
          apiUrl(`/api/labeling/datasets/${dataset}/annotations`),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              match_id: match.id,
              frame_index: frameIndex,
              bboxes: boxesToSave.map(boxToYolo),
            }),
          }
        );
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail ?? `HTTP ${response.status}`);
        }
        const stats: DatasetStats = await response.json();
        onAnnotationSaved(stats);
        setSavedFlash(true);
        window.setTimeout(() => setSavedFlash(false), 600);
        goToFrame(frameIndex + 1);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
      } finally {
        setSaving(false);
      }
    },
    [dataset, frameIndex, goToFrame, match.id, onAnnotationSaved, saving, videoInfo]
  );

  const deleteCurrentAnnotation = useCallback(async () => {
    if (!currentAnnotation || saving) return;
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(
        apiUrl(`/api/labeling/datasets/${dataset}/annotations/${match.id}/${frameIndex}`),
        { method: "DELETE" }
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const stats: DatasetStats = await response.json();
      onAnnotationDeleted(stats);
      setBoxes([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Löschen fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }, [currentAnnotation, dataset, frameIndex, match.id, onAnnotationDeleted, saving]);

  // --- Bounding box drawing (mouse) ---

  const normalizedPoint = (event: React.MouseEvent) => {
    const rect = overlayRef.current?.getBoundingClientRect();
    if (!rect) return null;
    return {
      x: Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width)),
      y: Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height)),
    };
  };

  const handleMouseDown = (event: React.MouseEvent) => {
    if (event.button !== 0) return;
    const point = normalizedPoint(event);
    if (!point) return;
    // A new drag cancels a pending auto-save - the user is drawing another
    // ball, so saving must wait until the last box is finished.
    clearAutoSaveTimer();
    setDrag({ x0: point.x, y0: point.y, x1: point.x, y1: point.y });
  };

  const handleMouseMove = (event: React.MouseEvent) => {
    if (!drag) return;
    const point = normalizedPoint(event);
    if (!point) return;
    setDrag({ ...drag, x1: point.x, y1: point.y });
  };

  const handleMouseUp = () => {
    if (!drag) return;
    const x = Math.min(drag.x0, drag.x1);
    const y = Math.min(drag.y0, drag.y1);
    const w = Math.abs(drag.x1 - drag.x0);
    const h = Math.abs(drag.y1 - drag.y0);
    setDrag(null);
    if (w < MIN_BOX_SIZE || h < MIN_BOX_SIZE) {
      // Too small to be a ball box - treat as a click that does nothing
      // (boxes are removed via their × button instead).
      return;
    }
    const newBox = { x, y, w, h };
    const nextBoxes = [...boxes, newBox];
    setBoxes(nextBoxes);
    if (autoSave) {
      setAutoSavePending(true);
      autoSaveTimer.current = window.setTimeout(() => {
        autoSaveTimer.current = null;
        setAutoSavePending(false);
        void saveAnnotation(nextBoxes);
      }, AUTO_SAVE_DELAY_MS);
    }
  };

  const removeBox = (index: number) => {
    clearAutoSaveTimer();
    setBoxes((current) => current.filter((_, i) => i !== index));
  };

  // --- Keyboard shortcuts ---

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          (event.key === "Enter" && target.tagName === "BUTTON"))
      ) {
        return;
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goToFrame(event.shiftKey ? frameIndex - Math.round(fps) : frameIndex - 1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        goToFrame(event.shiftKey ? frameIndex + Math.round(fps) : frameIndex + 1);
      } else if (event.key === "Enter") {
        event.preventDefault();
        if (boxes.length > 0) {
          clearAutoSaveTimer();
          void saveAnnotation(boxes);
        }
      } else if (event.key.toLowerCase() === "n") {
        event.preventDefault();
        clearAutoSaveTimer();
        void saveAnnotation([]);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [boxes, clearAutoSaveTimer, fps, frameIndex, goToFrame, saveAnnotation]);

  const dragPreview = drag
    ? {
        left: `${Math.min(drag.x0, drag.x1) * 100}%`,
        top: `${Math.min(drag.y0, drag.y1) * 100}%`,
        width: `${Math.abs(drag.x1 - drag.x0) * 100}%`,
        height: `${Math.abs(drag.y1 - drag.y0) * 100}%`,
      }
    : null;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <button onClick={onBack} className="text-blue-400 hover:text-blue-300">
            ← {t(language, "common.back")}
          </button>
          <h2 className="mt-1 text-lg font-semibold">
            {t(language, "labeling.title")} – {match.custom_title || match.original_filename}
          </h2>
          <p className="text-sm text-slate-400">
            {t(language, "labeling.common.new_dataset")}: <span className="font-mono text-slate-300">{dataset}</span>
          </p>
        </div>
        <div className="text-right text-sm">
          <p className="text-slate-400">
            {t(language, "labeling.workbench.labeled_progress", {
              labeled: matchAnnotations.length,
              total: frameCount || "?",
              withBall: matchAnnotations.filter((a) => a.has_ball).length,
            })}
          </p>
        </div>
      </div>

      {error && (
        <p className="rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {/* Frame display with drawing overlay. The <img> defines the element
          size (w-full h-auto), so the overlay rect always matches the
          picture area exactly - normalized coords need no correction. */}
      <div className="relative overflow-hidden rounded-xl border border-white/10 bg-black">
        {!imgLoaded && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60 text-sm text-slate-300">
            {t(language, "labeling.workbench.loading")}
          </div>
        )}
        {/* key forces a fresh <img> per frame; the browser cache (enabled by
            the backend Cache-Control header) makes revisits instant. */}
        <img
          key={frameIndex}
          src={frameUrl}
          alt={`Frame ${frameIndex}`}
          className="block w-full select-none"
          draggable={false}
          onLoad={() => setImgLoaded(true)}
        />
        <div
          ref={overlayRef}
          className="absolute inset-0 cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {boxes.map((box, index) => (
            <div
              key={index}
              className="absolute border-2 border-pink-400 bg-pink-400/20"
              style={{
                left: `${box.x * 100}%`,
                top: `${box.y * 100}%`,
                width: `${box.w * 100}%`,
                height: `${box.h * 100}%`,
              }}
            >
              <button
                onClick={() => removeBox(index)}
                title={t(language, "labeling.workbench.remove_box")}
                className="absolute -right-2.5 -top-2.5 flex h-5 w-5 items-center justify-center rounded-full border border-pink-400 bg-[#0a0e17] text-xs font-bold leading-none text-pink-300 hover:bg-pink-500 hover:text-white"
              >
                ×
              </button>
            </div>
          ))}
          {dragPreview && (
            <div
              className="absolute border-2 border-dashed border-pink-300 bg-pink-300/10"
              style={dragPreview}
            />
          )}
          {autoSavePending && (
            <div className="absolute bottom-2 left-2 rounded-full border border-pink-400/40 bg-[#0a0e17]/90 px-3 py-1 text-xs text-pink-300">
              {t(language, "labeling.workbench.auto_save_pending")}
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => goToFrame(frameIndex - Math.round(fps))}
          className="rounded-lg bg-white/[0.06] px-3 py-1.5 text-sm text-slate-300 hover:bg-white/[0.12]"
        >
          {t(language, "labeling.workbench.prev_second")}
        </button>
        <button
          onClick={() => goToFrame(frameIndex - 1)}
          className="rounded-lg bg-white/[0.06] px-3 py-1.5 text-sm text-slate-300 hover:bg-white/[0.12]"
        >
          {t(language, "labeling.workbench.prev_frame")}
        </button>
        <span className="rounded-lg bg-white/[0.06] px-3 py-1.5 font-mono text-sm text-slate-200">
          {t(language, "labeling.workbench.frame")} {frameIndex + 1}/{frameCount || "?"}
          {" · "}
          {formatTime(frameIndex / fps)}
        </span>
        <button
          onClick={() => goToFrame(frameIndex + 1)}
          className="rounded-lg bg-white/[0.06] px-3 py-1.5 text-sm text-slate-300 hover:bg-white/[0.12]"
        >
          {t(language, "labeling.workbench.next_frame")}
        </button>
        <button
          onClick={() => goToFrame(frameIndex + Math.round(fps))}
          className="rounded-lg bg-white/[0.06] px-3 py-1.5 text-sm text-slate-300 hover:bg-white/[0.12]"
        >
          {t(language, "labeling.workbench.next_second")}
        </button>

        <span
          className={`rounded-full px-3 py-1 text-xs ${
            currentAnnotation
              ? "border border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
              : "border border-white/10 bg-white/[0.06] text-slate-400"
          }`}
        >
          {currentAnnotation
            ? t(language, "labeling.workbench.labeled")
            : t(language, "labeling.workbench.not_labeled")}
        </span>

        {savedFlash && (
          <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">
            {t(language, "labeling.workbench.saved")}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => void saveAnnotation([])}
          disabled={saving || !videoInfo}
          className="rounded-lg bg-amber-500/20 px-4 py-2 text-sm font-medium text-amber-300 hover:bg-amber-500/30 disabled:opacity-50"
        >
          {t(language, "labeling.workbench.no_ball")}
        </button>
        <button
          onClick={() => {
            clearAutoSaveTimer();
            void saveAnnotation(boxes);
          }}
          disabled={saving || boxes.length === 0}
          className="rounded-lg bg-pink-500/20 px-4 py-2 text-sm font-medium text-pink-300 hover:bg-pink-500/30 disabled:opacity-50"
        >
          {saving
            ? t(language, "labeling.workbench.saving")
            : t(language, "labeling.workbench.save_next")}
        </button>
        {boxes.length > 1 && (
          <button
            onClick={() => {
              clearAutoSaveTimer();
              setBoxes([]);
            }}
            className="rounded-lg bg-white/[0.06] px-4 py-2 text-sm text-slate-400 hover:bg-white/[0.12]"
          >
            {t(language, "labeling.workbench.clear_boxes", { count: boxes.length })}
          </button>
        )}
        {currentAnnotation && (
          <button
            onClick={() => void deleteCurrentAnnotation()}
            disabled={saving}
            className="rounded-lg bg-white/[0.06] px-4 py-2 text-sm text-slate-400 hover:bg-white/[0.12] disabled:opacity-50"
          >
            {t(language, "labeling.workbench.delete_annotation")}
          </button>
        )}
        <label className="ml-auto flex cursor-pointer items-center gap-2 text-sm text-slate-400">
          <input
            type="checkbox"
            checked={autoSave}
            onChange={(e) => setAutoSave(e.target.checked)}
            className="h-4 w-4 accent-blue-500"
          />
          {t(language, "labeling.workbench.auto_save")}
        </label>
      </div>

      <div className="space-y-1">
        <p className="text-sm text-slate-500">
          {t(language, "labeling.workbench.draw_hint")}
        </p>
        <p className="text-sm text-slate-600">
          {t(language, "labeling.workbench.multi_hint")}
        </p>
      </div>

      {/* Prefetch the next frame so stepping forward feels instant. */}
      {nextFrameUrl && (
        <img src={nextFrameUrl} alt="" className="hidden" aria-hidden />
      )}
    </section>
  );
}
