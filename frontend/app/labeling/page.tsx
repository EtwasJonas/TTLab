"use client";

import { useCallback, useEffect, useState } from "react";
import { useLanguage } from "../../lib/LanguageContext";
import { t } from "../../lib/translations";
import { apiUrl } from "../../lib/api";
import FrameLabeler from "../../components/FrameLabeler";
import type { DatasetStats, FrameAnnotation, Match } from "../../lib/types";

/**
 * Labeling tool (V0.6): builds the ball-tracking dataset.
 *
 * Flow: 1) pick or create a dataset, 2) pick a video, 3) label frames
 * with the FrameLabeler workbench. The dataset overview shows the export
 * button which builds the YOLO train/val split for model training.
 */
export default function LabelingPage() {
  const { language } = useLanguage();
  const [datasets, setDatasets] = useState<DatasetStats[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [annotations, setAnnotations] = useState<FrameAnnotation[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDatasets = useCallback(async () => {
    try {
      const response = await fetch(apiUrl("/api/labeling/datasets"));
      if (response.ok) setDatasets(await response.json());
    } catch {
      setError("Datensätze konnten nicht geladen werden");
    }
  }, []);

  const fetchAnnotations = useCallback(async (dataset: string) => {
    try {
      const response = await fetch(
        apiUrl(`/api/labeling/datasets/${dataset}/annotations`)
      );
      if (response.ok) setAnnotations(await response.json());
    } catch {
      setError("Annotationen konnten nicht geladen werden");
    }
  }, []);

  useEffect(() => {
    fetchDatasets();
    (async () => {
      try {
        const response = await fetch(apiUrl("/api/matches"));
        if (response.ok) setMatches(await response.json());
      } catch {
        setError("Matches konnten nicht geladen werden");
      }
    })();
  }, [fetchDatasets]);

  useEffect(() => {
    if (selectedDataset) void fetchAnnotations(selectedDataset);
  }, [selectedDataset, fetchAnnotations]);

  const applyStats = useCallback((stats: DatasetStats) => {
    setDatasets((current) =>
      current.map((d) => (d.name === stats.name ? stats : d))
    );
  }, []);

  const refreshAnnotations = useCallback(
    (_stats: DatasetStats) => {
      if (selectedDataset) void fetchAnnotations(selectedDataset);
    },
    [selectedDataset, fetchAnnotations]
  );

  const createDataset = async () => {
    const name = newName.trim().toLowerCase();
    if (!name || creating) return;
    setCreating(true);
    setError(null);
    try {
      const response = await fetch(apiUrl("/api/labeling/datasets"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail ?? `HTTP ${response.status}`);
      }
      setNewName("");
      await fetchDatasets();
      setSelectedDataset(name);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Datensatz konnte nicht erstellt werden");
    } finally {
      setCreating(false);
    }
  };

  const exportDataset = async () => {
    if (!selectedDataset || exporting) return;
    setExporting(true);
    setError(null);
    setExportResult(null);
    try {
      const response = await fetch(
        apiUrl(`/api/labeling/datasets/${selectedDataset}/export`),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ val_ratio: 0.2, seed: 42 }),
        }
      );
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail ?? `HTTP ${response.status}`);
      }
      const result = await response.json();
      setExportResult(
        t(language, "labeling.export.result", {
          train: result.train_frames,
          val: result.val_frames,
        })
      );
      await fetchDatasets();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export fehlgeschlagen");
    } finally {
      setExporting(false);
    }
  };

  const datasetStats = datasets.find((d) => d.name === selectedDataset) ?? null;

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-pink-400/20 bg-pink-500/[0.06] p-5">
        <p className="text-xs uppercase tracking-widest text-pink-300">V0.6 Ball-Tracking</p>
        <h1 className="mt-1 text-2xl font-bold">{t(language, "labeling.title")}</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-400">
          {t(language, "labeling.description")}
        </p>
      </section>

      {error && (
        <p className="rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {selectedMatch && selectedDataset ? (
        <FrameLabeler
          dataset={selectedDataset}
          match={selectedMatch}
          annotations={annotations}
          onAnnotationSaved={(stats) => {
            applyStats(stats);
            refreshAnnotations(stats);
          }}
          onAnnotationDeleted={(stats) => {
            applyStats(stats);
            refreshAnnotations(stats);
          }}
          onBack={() => setSelectedMatch(null)}
        />
      ) : selectedDataset ? (
        <section className="space-y-4">
          <button
            onClick={() => setSelectedDataset(null)}
            className="text-blue-400 hover:text-blue-300"
          >
            ← {t(language, "common.back")}
          </button>

          {/* Dataset overview */}
          {datasetStats && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold">
                    <span className="font-mono">{datasetStats.name}</span>
                  </h2>
                  <p className="mt-1 text-sm text-slate-400">
                    {datasetStats.total_frames}{" "}
                    {t(language, "labeling.dataset.frames")} ·{" "}
                    {datasetStats.frames_with_ball}{" "}
                    {t(language, "labeling.dataset.with_ball")} ·{" "}
                    {datasetStats.frames_without_ball}{" "}
                    {t(language, "labeling.dataset.without_ball")}
                  </p>
                </div>
                <button
                  onClick={() => void exportDataset()}
                  disabled={exporting || datasetStats.total_frames < 2}
                  className="rounded-lg bg-emerald-500/20 px-4 py-2 text-sm font-medium text-emerald-300 hover:bg-emerald-500/30 disabled:opacity-50"
                >
                  {exporting ? "..." : t(language, "labeling.export.button")}
                </button>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {t(language, "labeling.export.hint")}
              </p>
              {datasetStats.total_frames < 2 && (
                <p className="mt-1 text-xs text-amber-400">
                  {t(language, "labeling.export.need_more")}
                </p>
              )}
              {exportResult && (
                <p className="mt-2 text-sm text-emerald-300">{exportResult}</p>
              )}
            </div>
          )}

          {/* Video selection */}
          <div>
            <h3 className="text-lg font-semibold">
              {t(language, "labeling.match.select")}
            </h3>
            <p className="text-sm text-slate-400">
              {t(language, "labeling.match.select_hint")}
            </p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {matches.map((match) => {
                const labeled = annotations.filter((a) => a.match_id === match.id).length;
                return (
                  <button
                    key={match.id}
                    onClick={() => setSelectedMatch(match)}
                    className="rounded-xl border border-white/10 bg-white/[0.06] p-4 text-left transition hover:border-blue-400/40 hover:bg-white/[0.1]"
                  >
                    <p className="truncate font-medium">
                      {match.custom_title || match.original_filename}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      #{match.id} · {match.status} ·{" "}
                      {labeled > 0
                        ? t(language, "labeling.workbench.labeled_progress", {
                            labeled,
                            total: "?",
                            withBall: annotations.filter(
                              (a) => a.match_id === match.id && a.has_ball
                            ).length,
                          })
                        : t(language, "labeling.workbench.not_labeled")}
                    </p>
                  </button>
                );
              })}
              {matches.length === 0 && (
                <p className="text-sm text-slate-500">
                  {t(language, "rally.no_rallies_detected")}
                </p>
              )}
            </div>
          </div>
        </section>
      ) : (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold">
            {t(language, "labeling.dataset.select")}
          </h2>

          {datasets.length === 0 && (
            <p className="text-sm text-slate-500">
              {t(language, "labeling.dataset.empty")}
            </p>
          )}

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {datasets.map((dataset) => (
              <button
                key={dataset.name}
                onClick={() => setSelectedDataset(dataset.name)}
                className="rounded-xl border border-white/10 bg-white/[0.06] p-4 text-left transition hover:border-pink-400/40 hover:bg-white/[0.1]"
              >
                <p className="font-mono font-medium">{dataset.name}</p>
                <p className="mt-1 text-sm text-slate-400">
                  {dataset.total_frames} {t(language, "labeling.dataset.frames")}
                </p>
                <p className="text-xs text-slate-500">
                  {dataset.frames_with_ball} {t(language, "labeling.dataset.with_ball")} ·{" "}
                  {dataset.frames_without_ball} {t(language, "labeling.dataset.without_ball")}
                  {dataset.exported && (
                    <span className="ml-2 text-emerald-400">
                      {t(language, "labeling.dataset.exported")}
                    </span>
                  )}
                </p>
              </button>
            ))}
          </div>

          {/* Create new dataset */}
          <div className="rounded-xl border border-white/10 bg-white/[0.06] p-4">
            <p className="text-sm font-medium text-slate-300">
              {t(language, "labeling.dataset.new_name")}
            </p>
            <div className="mt-2 flex gap-2">
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void createDataset()}
                placeholder={t(language, "labeling.dataset.name_placeholder")}
                className="w-64 rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-sm outline-none focus:border-blue-400/60"
              />
              <button
                onClick={() => void createDataset()}
                disabled={creating || !newName.trim()}
                className="rounded-lg bg-blue-500/20 px-4 py-2 text-sm font-medium text-blue-300 hover:bg-blue-500/30 disabled:opacity-50"
              >
                {t(language, "labeling.dataset.create")}
              </button>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
